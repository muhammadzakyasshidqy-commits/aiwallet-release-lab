"""v0.4 evidence: strict detector resolution and rerunnable receipts."""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from aiwallet_release_lab.cli import main
from aiwallet_release_lab.core import AuditError, audit_video
from aiwallet_release_lab.policy import evaluate_policy
from aiwallet_release_lab.workflow import verify_receipt, gate_report


def _clip(tmp_path: Path, color: str, duration: float, *, mode: str = 'video') -> Path:
    path = tmp_path / f'{color}_segment.mp4'
    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-f', 'lavfi', '-i', f'color=c={color}:s=360x640:r=24:d={duration}',
        '-f', 'lavfi', '-i', 'testsrc2=s=360x640:r=24:d=2',
        '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]',
        '-map', '[v]', '-c:v', 'libx264', '-threads', '2', '-y', str(path),
    ]
    subprocess.run(command, check=True, timeout=35)
    return path


def test_default_black_detector_is_not_allowed_to_claim_stricter_sensitivity(tmp_path):
    video = _clip(tmp_path, 'black', 0.28)
    report = audit_video(video)
    assert report['measurements']['black_segments'] == []
    policy = {'schema': 'aiwallet.release-policy/v1', 'name': 'strict-black',
              'max_black_segment_seconds': 0.16}
    blocks = evaluate_policy(report, policy)
    assert any(v['code'] == 'max_black_segment_seconds' for v in blocks)
    new = audit_video(video, scan_limits={'black_segments': 0.16})
    assert new['measurements']['black_segments']
    assert any(v['code'] == 'max_black_segment_seconds' and 'start' in v['observed']
               for v in evaluate_policy(new, policy))


def test_adaptive_freeze_detector_catches_short_static_section(tmp_path):
    video = _clip(tmp_path, 'blue', 1.12)
    old = audit_video(video)
    assert old['measurements']['freeze_segments'] == []
    policy = {'schema': 'aiwallet.release-policy/v1', 'name': 'strict-freeze',
              'max_freeze_segment_seconds': 0.45}
    new = audit_video(video, scan_limits={'freeze_segments': 0.45})
    assert new['measurements']['freeze_segments']
    assert not gate_report(new, policy=policy, fail_on='none')['passed']


def test_adaptive_audio_detector_detects_silence_below_old_threshold(tmp_path):
    path = tmp_path / 'audio_silence.mp4'
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error',
           '-f', 'lavfi', '-i', 'testsrc2=s=360x640:r=24:d=3',
           '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=3',
           '-filter_complex', r'[1:a]volume=enable=between(t\,1\,1.65):volume=0[a]',
           '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-threads', '2',
           '-c:a', 'aac', '-shortest', '-y', str(path)]
    subprocess.run(cmd, check=True, timeout=35)
    report = audit_video(path)
    assert report['measurements']['silence_segments'] == []
    updated = audit_video(path, scan_limits={'silence_segments': 0.35})
    assert updated['measurements']['silence_segments']
    policy = {'schema': 'aiwallet.release-policy/v1', 'name': 'silence-limit',
              'max_silence_segment_seconds': 0.35}
    assert any(v['code'] == 'max_silence_segment_seconds' for v in evaluate_policy(updated, policy))


def test_unmeasured_thresholds_and_event_truncation_fail_closed(sample_video):
    report = audit_video(sample_video)
    for field in ('black_segments', 'freeze_segments', 'silence_segments'):
        policy = {'schema': 'aiwallet.release-policy/v1', 'name': field,
                  'max_' + field[:-1] + '_seconds': 0.01}
        # Use the actual names; audit policy must not claim proof below detector precision.
        names = {'black_segments': 'max_black_segment_seconds',
                 'freeze_segments': 'max_freeze_segment_seconds',
                 'silence_segments': 'max_silence_segment_seconds'}
        policy = {'schema': 'aiwallet.release-policy/v1', 'name': field, names[field]: 0.0}
        assert any(x['code'] == names[field] for x in evaluate_policy(report, policy))
    policy = {'schema': 'aiwallet.release-policy/v1', 'name': 'no-truncation',
              'max_black_segment_seconds': 1.0}
    updated = copy.deepcopy(report)
    updated['measurements']['truncated_sections'] = ['black_segments']
    assert any(x['observed'] == 'events_truncated' for x in evaluate_policy(updated, policy))


def test_verify_repeats_proof_and_catches_tampering(sample_video, tmp_path, capsys):
    output = tmp_path / 'receipt.json'
    report = audit_video(sample_video, quick=True)
    output.write_text(json.dumps(report))
    assert verify_receipt(sample_video, output)['verified'] is True
    assert main(['verify', str(sample_video), str(output)]) == 0
    assert json.loads(capsys.readouterr().out)['verified'] is True
    report['summary']['warnings'] = 0
    output.write_text(json.dumps(report))
    assert 'changed_summary' in verify_receipt(sample_video, output)['reason_codes']
    assert main(['verify', str(sample_video), str(output)]) == 3
    assert json.loads(capsys.readouterr().out)['verified'] is False


def test_verify_policy_bound_to_receipt(sample_video, tmp_path):
    output = tmp_path / 'receipt.json'
    report = audit_video(sample_video)
    output.write_text(json.dumps(report))
    strict = {'schema': 'aiwallet.release-policy/v1', 'name': 'strict', 'min_width': 720}
    result = verify_receipt(sample_video, output, policy=strict)
    assert not result['verified']
    assert 'policy_blocked' in result['reason_codes']


def test_verify_rejects_old_ruleset_and_symlink(sample_video, tmp_path):
    output = tmp_path / 'receipt.json'
    report = audit_video(sample_video, quick=True)
    report['ruleset'] = 'legacy'
    output.write_text(json.dumps(report))
    verdict = verify_receipt(sample_video, output)
    assert not verdict['verified']
    assert 'ruleset_mismatch' in verdict['reason_codes']
    link = tmp_path / 'link.json'
    link.symlink_to(output)
    with pytest.raises(AuditError):
        verify_receipt(sample_video, link)


def test_verify_rejects_different_video(sample_video, black_video, tmp_path):
    output = tmp_path / 'receipt.json'
    output.write_text(json.dumps(audit_video(sample_video, quick=True)))
    result = verify_receipt(black_video, output)
    assert not result['verified']
    assert 'media_hash_mismatch' in result['reason_codes']


def test_detector_input_guard(sample_video):
    for setting in [{'black_segments': -1.0}, {'black_segments': float('nan')},
                    {'unknown': 0.5}, {'freeze_segments': True}]:
        with pytest.raises(AuditError):
            audit_video(sample_video, quick=True, scan_limits=setting)
