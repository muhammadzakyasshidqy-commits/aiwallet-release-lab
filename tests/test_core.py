import json
import pathlib
import re

import pytest

from aiwallet_release_lab.core import AuditError, audit_video, make_poster, probe_video, sha256
from aiwallet_release_lab.report import render_html, save_report


def test_real_video_metadata(sample_video):
    meta = probe_video(sample_video)
    assert meta["width"] == 480
    assert meta["height"] == 854
    assert meta["video_codec"] == "h264"
    assert meta["has_audio"] is True
    assert meta["fps"] == 24
    assert 3.0 < meta["duration_seconds"] < 3.4


def test_deterministic_checks_and_hash(sample_video):
    report = audit_video(sample_video, quick=True)
    assert report["file"]["sha256"] == sha256(sample_video)
    assert report["summary"]["status"] in {"pass", "warn"}
    assert report["ruleset"] == "reels-qc-2026.11.2"
    assert {c["code"] for c in report["checks"]} >= {"geometry", "codec", "fps", "duration", "audio"}
    assert sum(report["summary"][k] for k in ["passed", "warnings", "failed"]) == len(report["checks"])


def test_real_ffmpeg_scans(sample_video):
    report = audit_video(sample_video)
    assert report["measurements"]["analysis_seconds"] >= 3.1
    assert "integrated_lufs" in report["measurements"]
    assert isinstance(report["measurements"]["black_segments"], list)
    assert isinstance(report["measurements"]["freeze_segments"], list)


def test_black_is_a_warning_not_an_absolute_fail(black_video):
    report = audit_video(black_video)
    assert report["metadata"]["has_audio"] is False
    assert any(c["code"] == "audio" and c["level"] == "warn" for c in report["checks"])
    assert report["summary"]["status"] == "warn"
    assert report["measurements"]["black_segments"]


def test_poster_and_report_export(sample_video, tmp_path):
    report = audit_video(sample_video, quick=True)
    poster = tmp_path / "cover.jpg"
    assert make_poster(sample_video, poster, report["metadata"]["duration_seconds"])
    j, h = save_report(report, tmp_path, poster)
    assert j.is_file() and h.is_file()
    assert json.loads(j.read_text())["file"]["sha256"] == report["file"]["sha256"]
    assert "data:image/jpeg;base64," in h.read_text()


def test_html_report_escapes_user_supplied_names(sample_video):
    report = audit_video(sample_video, quick=True)
    report["file"]["name"] = '<img src=x onerror="alert(1)">.mp4'
    h = render_html(report)
    assert "&lt;img" in h
    assert '<img src=x onerror=' not in h


def test_reject_invalid_media_extension(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_bytes(b"wrong data" * 60)
    with pytest.raises(AuditError):
        audit_video(p)


def test_reject_fake_mp4(tmp_path):
    p = tmp_path / "fake.mp4"
    p.write_bytes(b"fake data" * 100)
    with pytest.raises(AuditError):
        audit_video(p)


def test_reject_symlink(sample_video, tmp_path):
    p = tmp_path / "link.mp4"
    p.symlink_to(sample_video)
    with pytest.raises(AuditError):
        audit_video(p)
