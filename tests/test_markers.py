"""v0.5: NLE-neutral timeline and bounded, safely encoded evidence export."""
from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aiwallet_release_lab.cli import main
from aiwallet_release_lab.core import AuditError, audit_video
from aiwallet_release_lab.markers import extract_markers, markers_csv, markers_from_file
from aiwallet_release_lab.web import create_app


def receipt():
    path = Path(__file__).parents[1] / 'site' / 'demo' / 'audit.json'
    return json.loads(path.read_text('utf8'))


def test_black_and_freeze_become_bounded_sorted_timestamps():
    r = extract_markers(receipt())
    assert r['schema'] == 'aiwallet.release-markers/v1'
    assert r['fps'] == 24
    assert r['markers']
    assert r['markers'][0]['start_timestamp'] == '00:00:00.000'
    assert all(m['kind'] in ('black', 'freeze', 'silence') for m in r['markers'])
    assert r['markers'] == sorted(r['markers'], key=lambda m: (m['start_seconds'], m['kind']))
    assert all('platform guarantee' not in m['note'] for m in r['markers'])
    assert r['scan_complete'] in (True, False)
    assert 'no SMPTE drop-frame' in r['limitation']


def test_unclosed_events_must_be_labeled_as_estimated():
    report = receipt()
    report['measurements']['analysis_seconds'] = 2.0
    report['metadata']['duration_seconds'] = 3.0
    report['measurements']['freeze_segments'] = [{'start': 1.0, 'end': None}]
    markers = extract_markers(report)['markers']
    freeze = next(x for x in markers if x['kind'] == 'freeze')
    assert freeze['end_seconds'] == 2.0
    assert 'estimated' in freeze['note']
    assert extract_markers(report)['scan_complete'] is False


def test_spreadsheet_injection_is_escaped_in_marker_csv():
    r = receipt()
    r['file']['name'] = '=HYPERLINK("https://evil.invalid")'
    rows = list(csv.DictReader(io.StringIO(markers_csv(extract_markers(r)))))
    assert rows
    assert rows[0]['source_video'].startswith("'=")
    assert rows[0]['source_video'].endswith(')')
    assert rows[0]['start_timestamp'].startswith('00:')


def test_non_integer_frame_rates_are_approximate_not_dropframe():
    r = receipt()
    r['metadata']['fps'] = 30000 / 1001
    out = extract_markers(r)
    assert out['markers'][0]['approx_frame_start'] == 0
    assert 'no SMPTE drop-frame' in out['limitation']


@pytest.mark.parametrize('bad', [
    {'metadata': {'fps': 'oops'}},
    {'metadata': {'duration_seconds': float('nan')}},
    {'measurements': {'black_segments': 'not-list'}},
    {'measurements': {'freeze_segments': [{'start': -1, 'end': 1}]}},
    {'measurements': {'black_segments': [{'start': 999, 'end': 1000}]}},
    {'measurements': {'black_segments': [{'start': 2, 'end': 1}]}},
    {'measurements': {'analysis_seconds': 1000}},
])
def test_malformed_receipt_fails_closed(bad):
    r = receipt()
    for k, val in bad.items():
        r[k].update(val)
    with pytest.raises(AuditError):
        extract_markers(r)


def test_quick_scan_without_events_not_claimed_complete(sample_video):
    quick = audit_video(sample_video, quick=True)
    out = extract_markers(quick)
    assert out['markers'] == []
    assert out['scan_complete'] is False


def test_cli_writes_both_formats_without_reprocessing(sample_video, tmp_path):
    r = audit_video(sample_video, quick=True)
    p = tmp_path/'audit.json';p.write_text(json.dumps(r))
    output = tmp_path/'markers.csv'
    assert main(['markers', str(p), '-o', str(output)]) == 0
    assert 'start_seconds' in output.read_text()
    out = tmp_path/'markers.json'
    assert main(['markers', str(p), '--format', 'json', '-o', str(out)]) == 0
    assert json.loads(out.read_text())['schema'] == 'aiwallet.release-markers/v1'


def test_reject_large_or_symlink_marker_receipt(tmp_path):
    large = tmp_path/'large.json';large.write_bytes(b'x'*(2*1024*1024+1))
    with pytest.raises(AuditError):
        markers_from_file(large)
    link = tmp_path/'link.json';link.symlink_to(large)
    with pytest.raises(AuditError):
        markers_from_file(link)


def test_web_markers_download_and_deletion(sample_video, tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        with sample_video.open('rb') as fh:
            r = c.post('/api/audits', files={'file':('video.mp4', fh, 'video/mp4')})
        assert r.status_code == 201
        id_ = r.json()['id']
        markers = c.get(f'/api/reports/{id_}/markers.csv')
        assert markers.status_code == 200
        assert markers.headers['content-type'].startswith('text/csv')
        assert 'attachment' in markers.headers['content-disposition']
        assert markers.text.startswith('kind,start_seconds,')
        assert c.get('/api/reports/traversal/markers.csv').status_code == 404
        assert c.delete('/api/reports/'+id_).status_code == 200
        assert c.get(f'/api/reports/{id_}/markers.csv').status_code == 404
