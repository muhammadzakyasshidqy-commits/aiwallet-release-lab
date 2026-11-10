"""Human editorial release notes. Never infer creative quality from video metrics.

Reviews bind to exact original source SHA-256 and the technical ruleset. Reviewer
names are *self-entered*, not authenticated identities or digital signatures.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import AuditError

SCHEMA = "aiwallet.editorial-review/v1"
CRITERIA = ("story_hook", "visual_clarity", "pacing", "sound_design", "brand_accuracy")
RESPONSES = ("pass", "changes_requested", "not_applicable")
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


def _validate_input(name: str, criteria: dict[str, str], notes: str) -> None:
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 100:
        raise AuditError("Nama reviewer harus terdiri dari 2–100 karakter.")
    if not isinstance(notes, str) or len(notes) > 2400:
        raise AuditError("Catatan reviewer maksimum 2.400 karakter.")
    if not isinstance(criteria, dict) or set(criteria) != set(CRITERIA) or any(
        type(v) is not str or v not in RESPONSES for v in criteria.values()
    ):
        raise AuditError("Semua lima bagian review wajib dijawab: pass, changes_requested, atau not_applicable.")
    if all(v == "not_applicable" for v in criteria.values()):
        raise AuditError("Tidak boleh menyetujui review tanpa mengevaluasi satu pun kriteria.")


def create_review(report: dict[str, Any], *, reviewer: str,
                  criteria: dict[str, str], notes: str = "") -> dict[str, Any]:
    """Create an honest human-supplied review bound to a technical audit receipt."""
    _validate_input(reviewer, criteria, notes)
    try:
        sha = report["file"]["sha256"]
        ruleset = report["ruleset"]
        filename = report["file"]["name"]
    except (KeyError, TypeError) as exc:
        raise AuditError("Receipt QC belum valid atau tidak memuat hash sumber.") from exc
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise AuditError("Hash SHA-256 sumber tidak valid.")
    if not isinstance(ruleset, str) or not ruleset or len(ruleset) > 150:
        raise AuditError("Versi aturan QC tidak valid.")
    if not isinstance(filename, str) or not filename or len(filename) > 512:
        raise AuditError("Nama sumber video tidak valid.")
    return {
        "schema": SCHEMA,
        "file_sha256": sha,
        "file_name": filename,
        "ruleset": ruleset,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "reviewer": reviewer.strip(),
        "criteria": {field: criteria[field] for field in CRITERIA},
        "notes": notes.strip(),
        "outcome": "changes_requested" if "changes_requested" in criteria.values() else "approved",
        "identity_verified": False,
        "warning": "Self-declared editorial review, not an authenticated signature or proof of rights.",
    }


def review_gate(report: dict[str, Any], review: Any) -> dict[str, Any]:
    """Fail closed on absent/stale/invalid editorial review; never fake approval."""
    reasons: list[str] = []
    if not isinstance(review, dict):
        reasons.append("review:missing")
    elif review.get("schema") != SCHEMA:
        reasons.append("review:invalid_schema")
    else:
        fields = review.get("criteria")
        try:
            _validate_input(review.get("reviewer"), fields, review.get("notes"))
        except AuditError:
            reasons.append("review:invalid_content")
        if review.get("file_sha256") != report.get("file", {}).get("sha256"):
            reasons.append("review:source_changed")
        if review.get("ruleset") != report.get("ruleset"):
            reasons.append("review:ruleset_changed")
        if not isinstance(review.get("created_at"), str) or not review["created_at"].endswith("+00:00"):
            reasons.append("review:timestamp_invalid")
        if review.get("identity_verified") is not False:
            reasons.append("review:identity_claim_invalid")
        if not reasons:
            should_approve = "changes_requested" not in fields.values()
            if review.get("outcome") != ("approved" if should_approve else "changes_requested"):
                reasons.append("review:outcome_inconsistent")
            elif not should_approve:
                reasons.append("review:changes_requested")
    return {
        "schema": "aiwallet.editorial-gate/v1",
        "passed": not reasons,
        "blocking_check_codes": reasons,
        "reviewer_identity_verified": False,
        "source_bound": isinstance(review, dict) and report.get("file", {}).get("sha256") == review.get("file_sha256"),
        "disclaimer": "Editorial evidence is a self-attestation; it does not authenticate a reviewer or certify creativity.",
    }


def read_review(path: str | Path) -> Any:
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > 32768:
        raise AuditError("File editorial review tidak tersedia atau melebihi 32 KiB.")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise AuditError("JSON editorial review tidak valid.") from exc
