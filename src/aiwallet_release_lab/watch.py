"""Persistent, local-only video render watch queue.

Only stable, regular files within the selected directory can be inspected.
No uploads, telemetry, code execution from files, cloud credentials or billing.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
import tempfile
import time
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .core import ALLOWED_EXTENSIONS, AuditError, MAX_FILE_BYTES, audit_video
from .policy import validate_policy
from .report import save_report
from .workflow import _safe_csv_cell, _slug, gate_report

SCHEMA = "aiwallet.release-watch/v1"
MAX_WATCHED = 200


def _atomic_write(path: Path, content: str) -> None:
    """Replace the entire output in one move; never expose partial manifests."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent,
                                         prefix=".aiwallet-", suffix=".tmp", delete=False) as fp:
            tmp = Path(fp.name)
            try:
                os.chmod(tmp, 0o600)
            except OSError:
                pass
            fp.write(content)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def _signature(p: Path) -> tuple[int, int, int]:
    """Size and two timestamps: fast change signal; audit SHA-256 is the identity."""
    stat = p.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _valid_stored_record(name: str, row: Any) -> bool:
    """Do not trust a prior state.json after manual edits or disk corruption."""
    if not isinstance(name, str) or not name or len(name) > 512 or not isinstance(row, dict):
        return False
    signature = row.get("signature")
    if not isinstance(signature, list) or len(signature) != 3 or any(
        isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in signature
    ):
        return False
    if row.get("gate_passed") is not True and row.get("gate_passed") is not False:
        return False
    if row.get("status") not in ("pass", "warn", "fail", "error"):
        return False
    if row.get("error") is not None and not isinstance(row.get("error"), str):
        return False
    for label in ("report_json", "report_html"):
        ref = row.get(label)
        if ref is None:
            continue
        if not isinstance(ref, str) or len(ref) > 300:
            return False
        p = Path(ref)
        if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] != "reports":
            return False
    return True


