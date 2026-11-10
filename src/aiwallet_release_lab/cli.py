"""Offline command line entry point for the open-source core."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import AuditError, audit_video, make_poster, _binary
from . import __version__
from .report import save_report
from .workflow import audit_batch, compare_reports, gate_report, verify_receipt
from .markers import markers_from_file, markers_csv
from .policy import read_policy
from .watch import WatchSession, run_watch
from .editorial import CRITERIA, RESPONSES, create_review, review_gate, read_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="releaselab", description="QC video pendek lokal tanpa upload atau akun")
    parser.add_argument("--version", action="version", version=f"releaselab {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="Periksa video dan buat audit.json + audit.html")
    audit.add_argument("video", help="Berkas MP4, MOV, M4V, WebM, atau MKV")
    audit.add_argument("--output", "-o", help="Direktori output, default ./release-report")
    audit.add_argument("--quick", action="store_true", help="Metadata saja, tanpa scan audio dan visual")
    gate = sub.add_parser("gate", help="CI release gate dengan exit code nonzero untuk pemeriksaan yang memblokir")
    gate.add_argument("video")
    gate.add_argument("--quick", action="store_true")
    gate.add_argument("--fail-on", choices=("warn", "fail", "none"), default="warn")
    gate.add_argument("--output", "-o", help="Opsional: simpan laporan lengkap")
    gate.add_argument("--policy", help="Policy JSON lokal yang fail-closed untuk studio/CI")
    gate.add_argument("--editorial-review", help="Wajibkan review manual terikat hash sumber; tanpa review, gate kreatif tidak aktif")
    batch = sub.add_parser("batch", help="QC banyak video dan ekspor manifest+CSV+HTML")
    batch.add_argument("folder")
    batch.add_argument("--output", "-o", default="./release-batch")
    batch.add_argument("--quick", action="store_true")
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--max-files", type=int, default=40)
    batch.add_argument("--fail-on", choices=("warn", "fail", "none"), default="warn")
    batch.add_argument("--policy", help="Policy JSON lokal untuk semua video batch")
    watch = sub.add_parser("watch", help="Pantau folder ekspor; jalankan QC ketika berkas sudah stabil")
    watch.add_argument("folder", help="Direktori ekspor (sumber tidak diubah)")
    watch.add_argument("--output", "-o", default="./release-watch", help="Direktori laporan, harus di luar folder video")
    watch.add_argument("--recursive", action="store_true")
    watch.add_argument("--quick", action="store_true")
    watch.add_argument("--policy", help="JSON studio policy yang berlaku untuk semua video baru")
    watch.add_argument("--fail-on", choices=("warn", "fail", "none"), default="warn")
    watch.add_argument("--stable-seconds", type=float, default=3.0, help="Tunggu ukuran dan waktu modifikasi tetap stabil")
    watch.add_argument("--poll-interval", type=float, default=2.0, help="Interval polling dalam detik (0.2–120)")
    watch.add_argument("--max-files", type=int, default=40)
    watch.add_argument("--once", action="store_true", help="Periksa sekali; berguna untuk cron/scheduler")
    compare = sub.add_parser("compare", help="Bandingkan dua ekspor dan tunjukkan regresi teknis")
    compare.add_argument("before")
    compare.add_argument("after")
    compare.add_argument("--quick", action="store_true")
    compare.add_argument("--output", "-o")
    markers = sub.add_parser("markers", help="Ekspor timecoded QC markers dari receipt (CSV atau JSON)")
    markers.add_argument("receipt", help="audit.json dari Release Lab")
    markers.add_argument("--output", "-o", help="Opsional: path CSV/JSON, atau stdout jika tidak ada")
    markers.add_argument("--format", choices=("csv", "json"), default="csv")
    editorial = sub.add_parser("editorial", help="Catat pemeriksaan kreatif manual dari receipt JSON; bukan skor AI")
    editorial.add_argument("receipt", help="Path audit.json dari QC video sebelumnya")
    editorial.add_argument("--reviewer", required=True, help="Nama reviewer (diisi sendiri, tanpa verifikasi identitas)")
    for flag in CRITERIA:
        editorial.add_argument("--"+flag.replace("_", "-"), required=True, choices=RESPONSES)
    editorial.add_argument("--notes", default="", help="Catatan ke editor, maksimum 2400 karakter")
    editorial.add_argument("--output", "-o", default="./editorial-review.json", help="Berkas editorial-review.json")
    verify = sub.add_parser("verify", help="Uji ulang receipt JSON terhadap video asli")
    verify.add_argument("video")
    verify.add_argument("report")
    verify.add_argument("--policy", help="Opsional: policy tambahan untuk audit yang diverifikasi")
    sub.add_parser("doctor", help="Periksa toolchain FFmpeg / FFprobe")
    serve = sub.add_parser("serve", help="Mulai dashboard browser lokal")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=7860)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps({"ffmpeg": _binary("ffmpeg"), "ffprobe": _binary("ffprobe")}, indent=2))
            return 0
        if args.command == "serve":
            try:
                import uvicorn
            except ImportError as exc:
                raise AuditError("Dashboard memerlukan: pip install '.[web]'") from exc
            if args.host not in ("127.0.0.1", "localhost", "::1"):
                raise AuditError("Dashboard hanya boleh di-bind ke loopback pada versi alpha ini.")
            uvicorn.run("aiwallet_release_lab.web:app", host=args.host, port=args.port, log_level="info")
            return 0
        if args.command == "watch":
            session = WatchSession(args.folder, args.output, recursive=args.recursive,
                                   quick=args.quick, fail_on=args.fail_on,
                                   policy=read_policy(args.policy) if args.policy else None,
                                   stable_seconds=0 if args.once else args.stable_seconds,
                                   max_files=args.max_files)
            run_watch(session, poll_interval=args.poll_interval, max_cycles=1 if args.once else None)
            return 0 if session.records and all(row["gate_passed"] for row in session.records.values()) else 3
        if args.command == "editorial":
            receipt = Path(args.receipt)
            if receipt.is_symlink() or not receipt.is_file() or receipt.stat().st_size > 1024*1024:
                raise AuditError("Receipt QC tidak ada atau melebihi 1 MiB.")
            try:
                source = json.loads(receipt.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError) as exc:
                raise AuditError("Receipt QC JSON tidak dapat dibaca.") from exc
            answers = {field: getattr(args, field) for field in CRITERIA}
            output = create_review(source, reviewer=args.reviewer, criteria=answers, notes=args.notes)
            dest = Path(args.output)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            print(json.dumps({"status":output["outcome"], "file":str(dest),
                              "source_sha256":output["file_sha256"],
                              "identity_verified":False}, ensure_ascii=False))
            return 0 if output["outcome"] == "approved" else 3
        if args.command == "verify":
            verification = verify_receipt(args.video, args.report,
                                          policy=read_policy(args.policy) if args.policy else None)
            print(json.dumps(verification, ensure_ascii=False))
            return 0 if verification["verified"] else 3
        if args.command == "batch":
            policy = read_policy(args.policy) if args.policy else None
            manifest = audit_batch(args.folder, args.output, quick=args.quick,
                                   recursive=args.recursive, max_files=args.max_files,
                                   fail_on=args.fail_on, policy=policy)
            print(json.dumps({"path": str(Path(args.output) / "manifest.json"),
                              "summary": manifest["summary"]}, ensure_ascii=False))
            return 3 if manifest["summary"]["blocked"] else 0
        if args.command == "markers":
            parsed = markers_from_file(args.receipt)
            output = markers_csv(parsed) if args.format == "csv" else json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
            if args.output:
                destination = Path(args.output)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(output, encoding="utf-8", newline="")
            else:
                sys.stdout.write(output)
            if not parsed["scan_complete"]:
                print("Warning: source receipt has incomplete technical scan coverage.", file=sys.stderr)
            return 0
        if args.command == "compare":
            report = compare_reports(audit_video(args.before, quick=args.quick),
                                     audit_video(args.after, quick=args.quick))
            if args.output:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False))
            return 3 if report["regression_count"] else 0
        policy = read_policy(args.policy) if args.command == "gate" and args.policy else None
        limits = {field: policy[key] for key, field in (("max_black_segment_seconds", "black_segments"),
                  ("max_freeze_segment_seconds", "freeze_segments"), ("max_silence_segment_seconds", "silence_segments"))
                  if policy is not None and key in policy}
        data = audit_video(args.video, quick=args.quick, scan_limits=limits)
        if args.command == "gate":
            verdict = gate_report(data, fail_on=args.fail_on, policy=policy)
            if args.editorial_review:
                try:
                    editorial_data = read_review(args.editorial_review)
                    review_result = review_gate(data, editorial_data)
                except (AuditError, OSError) as exc:
                    review_result = {"schema":"aiwallet.editorial-gate/v1", "passed":False,
                                     "blocking_check_codes":["review:missing_or_unreadable"],
                                     "reviewer_identity_verified":False,
                                     "disclaimer":"The editorial review could not be read; release blocked."}
                verdict["editorial_gate"] = review_result
                if not review_result["passed"]:
                    verdict["passed"] = False
                    verdict["blocking_check_codes"].extend(review_result["blocking_check_codes"])
            if args.output:
                destination = Path(args.output)
                poster = destination / "poster.jpg"
                made = make_poster(args.video, poster, data["metadata"]["duration_seconds"])
                save_report(data, destination, poster if made else None)
            print(json.dumps(verdict, ensure_ascii=False))
            return 0 if verdict["passed"] else 3
        destination = Path(args.output or "release-report")
        poster = destination / "poster.jpg"
        made = make_poster(args.video, poster, data["metadata"]["duration_seconds"])
        json_path, html_path = save_report(data, destination, poster if made else None)
        print(json.dumps({"status": data["summary"]["status"], "json": str(json_path),
                          "html": str(html_path), "warnings": data["summary"]["warnings"]}, ensure_ascii=False))
        return 0
    except AuditError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
