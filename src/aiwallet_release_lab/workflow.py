"""Machine-readable release gate, local batch mode, and export comparison.

Never reads network credentials or uploads source videos. All outputs are local.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

from .core import ALLOWED_EXTENSIONS, AuditError, audit_video, DEFAULT_DETECTOR_SECONDS, sha256, _file, RULESET, MAX_FILE_BYTES
from .report import save_report
from .policy import evaluate_policy, validate_policy


def gate_report(report: dict[str, Any], *, fail_on: str = "warn",
                policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """CI result: strictly a *technical* gate, not social-platform approval."""
    if fail_on not in ("warn", "fail", "none"):
        raise AuditError("fail_on harus warn, fail, atau none.")
    counts = report["summary"]
    reasons = [c["code"] for c in report["checks"]
               if c["level"] == "fail" or (fail_on == "warn" and c["level"] == "warn")]
    if fail_on == "none":
        reasons = []
    failures = evaluate_policy(report, policy) if policy is not None else []
    reasons.extend("policy:" + f["code"] for f in failures)
    return {
        "schema": "aiwallet.release-gate/v1",
        "file": {"name": report["file"]["name"], "sha256": report["file"]["sha256"]},
        "rule_set": report["ruleset"],
        "technical_status": counts["status"],
        "passed": not reasons,
        "fail_on": fail_on,
        "blocking_check_codes": reasons,
        "policy_name": policy.get("name") if policy else None,
        "policy_violations": failures,
        "checks_passed": counts["passed"],
        "checks_warned": counts["warnings"],
        "checks_failed": counts["failed"],
        "disclaimer": "Heuristic technical gate; not editorial sign-off, distribution approval, or proof of rights.",
    }


def _safe_csv_cell(value: str) -> str:
    """Prevent spreadsheet formula execution in user-named paths when CSV is opened."""
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


def _slug(stem: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-_")[:52]
    return name or "video"


def discover_videos(folder: str | Path, *, recursive: bool = False, max_files: int = 40) -> list[Path]:
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise AuditError("Folder video tidak ditemukan, atau bukan direktori biasa.")
    if not 1 <= max_files <= 200:
        raise AuditError("max_files harus 1–200 untuk membatasi beban dan biaya.")
    files = [p for p in (folder.rglob("*") if recursive else folder.iterdir())
             if p.suffix.lower() in ALLOWED_EXTENSIONS and p.is_file() and not p.is_symlink()]
    files.sort(key=lambda p: p.relative_to(folder).as_posix().casefold())
    if not files:
        raise AuditError("Folder tidak berisi video MP4, MOV, M4V, WebM, atau MKV.")
    if len(files) > max_files:
        raise AuditError(f"Ada {len(files)} video. Batas batch {max_files}; pecah menjadi beberapa batch.")
    return files


def audit_batch(folder: str | Path, destination: str | Path, *, quick: bool = False,
                recursive: bool = False, max_files: int = 40, fail_on: str = "warn",
                policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Scan a bounded folder. Errors are retained without hiding successful scans."""
    if fail_on not in ("warn", "fail", "none"):
        raise AuditError("fail_on harus warn, fail, atau none.")
    if policy is not None:
        policy = validate_policy(policy)
    source = Path(folder)
    files = discover_videos(source, recursive=recursive, max_files=max_files)
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"schema": "aiwallet.release-batch/v1", "quick": quick,
                                "recursive": recursive, "fail_on": fail_on, "policy_name": policy.get("name") if policy else None,
                                "items": [],
                                "media_copied": False}
    for p in files:
        relative = p.relative_to(source).as_posix()
        unique = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:12]
        output_dir = out / "reports" / f"{_slug(p.stem)}-{unique}"
        try:
            limits = {field: policy[key] for key, field in (("max_black_segment_seconds", "black_segments"),
                      ("max_freeze_segment_seconds", "freeze_segments"), ("max_silence_segment_seconds", "silence_segments"))
                      if policy is not None and key in policy}
            report = audit_video(p, quick=quick, scan_limits=limits)
            report["file"]["name"] = relative
            json_path, html_path = save_report(report, output_dir)
            gate = gate_report(report, fail_on=fail_on, policy=policy)
            manifest["items"].append({"file": relative, "status": report["summary"]["status"],
                                      "gate_passed": gate["passed"],
                                      "blocking_check_codes": gate["blocking_check_codes"],
                                      "sha256": report["file"]["sha256"],
                                      "warnings": report["summary"]["warnings"],
                                      "report_json": json_path.relative_to(out).as_posix(),
                                      "report_html": html_path.relative_to(out).as_posix(),
                                      "error": None})
        except AuditError as exc:
            manifest["items"].append({"file": relative, "status": "error", "gate_passed": False,
                                      "blocking_check_codes": ["read_error"],
                                      "sha256": None, "warnings": None,
                                      "report_json": None, "report_html": None,
                                      "error": str(exc)})
    manifest["summary"] = {
        "total": len(manifest["items"]),
        "passed": sum(bool(x["gate_passed"]) for x in manifest["items"]),
        "blocked": sum(not bool(x["gate_passed"]) for x in manifest["items"]),
        "errors": sum(x["status"] == "error" for x in manifest["items"]),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("file", "status", "gate_passed", "warnings", "sha256", "report_html", "error"))
        for item in manifest["items"]:
            writer.writerow((_safe_csv_cell(item["file"]), item["status"],
                             item["gate_passed"], item["warnings"] if item["warnings"] is not None else "",
                             item["sha256"] or "", item["report_html"] or "",
                             _safe_csv_cell(item["error"] or "")))
    rows = "".join(
        '<tr><td>' + html.escape(x["file"]) + '</td><td>' + html.escape(x["status"]) + '</td>'
        + '<td>' + ("YES" if x["gate_passed"] else "NO") + '</td><td>'
        + (f'<a href="{html.escape(x["report_html"], quote=True)}">Audit</a>' if x["report_html"] else html.escape(x["error"] or ""))
        + '</td></tr>' for x in manifest["items"]
    )
    layout = f"""<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AIWallet Batch Release Receipt</title>
    <style>body{{margin:0;padding:5vw;max-width:1000px;font:15px/1.5 system-ui;background:#f4f3ed;color:#173027}}
    h1{{font-size:clamp(32px,5vw,54px)}}table{{width:100%;border-collapse:collapse}}td,th{{padding:12px;border-bottom:1px solid #c5d2c6;text-align:left;word-break:break-word}}a{{color:#165e42}}small{{color:#64736d}}</style></head>
    <body><p>AIWALLET / RELEASE LAB</p><h1>Batch release receipt</h1><p>{manifest['summary']['total']} files inspected. {manifest['summary']['blocked']} blocked by selected CI gate.</p>
    <table><thead><tr><th>File</th><th>Technical</th><th>Gate</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table>
    <p><small>No video bytes are included in this report. A technical PASS is not creative approval or platform guarantee.</small></p></body></html>"""
    (out / "index.html").write_text(layout, encoding="utf-8")
    return manifest


