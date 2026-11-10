"""Real media and adversarial workflow tests for CI and batch handoff."""
import csv
import json
import shutil
from pathlib import Path

import pytest

from aiwallet_release_lab.core import AuditError, audit_video
from aiwallet_release_lab.cli import main
from aiwallet_release_lab.workflow import audit_batch, compare_reports, discover_videos, gate_report, _safe_csv_cell


def test_gate_warn_blocks_warn(sample_video):
    report = audit_video(sample_video, quick=True)
    assert report['summary']['warnings'] > 0  # low resolution fixture
    result = gate_report(report, fail_on='warn')
    assert result['passed'] is False
    assert 'resolution' in result['blocking_check_codes']


def test_gate_fail_does_not_block_heuristic_warning(sample_video):
    report = audit_video(sample_video, quick=True)
    result = gate_report(report, fail_on='fail')
    assert result['passed'] is True
    assert result['blocking_check_codes'] == []
    assert result['technical_status'] == 'warn'


def test_gate_none_explicit_opt_out(sample_video):
    report = audit_video(sample_video, quick=True)
    assert gate_report(report, fail_on='none')['passed'] is True
    with pytest.raises(AuditError):
        gate_report(report, fail_on='not_valid')


def test_batch_real_video_with_isolated_reports(sample_video, tmp_path):
    source = tmp_path/'input'
    source.mkdir()
    shutil.copy2(sample_video, source/'first.mp4')
    shutil.copy2(sample_video, source/'second.mp4')
    manifest = audit_batch(source, tmp_path/'output', quick=True)
    assert manifest['summary'] == {'total': 2, 'passed': 0, 'blocked': 2, 'errors': 0}
    assert len({x['report_html'] for x in manifest['items']}) == 2
    assert (tmp_path/'output'/'index.html').is_file()
    assert (tmp_path/'output'/'manifest.json').is_file()
    assert (tmp_path/'output'/'summary.csv').is_file()
    for item in manifest['items']:
        assert item['status'] == 'warn'
        assert (tmp_path/'output'/item['report_html']).is_file()
    assert not list((tmp_path/'output').rglob('*.mp4'))


def test_batch_reports_errors_but_keeps_good_video(sample_video, tmp_path):
    source = tmp_path/'source'
    source.mkdir()
    shutil.copy2(sample_video, source/'good.mp4')
    (source/'bad.mp4').write_bytes(b'fakevideo'*100)
    manifest = audit_batch(source, tmp_path/'result', quick=True, fail_on='fail')
    assert manifest['summary'] == {'total': 2, 'passed': 1, 'blocked': 1, 'errors': 1}
    error = next(x for x in manifest['items'] if x['status'] == 'error')
    assert error['report_json'] is None
    assert error['error']


def test_batch_rejects_too_many_files_before_side_effects(sample_video, tmp_path):
    folder = tmp_path/'many'
    folder.mkdir()
    for n in range(3): shutil.copy2(sample_video,folder/f'{n}.mp4')
    with pytest.raises(AuditError, match='Batas batch'):
        audit_batch(folder,tmp_path/'should_not_exist',max_files=2,quick=True)
    assert not (tmp_path/'should_not_exist').exists()


def test_batch_skips_symlinks_and_no_recursive_by_default(sample_video, tmp_path):
    folder = tmp_path/'nested'
    folder.mkdir()
    sub = folder/'inner'
    sub.mkdir()
    shutil.copy2(sample_video, sub/'media.mp4')
    with pytest.raises(AuditError, match='tidak berisi'):
        discover_videos(folder)
    assert len(discover_videos(folder,recursive=True)) == 1
    (folder/'link.mp4').symlink_to(sub/'media.mp4')
    assert len(discover_videos(folder,recursive=True)) == 1


def test_batch_html_escaping_and_csv_formula_prevention(sample_video,tmp_path):
    folder = tmp_path/'input'
    folder.mkdir()
    hostile = '=HYPERLINK("http___invalid")&<x>.mp4'
    shutil.copy2(sample_video, folder/hostile)
    manifest = audit_batch(folder,tmp_path/'output',quick=True)
    csvtext = (tmp_path/'output'/'summary.csv').read_text()
    assert "'=HYPERLINK" in csvtext
    h = (tmp_path/'output'/'index.html').read_text()
    assert '&lt;x&gt;' in h
    assert '<x>' not in h
    assert manifest['items'][0]['report_html'].startswith('reports/')


def test_compare_same_video_has_no_regression(sample_video):
    b = audit_video(sample_video, quick=True)
    after = audit_video(sample_video, quick=True)
    delta = compare_reports(b,after)
    assert delta['same_bytes']
    assert delta['changed_checks'] == []
    assert delta['regression_count'] == 0
    assert delta['metrics']['width']['delta'] == 0


def test_compare_detects_decline_and_improvement(sample_video):
    b = audit_video(sample_video, quick=True)
    later = json.loads(json.dumps(b))
    old = next(c for c in later['checks'] if c['code']=='codec')
    old['level'] = 'warn'
    old['observation'] = 'unrecognized'
    delta = compare_reports(b,later)
    assert delta['regression_count'] == 1
    delta2 = compare_reports(later,b)
    assert delta2['regression_count'] == 0
    assert delta2['changed_checks'][0]['after'] == 'pass'


def test_cli_gate_produces_parseable_result_and_exit_code(sample_video,capsys):
    exitcode = main(['gate',str(sample_video),'--quick','--fail-on','warn'])
    captured = capsys.readouterr().out
    obj = json.loads(captured)
    assert exitcode == 3
    assert obj['schema']=='aiwallet.release-gate/v1'
    assert obj['passed'] is False


def test_cli_batch_fail_vs_pass(sample_video,tmp_path,capsys):
    src=tmp_path/'input';src.mkdir();shutil.copy2(sample_video,src/'video.mp4')
    ret = main(['batch',str(src),'--output',str(tmp_path/'out'),'--quick','--fail-on','fail'])
    assert ret == 0
    obj = json.loads(capsys.readouterr().out)
    assert obj['summary']['passed']==1


def test_cli_compare_exit_zero_for_identical_file(sample_video,capsys):
    ret = main(['compare',str(sample_video),str(sample_video),'--quick'])
    assert ret == 0
    obj = json.loads(capsys.readouterr().out)
    assert obj['regression_count'] == 0


def test_formula_cell_guards_multiple_prefixes():
    for s in ['=1+2','+1','-3','@SUM(A1)','   =1+2']:
        assert _safe_csv_cell(s).startswith("'")
    assert _safe_csv_cell('clip.mp4')=='clip.mp4'
