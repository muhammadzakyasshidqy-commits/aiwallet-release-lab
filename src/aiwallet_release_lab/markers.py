"""Generic QC timeline export. No NLE-specific import compatibility is claimed.

A marker is supporting technical evidence from an existing Release Lab receipt,
NOT an editorial instruction or platform acceptance record.
"""
from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
from typing import Any

from .core import AuditError

MAX_RECEIPT_BYTES = 2 * 1024 * 1024
MAX_MARKERS = 1500
FIELDS = (
    'kind', 'start_seconds', 'end_seconds', 'duration_seconds', 'start_timestamp',
    'end_timestamp', 'approx_frame_start', 'approx_frame_end', 'source_video', 'note',
)
TYPES = (
    ('black_segments', 'black', 'Black video interval; may be deliberate'),
    ('freeze_segments', 'freeze', 'Static/frozen picture interval; may be deliberate'),
    ('silence_segments', 'silence', 'Quiet audio interval; may be deliberate'),
)


def _finite_float(value: Any, name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise AuditError(f'Invalid receipt number: {name}')
    return float(value)


def _timestamp(seconds: float) -> str:
    # Millisecond timestamp, *not* SMPTE drop-frame or an official NLE marker format.
    millis = round(seconds * 1000)
    hours, remain = divmod(millis, 3_600_000)
    minutes, remain = divmod(remain, 60_000)
    secs, milli = divmod(remain, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}.{milli:03d}'


def _csv_safe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    # Full, not stripped, content retains source references but prevents formula runs.
    if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
        return "'" + value
    return value


def extract_markers(report: Any) -> dict[str, Any]:
    """Strictly validate event structure and return bounded, chronological markers."""
    if not isinstance(report, dict) or report.get('schema_version') != '1.0':
        raise AuditError('Receipt JSON schema_version harus 1.0.')
    metadata, measures, source = report.get('metadata'), report.get('measurements'), report.get('file')
    if not isinstance(metadata, dict) or not isinstance(measures, dict) or not isinstance(source, dict):
        raise AuditError('Metadata/measurements/file receipt hilang.')
    filename = source.get('name')
    if not isinstance(filename, str) or len(filename) > 300:
        raise AuditError('Nama media receipt tidak valid.')
    duration = _finite_float(metadata.get('duration_seconds'), 'duration_seconds', minimum=0.01)
    fps = _finite_float(metadata.get('fps'), 'fps', minimum=0.01)
    if fps > 240 or duration > 24 * 3600:
        raise AuditError('FPS/durasi receipt di luar batas.')
    coverage = _finite_float(measures.get('analysis_seconds', 0), 'analysis_seconds')
    if coverage > duration + 1.5:
        raise AuditError('Cakupan scan melebihi durasi video.')
    errors = measures.get('scan_errors', [])
    truncated = measures.get('truncated_sections', [])
    if not isinstance(errors, list) or not isinstance(truncated, list):
        raise AuditError('Status cakupan scan tidak valid.')
    if len(errors) > 100 or len(truncated) > 20:
        raise AuditError('Metadata pemindaian terlalu panjang.')
    rows: list[dict[str, Any]] = []
    for field, kind, note in TYPES:
        segments = measures.get(field, [])
        if not isinstance(segments, list):
            raise AuditError(f'Field {field} bukan daftar.')
        if len(segments) > MAX_MARKERS:
            raise AuditError(f'Terlalu banyak segmen dalam {field}.')
        for entry in segments:
            if not isinstance(entry, dict):
                raise AuditError(f'Segmen {kind} harus objek.')
            start = _finite_float(entry.get('start'), f'{kind}.start')
            if start > duration + 0.2:
                raise AuditError('Segmen dimulai di luar media.')
            end_value = entry.get('end')
            if end_value is None:
                # A null end in an FFmpeg event is an open interval, not proof of an end.
                end = min(coverage, duration) if coverage > start else None
                end_is_estimated = end is not None
            else:
                end = _finite_float(end_value, f'{kind}.end')
                end_is_estimated = False
            if end is not None and (end < start or end > duration + 0.2):
                raise AuditError('Segmen berakhir di luar media.')
            if len(rows) >= MAX_MARKERS:
                raise AuditError(f'Maksimal {MAX_MARKERS} penanda per receipt.')
            length = round(end - start, 6) if end is not None else None
            row = {
                'kind': kind,
                'start_seconds': round(start, 6),
                'end_seconds': round(end, 6) if end is not None else None,
                'duration_seconds': length,
                'start_timestamp': _timestamp(start),
                'end_timestamp': _timestamp(end) if end is not None else '',
                'approx_frame_start': round(start * fps),
                'approx_frame_end': round(end * fps) if end is not None else None,
                'source_video': filename,
                'note': note + ('; end estimated from scan coverage' if end_is_estimated else ''),
            }
            rows.append(row)
    rows.sort(key=lambda e: (e['start_seconds'], e['kind']))
    limited = coverage + 0.15 < duration or bool(measures.get('limited_scan'))
    complete = coverage > 0 and not limited and not errors and not truncated
    return {
        'schema': 'aiwallet.release-markers/v1', 'source_name': filename,
        'media_sha256': source.get('sha256'),
        'duration_seconds': duration, 'fps': fps,
        'analysis_seconds': coverage,
        'scan_complete': complete,
        'scan_errors_present': bool(errors),
        'truncated_sections': [str(x)[:60] for x in truncated],
        'markers': rows,
        'limitation': 'Generic CSV/JSON markers only. Approximate frames; no SMPTE drop-frame, NLE-import claim, or creative approval. Missing markers are not evidence of a clean video without complete scans.',
    }


def markers_csv(result: dict[str, Any]) -> str:
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS, extrasaction='ignore', lineterminator='\r\n')
    writer.writeheader()
    for row in result['markers']:
        writer.writerow({field: _csv_safe(row.get(field) if row.get(field) is not None else '') for field in FIELDS})
    return output.getvalue()


def markers_from_file(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_RECEIPT_BYTES:
        raise AuditError('Receipt JSON tidak ada, berupa symlink, atau melebihi 2 MiB.')
    try:
        content = json.loads(p.read_text(encoding='utf8'))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise AuditError('Berkas receipt JSON tidak valid.') from exc
    return extract_markers(content)