def compare_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Explain exactly which technical findings changed between two exports."""
    old = {c["code"]: c for c in before["checks"]}
    new = {c["code"]: c for c in after["checks"]}
    score = {"pass": 0, "warn": 1, "fail": 2}
    changed = []
    for key in sorted(old.keys() | new.keys()):
        was, now = old.get(key), new.get(key)
        old_state = was["level"] if was else "missing"
        new_state = now["level"] if now else "missing"
        if old_state == new_state:
            continue
        # Losing a check removes its evidence: treat that as a regression, never an improvement.
        regression = (now is None and was is not None) or (
            was is None and now is not None and now["level"] != "pass"
        ) or (was is not None and now is not None and score[now["level"]] > score[was["level"]])
        changed.append({"code": key, "before": old_state, "after": new_state,
                        "regression": bool(regression)})
    numeric = ("duration_seconds", "width", "height", "fps", "bitrate_bps")
    metrics = {}
    for key in numeric:
        a = before["metadata"].get(key)
        b = after["metadata"].get(key)
        if isinstance(a, (float, int)) and isinstance(b, (float, int)):
            metrics[key] = {"before": a, "after": b, "delta": round(b - a, 3)}
    return {"schema": "aiwallet.release-comparison/v1",
            "before_sha256": before["file"]["sha256"],
            "after_sha256": after["file"]["sha256"],
            "same_bytes": before["file"]["sha256"] == after["file"]["sha256"],
            "changed_checks": changed,
            "regression_count": sum(x["regression"] for x in changed),
            "metrics": metrics,
            "limitation": "Delta describes technical checks, not human creativity or distribution results."}


def verify_receipt(video: str | Path, report_path: str | Path, *,
                   policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Re-run the SAME detector settings and compare every technical observation.

    This is repeatability verification, not a digital signature, media rights proof,
    or independent verification of the report author's identity.
    """
    p = _file(video)
    receipt_path = Path(report_path)
    if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 2 * 1024 * 1024:
        raise AuditError("Berikan JSON receipt biasa berukuran maksimal 2 MiB.")
    try:
        raw = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise AuditError("Receipt bukan JSON valid.") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != "1.0":
        raise AuditError("Skema receipt tidak dikenal.")
    orig_file = raw.get("file") or {}
    measurements = raw.get("measurements") or {}
    if not isinstance(orig_file, dict) or not isinstance(measurements, dict):
        raise AuditError("Struktur receipt tidak valid.")
    reasons: list[str] = []
    if raw.get("ruleset") != RULESET:
        reasons.append("ruleset_mismatch")
    from . import __version__
    if raw.get("software_version") != __version__:
        reasons.append("software_version_mismatch")
    digest = sha256(p)
    if orig_file.get("sha256") != digest:
        reasons.append("media_hash_mismatch")
    if orig_file.get("size_bytes") != p.stat().st_size:
        reasons.append("media_size_mismatch")
    quick = not bool(measurements.get("analysis_seconds"))
    # Only rerun a current-algorithm report. Old versions cannot be silently
    # certified as new because event detectors and policy semantics may differ.
    if "ruleset_mismatch" not in reasons and "software_version_mismatch" not in reasons:
        limits = {}
        detectors = measurements.get("detector_min_duration_seconds") or {}
        for field, default in DEFAULT_DETECTOR_SECONDS.items():
            val = detectors.get(field, default)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not 0.02 <= val <= default:
                reasons.append("invalid_detector_setting:" + field)
            else:
                limits[field] = float(val)
        if not any(x.startswith("invalid_detector_setting") for x in reasons):
            fresh = audit_video(p, quick=quick, scan_limits={field: 2 * val for field, val in limits.items()})
            # Twice the recorded filter minimum recreates the same sensitivity;
            # audit_video itself caps the duration at the product defaults.
            for field in ("metadata", "checks", "measurements", "summary"):
                if fresh.get(field) != raw.get(field):
                    reasons.append("changed_" + field)
            if policy is not None:
                verdict = gate_report(fresh, policy=policy, fail_on="none")
                if not verdict["passed"]:
                    reasons.append("policy_blocked")
    return {"schema": "aiwallet.receipt-verification/v1", "verified": not reasons,
            "scope": "metadata_only" if quick else "bounded_media_scan",
            "declared_analysis_seconds": measurements.get("analysis_seconds", 0),
            "media_sha256": digest, "report_sha256": sha256(receipt_path),
            "reason_codes": reasons, "policy_name": policy.get("name") if policy else None,
            "caveat": "Repeatability check, not an author signature, copyright clearance or platform certification."}
