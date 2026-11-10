"""Deterministic media inspection. Never uploads, edits, or publishes user media."""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from . import __version__

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
RULESET = "reels-qc-2026.11.2"
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_DURATION_SECONDS = 30 * 60
MIN_LENGTH_SECONDS = 1.0


class AuditError(ValueError):
    """A video cannot be inspected safely or a required tool is unavailable."""


def _run(args: list[str], *, timeout: int = 45) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False,
                              encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        raise AuditError("Analisis melampaui batas waktu; coba video lebih pendek.") from exc
    except OSError as exc:
        raise AuditError("FFmpeg/FFprobe tidak tersedia. Pasang paket ffmpeg terlebih dahulu.") from exc


def _binary(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise AuditError(f"{name} tidak ditemukan dalam PATH. Pasang FFmpeg terlebih dahulu.")
    return found


def _file(path: str | Path) -> Path:
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise AuditError("Berikan berkas video biasa, bukan symlink atau direktori.")
    if p.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise AuditError("Ekstensi yang didukung: MP4, MOV, M4V, WebM, MKV.")
    size = p.stat().st_size
    if size < 128 or size > MAX_FILE_BYTES:
        raise AuditError("Berkas harus berukuran 128 byte hingga 256 MiB.")
    return p.resolve(strict=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fraction(value: str | None) -> float | None:
    try:
        n = float(Fraction(value or "0"))
        return round(n, 3) if 0.0 < n < 300 else None
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def probe_video(path: str | Path) -> dict[str, Any]:
    p = _file(path)
    r = _run([_binary("ffprobe"), "-v", "error", "-protocol_whitelist", "file,pipe",
              "-show_entries", "stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,bit_rate,field_order:format=duration,size,format_name,bit_rate",
              "-of", "json", str(p)], timeout=25)
    if r.returncode != 0:
        raise AuditError("FFprobe tidak bisa membaca video. Berkas mungkin rusak atau formatnya tidak valid.")
    try:
        data = json.loads(r.stdout)
        streams = data.get("streams", [])
        video = next(x for x in streams if x.get("codec_type") == "video")
        audio = next((x for x in streams if x.get("codec_type") == "audio"), None)
        fmt = data.get("format") or {}
        dur = float(fmt.get("duration", 0))
        width = int(video.get("width", 0))
        height = int(video.get("height", 0))
        if not 0.1 <= dur <= MAX_DURATION_SECONDS or width < 16 or height < 16:
            raise ValueError("video outside accepted bounds")
        fps = _fraction(video.get("avg_frame_rate")) or _fraction(video.get("r_frame_rate"))
        return {"duration_seconds": round(dur, 3), "width": width, "height": height,
                "aspect_ratio": round(width / height, 5), "fps": fps,
                "video_codec": video.get("codec_name", "unknown"),
                "audio_codec": audio.get("codec_name") if audio else None,
                "has_audio": bool(audio), "format": fmt.get("format_name", "unknown"),
                "size_bytes": p.stat().st_size,
                "bitrate_bps": int(fmt.get("bit_rate", 0) or 0),
                "field_order": video.get("field_order", "unknown")}
    except (KeyError, TypeError, ValueError, StopIteration) as exc:
        raise AuditError("Video tidak berisi stream video dan metadata durasi yang valid.") from exc


def _check(checks: list[dict[str, Any]], code: str, level: str, title: str,
           observation: str, advice: str) -> None:
    checks.append({"code": code, "level": level, "title": title,
                   "observation": observation, "advice": advice})


def _run_scan(p: Path, filter_string: str, *, length: float, timeout: int = 60, audio: bool = False) -> str:
    cmd = [_binary("ffmpeg"), "-hide_banner", "-nostdin", "-nostats", "-v", "info",
           "-protocol_whitelist", "file,pipe", "-i", str(p), "-t", str(round(min(length, 90), 3))]
    cmd += (["-map", "0:a:0", "-vn", "-af", filter_string] if audio
            else ["-map", "0:v:0", "-an", "-vf", filter_string])
    cmd += ["-f", "null", "-"]
    r = _run(cmd, timeout=timeout)
    if r.returncode != 0:
        raise AuditError("Salah satu analisis FFmpeg gagal.")
    return r.stderr


def scan_loudness(p: Path, seconds: float) -> tuple[float | None, float | None]:
    text = _run_scan(p, "ebur128=peak=true", length=seconds, audio=True, timeout=70)
    levels = re.findall(r"\bI:\s*(-?[\d.]+)\s*LUFS", text)
    peaks = re.findall(r"\bPeak:\s*(-?[\d.]+)\s*dBFS", text)
    return (float(levels[-1]) if levels else None, float(peaks[-1]) if peaks else None)


def scan_black(p: Path, seconds: float) -> list[dict[str, float]]:
    text = _run_scan(p, "blackdetect=d=0.4:pix_th=0.10", length=seconds, timeout=80)
    pattern = r"black_start:([-\d.]+)\s+black_end:([-\d.]+)\s+black_duration:([-\d.]+)"
    return [{"start": float(a), "end": float(b), "seconds": float(c)}
            for a, b, c in re.findall(pattern, text)][:30]


def scan_freeze(p: Path, seconds: float) -> list[dict[str, float]]:
    text = _run_scan(p, "freezedetect=n=-60dB:d=2.5", length=seconds, timeout=80)
    starts = [float(x) for x in re.findall(r"freeze_start:\s*([-\d.]+)", text)]
    ends = [float(x) for x in re.findall(r"freeze_end:\s*([-\d.]+)", text)]
    return [{"start": s, "end": ends[i] if i < len(ends) else None}
            for i, s in enumerate(starts[:30])]


def scan_silence(p: Path, seconds: float) -> list[dict[str, float | None]]:
    """Report pauses in audio, including one that continues to the end of the scan."""
    text = _run_scan(p, "silencedetect=noise=-50dB:d=0.8", length=seconds, audio=True, timeout=70)
    events = re.findall(r"silence_(start|end):\s*([-\d.]+)", text)
    active: float | None = None
    result: list[dict[str, float | None]] = []
    for typ, val in events:
        time = float(val)
        if typ == "start":
            active = time
        elif active is not None:
            result.append({"start": active, "end": time, "seconds": round(max(0, time - active), 3)})
            active = None
    if active is not None:
        result.append({"start": active, "end": None, "seconds": round(max(0, seconds - active), 3)})
    return result[:30]


def make_poster(path: str | Path, destination: str | Path, duration: float) -> bool:
    p = Path(path)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    position = max(0, min(duration * 0.2, duration - 0.1))
    r = _run([_binary("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "error",
              "-ss", f"{position:.2f}", "-i", str(p), "-frames:v", "1", "-vf",
              "scale='min(600,iw)':-2", "-q:v", "4", "-y", str(target)], timeout=30)
    return r.returncode == 0 and target.is_file() and target.stat().st_size > 500


def audit_video(path: str | Path, *, quick: bool = False) -> dict[str, Any]:
    p = _file(path)
    meta = probe_video(p)
    checks: list[dict[str, Any]] = []
    w, h, fps, dur = meta["width"], meta["height"], meta["fps"], meta["duration_seconds"]
    _check(checks, "geometry", "pass" if 0.54 <= w/h <= 0.58 else "warn", "Format 9:16",
           f"{w} × {h} ({w/h:.3f})",
           "9:16 direkomendasikan untuk video vertikal. Format lain mungkin memang sengaja dipilih.")
    _check(checks, "resolution", "pass" if w >= 720 and h >= 1280 else "warn", "Ketajaman dasar",
           f"{w} × {h}", "Ekspor sekurang-kurangnya 720 × 1280; 1080 × 1920 lebih aman untuk master vertikal.")
    _check(checks, "codec", "pass" if meta["video_codec"] == "h264" else "warn", "Kompatibilitas video",
           meta["video_codec"], "H.264 dalam MP4 biasanya paling mudah diterima lintas platform.")
    _check(checks, "duration", "pass" if 3 <= dur <= 180 else "warn", "Durasi konten singkat",
           f"{dur:g} detik", "Durasi 3–180 detik hanyalah patokan workflow ini, bukan batas resmi platform.")
    _check(checks, "fps", "pass" if fps is not None and 23.5 <= fps <= 60.5 else "warn", "Frame rate",
           f"{fps or 'tidak terbaca'} fps", "Gunakan 24, 25, 30, atau 60 fps bila cocok dengan footage sumber.")
    _check(checks, "audio", "pass" if meta["has_audio"] else "warn", "Ketersediaan audio",
           meta["audio_codec"] or "Tidak ada audio", "Periksa apakah video memang dimaksudkan tanpa suara.")
    _check(checks, "frame_order", "pass" if meta["field_order"] in ("progressive", "unknown", None) else "warn", "Pemindaian progresif",
           str(meta["field_order"]), "Gunakan progressive scan untuk distribusi video sosial.")
    measurements: dict[str, Any] = {"analysis_seconds": 0, "limited_scan": quick or meta["duration_seconds"] > 90.0,
                                    "black_segments": [], "freeze_segments": [], "silence_segments": [], "scan_errors": [],
                                    "integrated_lufs": None, "true_peak_dbfs": None}
    if quick:
        _check(checks, "scan_scope", "warn", "Analisis mendalam dilewati",
               "Metadata dan SHA-256 saja", "Mode quick bukan bukti audio/visual sudah diperiksa. Jalankan tanpa --quick untuk release gate.")
    if not quick:
        length = min(dur, 90.0)
        measurements["analysis_seconds"] = length
        if dur > 90.0:
            _check(checks, "scan_scope", "warn", "Cakupan analisis terbatas",
                   f"90 dari {dur:g} detik", "Segmen setelah 90 detik belum dipindai. Lakukan inspeksi tambahan sebelum rilis.")
        if meta["has_audio"]:
            try:
                loud, peak = scan_loudness(p, length)
                measurements["integrated_lufs"], measurements["true_peak_dbfs"] = loud, peak
                if loud is not None:
                    _check(checks, "loudness", "warn" if loud < -26 or loud > -10 else "pass",
                           "Perkiraan loudness terintegrasi", f"{loud:.1f} LUFS (sampel {length:g} detik)",
                           "Nilai di luar -26 hingga -10 LUFS perlu diperiksa lewat telinga; bukan standar wajib platform.")
                else:
                    _check(checks, "loudness", "warn", "Analisis loudness", "Tidak terukur", "Periksa audio dengan perangkat lain.")
                if peak is not None:
                    _check(checks, "peak", "warn" if peak > -1 else "pass",
                           "True peak", f"{peak:.1f} dBFS", "Sisakan headroom sekitar 1 dBTP untuk kompresi ulang.")
                else:
                    _check(checks, "peak", "warn", "Analisis true peak", "Tidak terukur", "Periksa audio dengan perangkat lain.")
            except AuditError as exc:
                measurements["scan_errors"].append("audio_scan")
                _check(checks, "audio_scan", "warn", "Analisis suara", "Tidak selesai", str(exc))
        if meta["has_audio"]:
            try:
                measurements["silence_segments"] = scan_silence(p, length)
                n = len(measurements["silence_segments"])
                _check(checks, "silence_segments", "warn" if n else "pass", "Jeda audio panjang",
                       f"{n} segmen hening ditemukan", "Jeda hening mungkin disengaja; dengarkan bagian yang tercatat.")
            except AuditError as exc:
                measurements["silence_segments"] = None
                measurements["scan_errors"].append("silence_segments")
                _check(checks, "silence_segments", "warn", "Analisis jeda audio", "Tidak selesai", str(exc))
        for key, scanner in (("black_segments", scan_black), ("freeze_segments", scan_freeze)):
            try:
                measurements[key] = scanner(p, length)
                n = len(measurements[key])
                _check(checks, key, "warn" if n else "pass",
                       "Segmen hitam" if key == "black_segments" else "Segmen diam panjang",
                       f"{n} terdeteksi pada {length:g} detik pertama",
                       "Periksa secara visual; transisi hitam dan gambar diam dapat sepenuhnya disengaja.")
            except AuditError as exc:
                measurements[key] = None
                measurements["scan_errors"].append(key)
                _check(checks, key, "warn", "Analisis visual", "Tidak selesai", str(exc))
    result = ("fail" if any(c["level"] == "fail" for c in checks) else
              "warn" if any(c["level"] == "warn" for c in checks) else "pass")
    return {"schema_version": "1.0", "software_version": __version__,
            "ruleset": RULESET, "created_at": datetime.now(timezone.utc).isoformat(),
            "file": {"name": p.name, "sha256": sha256(p), "size_bytes": meta["size_bytes"]},
            "metadata": meta, "checks": checks, "measurements": measurements,
            "summary": {"status": result, "passed": sum(c["level"] == "pass" for c in checks),
                        "warnings": sum(c["level"] == "warn" for c in checks),
                        "failed": sum(c["level"] == "fail" for c in checks)},
            "caveat": "QC teknis berbasis heuristik, bukan jaminan moderasi, viralitas, atau penerimaan platform."}
