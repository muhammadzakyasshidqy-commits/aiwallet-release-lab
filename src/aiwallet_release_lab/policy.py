"""Versioned, self-contained studio delivery policies.

Policies are local JSON, not Instagram/TikTok/YouTube certification rules.
Unknown keys and non-finite numbers fail closed so a typo cannot silently weaken a gate.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .core import AuditError, DEFAULT_DETECTOR_SECONDS

SCHEMA = "aiwallet.release-policy/v1"
NUMERIC = {
    "min_width": (16.0, 16384.0),
    "min_height": (16.0, 16384.0),
    "min_fps": (1.0, 240.0),
    "max_fps": (1.0, 240.0),
    "min_duration_seconds": (0.1, 1800.0),
    "max_duration_seconds": (0.1, 1800.0),
    "min_lufs": (-70.0, 0.0),
    "max_lufs": (-70.0, 0.0),
    "max_true_peak_dbfs": (-30.0, 3.0),
    "max_black_segment_seconds": (0.0, 90.0),
    "max_freeze_segment_seconds": (0.0, 90.0),
    "max_silence_segment_seconds": (0.0, 90.0),
}
BOOL = {"require_audio", "require_full_scan"}
OTHER = {"schema", "name", "allowed_codecs"}
MAX_POLICY_BYTES = 16 * 1024


def validate_policy(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise AuditError("Policy harus berupa objek JSON.")
    if data.get("schema") != SCHEMA:
        raise AuditError("Schema policy harus aiwallet.release-policy/v1.")
    unknown = set(data) - set(NUMERIC) - BOOL - OTHER
    if unknown:
        raise AuditError("Field policy tidak dikenal: " + ", ".join(sorted(unknown)))
    name = data.get("name", "unnamed-policy")
    if not isinstance(name, str) or not 1 <= len(name) <= 100:
        raise AuditError("Nama policy harus string 1–100 karakter.")
    for key in BOOL:
        if key in data and not isinstance(data[key], bool):
            raise AuditError(f"Policy {key} harus boolean.")
    for key, (minimum, maximum) in NUMERIC.items():
        if key in data:
            value = data[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
                raise AuditError(f"Policy {key} harus angka hingga rentang {minimum:g}–{maximum:g}.")
    codecs = data.get("allowed_codecs")
    if codecs is not None and (not isinstance(codecs, list) or not 1 <= len(codecs) <= 12 or
                               any(not isinstance(s, str) or not 1 <= len(s) <= 25 or not s.replace('_','').isalnum() for s in codecs)):
        raise AuditError("allowed_codecs harus array terbatas nama codec.")
    for lo, hi in (("min_fps", "max_fps"), ("min_duration_seconds", "max_duration_seconds"), ("min_lufs", "max_lufs")):
        if lo in data and hi in data and data[lo] > data[hi]:
            raise AuditError(f"Policy {lo} tidak boleh melampaui {hi}.")
    return dict(data)


def read_policy(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_POLICY_BYTES:
        raise AuditError("Policy tidak ada, berupa symlink, atau melebihi 16 KiB.")
    try:
        return validate_policy(json.loads(p.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise AuditError("Policy JSON tidak valid atau bukan UTF-8.") from exc


def evaluate_policy(report: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Return blocking technical deviations from a user-owned delivery spec."""
    p = validate_policy(policy)
    meta = report["metadata"]
    measurements = report["measurements"]
    findings: list[dict[str, Any]] = []

    def block(code: str, observed: Any, expected: str) -> None:
        findings.append({"code": code, "observed": observed, "expected": expected})

    for key, actual in (("min_width", meta["width"]), ("min_height", meta["height"]),
                        ("min_fps", meta["fps"]), ("min_duration_seconds", meta["duration_seconds"])):
        if key in p and (actual is None or actual < p[key]):
            block(key, actual, f"at least {p[key]}")
    for key, actual in (("max_fps", meta["fps"]), ("max_duration_seconds", meta["duration_seconds"])):
        if key in p and (actual is None or actual > p[key]):
            block(key, actual, f"at most {p[key]}")
    if "allowed_codecs" in p and meta["video_codec"] not in p["allowed_codecs"]:
        block("allowed_codecs", meta["video_codec"], " / ".join(p["allowed_codecs"]))
    if p.get("require_audio") and not meta["has_audio"]:
        block("require_audio", False, "audio stream present")
    coverage = measurements.get("analysis_seconds") or 0
    if p.get("require_full_scan") and (measurements.get("limited_scan") or measurements.get("scan_errors") or coverage + 0.15 < meta["duration_seconds"]):
        block("require_full_scan", {"requested_seconds": round(coverage, 3),
                                    "scan_errors": measurements.get("scan_errors", [])},
              f"all {meta['duration_seconds']} seconds successfully measured")

    def measure(key: str, field: str, op: str) -> None:
        if key not in p:
            return
        actual = measurements.get(field)
        if actual is None:
            # A threshold that cannot be observed is not a passing check.
            if field in ("integrated_lufs", "true_peak_dbfs") and not meta["has_audio"] and not p.get("require_audio"):
                return  # explicit permission for silent videos
            block(key, None, "measurement available")
        elif (op == "min" and actual < p[key]) or (op == "max" and actual > p[key]):
            block(key, actual, f"{op} {'>=' if op=='min' else '<='} {p[key]}")

    if meta["has_audio"]:
        measure("min_lufs", "integrated_lufs", "min")
        measure("max_lufs", "integrated_lufs", "max")
        measure("max_true_peak_dbfs", "true_peak_dbfs", "max")

    for key, field in (("max_black_segment_seconds", "black_segments"),
                       ("max_freeze_segment_seconds", "freeze_segments"),
                       ("max_silence_segment_seconds", "silence_segments")):
        if key not in p:
            continue
        if field == "silence_segments" and not meta["has_audio"] and not p.get("require_audio"):
            continue
        if coverage <= 0:
            block(key, None, "scan required")
            continue
        detectors = measurements.get("detector_min_duration_seconds") or DEFAULT_DETECTOR_SECONDS
        min_detectable = detectors.get(field, DEFAULT_DETECTOR_SECONDS[field])
        # Historical reports and quick scans may omit detector precision.
        # A threshold below the detector sensitivity cannot yield proof of PASS.
        if p[key] < min_detectable:
            block(key, {"detector_min_duration_seconds": min_detectable},
                  f"detection sensitivity <= policy maximum {p[key]}")
            continue
        if field in (measurements.get("truncated_sections") or []):
            block(key, "events_truncated", "full event set required")
            continue
        segments = measurements.get(field)
        if segments is None:
            block(key, None, "scan data required")
            continue
        for segment in segments:
            duration = segment.get("seconds")
            if duration is None and segment.get("end") is not None:
                duration = segment["end"] - segment["start"]
            if duration is None:
                duration = max(0.0, coverage - segment["start"])
            if duration > p[key]:
                block(key, {"start": segment["start"], "seconds": round(duration, 3)}, f"segment <= {p[key]} seconds")
    return findings