def _config_id(*, policy: dict[str, Any] | None, quick: bool, fail_on: str) -> str:
    content = json.dumps({"policy": policy, "quick": quick, "fail_on": fail_on},
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class WatchSession:
    def __init__(self, folder: str | Path, destination: str | Path, *, recursive: bool = False,
                 quick: bool = False, fail_on: str = "warn", policy: dict[str, Any] | None = None,
                 stable_seconds: float = 3, max_files: int = 40):
        raw = Path(folder)
        if raw.is_symlink() or not raw.is_dir():
            raise AuditError("Folder sumber harus direktori lokal biasa, bukan symlink.")
        if fail_on not in ("warn", "fail", "none"):
            raise AuditError("Pilihan fail-on harus warn, fail, atau none.")
        if isinstance(max_files, bool) or not 1 <= max_files <= MAX_WATCHED:
            raise AuditError(f"max-files harus 1–{MAX_WATCHED}.")
        if not isinstance(stable_seconds, (int, float)) or isinstance(stable_seconds, bool) or not math.isfinite(stable_seconds) or not 0 <= stable_seconds <= 600:
            raise AuditError("stable-seconds harus 0–600 detik.")
        self.source = raw.resolve(strict=True)
        out = Path(destination)
        if out.is_symlink():
            raise AuditError("Direktori output tidak boleh symlink.")
        self.out = out.resolve()
        # Reject output inside input: the watcher must never read its own artifacts.
        if self.out == self.source or self.out.is_relative_to(self.source):
            raise AuditError("Direktori output harus berada di luar folder video yang dipantau.")
        self.out.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.recursive = recursive
        self.quick = quick
        self.fail_on = fail_on
        self.policy = validate_policy(policy) if policy is not None else None
        self.config_id = _config_id(policy=self.policy, quick=quick, fail_on=fail_on)
        self.stable_seconds = float(stable_seconds)
        self.max_files = max_files
        self.seen: dict[str, tuple[tuple[int, int, int], float]] = {}
        self.records: dict[str, dict[str, Any]] = {}
        self.last_summary: dict[str, int] | None = None
        self.last_seen_files: set[str] | None = None
        self.last_unstable: int | None = None
        state_path = self.out / "state.json"
        if state_path.is_file():
            if state_path.stat().st_size > 1024 * 1024:
                raise AuditError("Watch state lebih dari 1 MiB; periksa secara manual.")
            try:
                saved = json.loads(state_path.read_text(encoding="utf-8"))
                if not isinstance(saved, dict) or saved.get("schema") != SCHEMA:
                    raise ValueError("unexpected state schema")
                if saved.get("source") != str(self.source):
                    raise ValueError("source folder mismatch")
                prior = saved.get("records", {})
                if not isinstance(prior, dict) or len(prior) > MAX_WATCHED:
                    raise ValueError("unexpected state record format")
                if any(not _valid_stored_record(k, v) for k, v in prior.items()):
                    raise ValueError("invalid prior receipt reference or signature")
                if saved.get("config_id") == self.config_id:
                    self.records = prior
                    self.last_summary = saved.get("summary") if isinstance(saved.get("summary"), dict) else None
            except (ValueError, TypeError, UnicodeError) as exc:
                raise AuditError("Watch state tidak valid. Simpan salinannya sebelum menjalankan lagi.") from exc

    def _files(self) -> list[Path]:
        # Path.rglob() doesn't follow directory symlinks in Python 3.11+, but
        # resolving the candidate below also rejects symlinked parents.
        paths = self.source.rglob("*") if self.recursive else self.source.iterdir()
        found: list[Path] = []
        for p in paths:
            if p.suffix.lower() not in ALLOWED_EXTENSIONS or p.is_symlink() or not p.is_file():
                continue
            try:
                if not p.resolve(strict=True).is_relative_to(self.source):
                    continue
            except (OSError, RuntimeError):
                continue
            found.append(p)
            if len(found) > self.max_files:
                raise AuditError(f"Folder berisi lebih dari {self.max_files} video; pecah folder atau naikkan --max-files.")
        found.sort(key=lambda p: p.relative_to(self.source).as_posix().casefold())
        return found

    def _save(self, *, files: list[Path], unstable: int) -> dict[str, Any]:
        current = {p.relative_to(self.source).as_posix() for p in files}
        self.records = {k: v for k, v in self.records.items() if k in current}
        summary = {"discovered": len(files), "stable_results": len(self.records),
                   "passed": sum(v.get("gate_passed") is True for v in self.records.values()),
                   "blocked": sum(v.get("gate_passed") is False for v in self.records.values()),
                   "pending_or_unstable": max(0, len(files) - len(self.records)),
                   "unstable_now": unstable}
        stamp = datetime.now(timezone.utc).isoformat()
        manifest = {"schema": SCHEMA, "source": str(self.source), "config_id": self.config_id,
                    "updated_at": stamp, "quick": self.quick, "recursive": self.recursive,
                    "policy_name": self.policy.get("name") if self.policy else None,
                    "summary": summary, "records": self.records,
                    "notice": "Technical QC only. No upload, publication, creative approval or platform acceptance."}
        _atomic_write(self.out / "state.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        buffer = ["file,status,gate_passed,sha256,report_html,error"]
        for name, row in sorted(self.records.items()):
            import io
            f = io.StringIO()
            writer = csv.writer(f)
            writer.writerow([_safe_csv_cell(name), row["status"], row["gate_passed"],
                             row.get("sha256") or "", row.get("report_html") or "",
                             _safe_csv_cell(row.get("error") or "")])
            buffer.append(f.getvalue().strip("\r\n"))
        _atomic_write(self.out / "summary.csv", "\n".join(buffer) + "\n")
        rows = "".join(
            "<tr><td>" + html.escape(name) + "</td><td>" + html.escape(row["status"])
            + "</td><td>" + ("PASS" if row["gate_passed"] else "BLOCK") + "</td><td>"
            + (f'<a href="{html.escape(row["report_html"], quote=True)}">Laporan</a>'
               if row.get("report_html") else html.escape(row.get("error") or ""))
            + "</td></tr>" for name, row in sorted(self.records.items()))
        page = f'''<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AIWallet Watch QC</title><style>body{{background:#f4f4ed;color:#12271f;font:16px/1.5 system-ui;max-width:950px;margin:5rem auto;padding:1rem}}table{{border-collapse:collapse;width:100%}}td,th{{padding:12px;border-bottom:1px solid #ccd7c7;text-align:left;overflow-wrap:anywhere}}a{{color:#276442}}@media(max-width:600px){{body{{margin:1rem auto}}td,th{{padding:6px;font-size:12px}}}}</style></head><body><p>AIWALLET / LOCAL WATCH</p><h1>Video release queue</h1><p>{summary["passed"]} passed, {summary["blocked"]} blocked; {summary["pending_or_unstable"]} pending.</p><table><thead><tr><th>File</th><th>QC</th><th>Gate</th><th>Report</th></tr></thead><tbody>{rows}</tbody></table><p>Local technical evidence only. Manual creative sign-off remains necessary.</p></body></html>'''
        _atomic_write(self.out / "index.html", page)
        return manifest

    def poll(self, *, now: float | None = None) -> dict[str, Any]:
        """Exactly one bounded discovery cycle; deterministic and unit-testable."""
        clock = time.monotonic() if now is None else float(now)
        files = self._files()
        current = {p.relative_to(self.source).as_posix() for p in files}
        for key in set(self.seen) - current:
            del self.seen[key]
        completed: list[dict[str, Any]] = []
        unstable = 0
        invalidated = False
        for p in files:
            rel = p.relative_to(self.source).as_posix()
            try:
                signature = _signature(p)
            except OSError:
                unstable += 1
                continue
            # Files not yet settled must not be touched by FFmpeg.
            observed = self.seen.get(rel)
            if observed is None or observed[0] != signature:
                self.seen[rel] = (signature, clock)
                observed = self.seen[rel]
            # An old PASS becomes invalid immediately when its source changes.
            # Do not display its verdict while a new export is still being written.
            old = self.records.get(rel)
            if old is not None and tuple(old.get("signature", ())) != signature:
                self.records.pop(rel, None)
                invalidated = True
            if clock - observed[1] < self.stable_seconds:
                unstable += 1
                continue
            existing = self.records.get(rel)
            if existing and tuple(existing.get("signature", ())) == signature:
                if existing.get("error") or (existing.get("report_json") and
                                            (self.out / existing["report_json"]).is_file()):
                    continue
            unique = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12]
            report_dir = self.out / "reports" / f"{_slug(p.stem)}-{unique}"
            try:
                limits = {field: self.policy[key] for key, field in (
                    ("max_black_segment_seconds", "black_segments"),
                    ("max_freeze_segment_seconds", "freeze_segments"),
                    ("max_silence_segment_seconds", "silence_segments"))
                    if self.policy is not None and key in self.policy}
                audit = audit_video(p, quick=self.quick, scan_limits=limits)
                # Avoid registering a receipt for a half-written file that changed mid-analysis.
                if _signature(p) != signature:
                    self.seen.pop(rel, None)
                    unstable += 1
                    continue
                audit["file"]["name"] = rel
                json_path, html_path = save_report(audit, report_dir)
                gate = gate_report(audit, fail_on=self.fail_on, policy=self.policy)
                row = {"file": rel, "signature": list(signature), "status": audit["summary"]["status"],
                       "gate_passed": gate["passed"], "blocking_check_codes": gate["blocking_check_codes"],
                       "sha256": audit["file"]["sha256"], "report_json": json_path.relative_to(self.out).as_posix(),
                       "report_html": html_path.relative_to(self.out).as_posix(), "error": None,
                       "checked_at": datetime.now(timezone.utc).isoformat()}
            except (AuditError, OSError) as exc:
                row = {"file": rel, "signature": list(signature), "status": "error", "gate_passed": False,
                       "blocking_check_codes": ["watch_scan_error"], "sha256": None,
                       "report_json": None, "report_html": None, "error": str(exc),
                       "checked_at": datetime.now(timezone.utc).isoformat()}
            self.records[rel] = row
            completed.append({"file": rel, "status": row["status"], "gate_passed": row["gate_passed"],
                              "sha256": row["sha256"], "error": row["error"]})
        # No idle busy-writes: an unattended 2-second poll must not fsync three
        # unchanged reports 43,200 times per day. A changed queue is still
        # committed immediately, including invalidation of previous PASS.
        changed = (bool(completed) or invalidated or self.last_summary is None or
                   current != self.last_seen_files or unstable != self.last_unstable)
        if changed:
            manifest = self._save(files=files, unstable=unstable)
            self.last_summary = manifest["summary"]
        self.last_seen_files = current
        self.last_unstable = unstable
        return {"schema": "aiwallet.watch-poll/v1", "new_results": completed, "summary": self.last_summary,
                "output": str(self.out / "index.html")}


@contextmanager
def exclusive_watch_lock(out: Path):
    """OS advisory lock: a second watcher cannot corrupt the same output.

    The lock file can remain on disk safely: it holds no lease or stale PID.
    The operating system releases the byte/flock when the process terminates.
    """
    path = out / ".watch.lock"
    with path.open("a+b") as fp:
        try:
            if os.name == "nt":
                import msvcrt  # Windows-only standard library
                fp.seek(0, os.SEEK_END)
                if fp.tell() == 0:
                    fp.write(b"\x00")
                    fp.flush()
                fp.seek(0)
                msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl  # POSIX-only standard library
                fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise AuditError("Sudah ada proses Watch yang memakai direktori output ini.") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                fp.seek(0)
                msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


def run_watch(session: WatchSession, *, poll_interval: float = 2.0, max_cycles: int | None = None):
    if isinstance(poll_interval, bool) or not isinstance(poll_interval, (int, float)) or not math.isfinite(poll_interval) or not .2 <= poll_interval <= 120:
        raise AuditError("poll-interval harus 0.2–120 detik.")
    if max_cycles is not None and (isinstance(max_cycles, bool) or not 1 <= max_cycles <= 10000):
        raise AuditError("max-cycles harus 1–10000.")
    i = 0
    with exclusive_watch_lock(session.out):
        try:
            while True:
                result = session.poll()
                if i == 0 or result["new_results"]:
                    print(json.dumps(result, ensure_ascii=False), flush=True)
                i += 1
                if max_cycles is not None and i >= max_cycles:
                    break
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print(json.dumps({"status": "stopped_by_user", "output": str(session.out / "index.html")}), flush=True)
