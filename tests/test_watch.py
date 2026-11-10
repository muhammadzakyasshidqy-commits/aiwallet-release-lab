"""Watch-mode regression tests; all use local, owned files and no network."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from aiwallet_release_lab.cli import main
from aiwallet_release_lab.core import AuditError
from aiwallet_release_lab.watch import WatchSession


def test_empty_watch_is_safe_and_reports_zero(tmp_path):
    src=tmp_path/'src';src.mkdir()
    watch=WatchSession(src,tmp_path/'out',stable_seconds=0)
    result=watch.poll(now=0)
    assert result['summary']=={'discovered':0,'stable_results':0,'passed':0,'blocked':0,'pending_or_unstable':0,'unstable_now':0}
    assert (tmp_path/'out/index.html').exists()
    assert main(['watch',str(src),'-o',str(tmp_path/'other'),'--once'])==3


def test_stable_file_then_skip_and_resume(sample_video,tmp_path):
    folder=tmp_path/'incoming';folder.mkdir()
    shutil.copyfile(sample_video,folder/'clip.mp4')
    out=tmp_path/'receipts'
    watch=WatchSession(folder,out,quick=True,fail_on='fail',stable_seconds=3)
    first=watch.poll(now=2)
    assert first['new_results']==[]
    assert first['summary']['pending_or_unstable']==1
    second=watch.poll(now=5)
    assert len(second['new_results'])==1
    assert second['summary']['passed']==1
    assert second['summary']['blocked']==0
    assert (out/'state.json').exists()
    assert (out/'index.html').is_file()
    assert (out/'summary.csv').is_file()
    assert watch.poll(now=6)['new_results']==[]
    restarted=WatchSession(folder,out,quick=True,fail_on='fail',stable_seconds=3)
    assert restarted.poll(now=7)['new_results']==[]
    state=json.loads((out/'state.json').read_text())
    assert 'clip.mp4' in state['records']
    assert state['records']['clip.mp4']['report_json'] is not None


def test_changed_export_invalidates_previous_gate_immediately(sample_video,black_video,tmp_path):
    src=tmp_path/'clips';src.mkdir()
    target=src/'new.mp4';shutil.copyfile(sample_video,target)
    watch=WatchSession(src,tmp_path/'receipts',quick=True,fail_on='fail',stable_seconds=3)
    watch.poll(now=0)
    assert watch.poll(now=3)['summary']['passed']==1
    # Replace an existing export with a different valid video.
    shutil.copyfile(black_video,target)
    mid=watch.poll(now=4)
    assert mid['new_results']==[]
    assert mid['summary']['passed']==0
    assert mid['summary']['pending_or_unstable']==1
    assert watch.poll(now=7)['summary']['passed']==1


def test_failed_video_blocks_and_keeps_source(tmp_path):
    src=tmp_path/'clips';src.mkdir()
    f=src/'bad.mp4';f.write_bytes(b'garbage'*150)
    watch=WatchSession(src,tmp_path/'receipts',stable_seconds=0)
    first=watch.poll(now=3)
    assert first['summary']['blocked']==1
    assert first['new_results'][0]['status']=='error'
    assert f.exists()
    assert watch.poll(now=4)['new_results']==[]
    assert 'bad.mp4' in (tmp_path/'receipts/index.html').read_text()


def test_changed_during_scan_never_gets_old_receipt(sample_video,tmp_path,monkeypatch):
    src=tmp_path/'src';src.mkdir();f=src/'movie.mp4'
    shutil.copyfile(sample_video,f)
    watch=WatchSession(src,tmp_path/'out',quick=True,fail_on='fail',stable_seconds=0)
    from aiwallet_release_lab import watch as module
    original=module.audit_video
    calls=[]
    def change_after_scan(path, **kwargs):
        receipt=original(path, **kwargs)
        if not calls:
            Path(path).write_bytes(Path(path).read_bytes()+b'\0')
        calls.append(1)
        return receipt
    monkeypatch.setattr(module,'audit_video',change_after_scan)
    first=watch.poll(now=0)
    assert first['new_results']==[]
    assert first['summary']['pending_or_unstable']==1
    assert not (tmp_path/'out/reports').exists()
    later=watch.poll(now=2)
    assert len(later['new_results'])==1
    assert later['summary']['passed']==1


def test_policy_change_invalidates_prior_record(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();shutil.copyfile(sample_video,src/'v.mp4')
    output=tmp_path/'out'
    first=WatchSession(src,output,quick=True,fail_on='fail',stable_seconds=0)
    assert first.poll()['summary']['passed']==1
    revised=WatchSession(src,output,quick=True,fail_on='warn',stable_seconds=0)
    r=revised.poll()
    assert r['summary']['blocked']==1
    assert len(r['new_results'])==1


def test_formula_filename_is_safe_csv_and_html(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();shutil.copyfile(sample_video,src/'=SUM(A1).mp4')
    out=tmp_path/'out'
    sess=WatchSession(src,out,quick=True,fail_on='fail',stable_seconds=0)
    sess.poll()
    assert "'=SUM(A1).mp4" in (out/'summary.csv').read_text()
    assert '=SUM(A1).mp4' in (out/'index.html').read_text()


def test_symlinked_media_and_nested_directory_are_skipped(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();out=tmp_path/'out'
    src.joinpath('evil.mp4').symlink_to(sample_video)
    outside=tmp_path/'outside';outside.mkdir();shutil.copyfile(sample_video,outside/'video.mp4')
    (src/'alias').symlink_to(outside,target_is_directory=True)
    session=WatchSession(src,out,recursive=True,quick=True,stable_seconds=0)
    assert session.poll()['summary']['discovered']==0


def test_disallow_output_in_source_and_reject_invalid_limits(tmp_path):
    src=tmp_path/'src';src.mkdir()
    with pytest.raises(AuditError):WatchSession(src,src/'output')
    with pytest.raises(AuditError):WatchSession(src,tmp_path/'out',max_files=201)
    with pytest.raises(AuditError):WatchSession(src,tmp_path/'out',stable_seconds=float('nan'))
    with pytest.raises(AuditError):WatchSession(src,tmp_path/'out',stable_seconds=-1)


def test_overflow_fails_closed(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir()
    for i in range(3):shutil.copyfile(sample_video,src/f'v{i}.mp4')
    session=WatchSession(src,tmp_path/'out',quick=True,max_files=2)
    with pytest.raises(AuditError,match='lebih dari'):session.poll()


def test_cli_watch_once_writes_file_and_gate_exit(sample_video,tmp_path,capsys):
    src=tmp_path/'src';src.mkdir();shutil.copyfile(sample_video,src/'v.mp4')
    out=tmp_path/'out'
    code=main(['watch',str(src),'-o',str(out),'--once','--quick','--fail-on','fail'])
    result=json.loads(capsys.readouterr().out.splitlines()[-1])
    assert code==0
    assert result['summary']['passed']==1
    assert result['new_results'][0]['file']=='v.mp4'


def test_corrupted_or_mismatched_state_rejected(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();shutil.copyfile(sample_video,src/'v.mp4')
    out=tmp_path/'out';out.mkdir()
    (out/'state.json').write_text('{oops')
    with pytest.raises(AuditError,match='tidak valid'):WatchSession(src,out)
    (out/'state.json').write_text(json.dumps({'schema':'aiwallet.release-watch/v1','source':'/wrong','records':{}}))
    with pytest.raises(AuditError):WatchSession(src,out)


def test_removed_file_is_pruned_from_current_manifest(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();target=src/'v.mp4';shutil.copyfile(sample_video,target)
    session=WatchSession(src,tmp_path/'out',quick=True,fail_on='fail',stable_seconds=0)
    assert session.poll()['summary']['passed']==1
    target.unlink()
    assert session.poll()['summary']['stable_results']==0
    assert json.loads((tmp_path/'out/state.json').read_text())['records']=={}


def test_separate_process_autowatch_real_export(sample_video,black_video,tmp_path):
    """Real watcher runs continuously; new and revised exports are detected."""
    import subprocess
    import sys
    import time

    folder=tmp_path/'incoming';folder.mkdir()
    out=tmp_path/'qc'
    env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
    proc=subprocess.Popen([sys.executable,'-m','aiwallet_release_lab','watch',str(folder),
                           '-o',str(out),'--quick','--fail-on','fail',
                           '--stable-seconds','0.25','--poll-interval','0.2'],
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    target=folder/'fresh.mp4'
    try:
        time.sleep(.5)
        shutil.copyfile(sample_video,target)
        first=None
        for _ in range(40):
            time.sleep(.2)
            if (out/'state.json').exists():
                content=json.loads((out/'state.json').read_text())
                record=content.get('records',{}).get('fresh.mp4')
                if record and record.get('gate_passed') is True:
                    first=record['sha256'];break
        assert first is not None,'Watcher never processed new export'
        shutil.copyfile(black_video,target)
        changed=None
        for _ in range(40):
            time.sleep(.2)
            content=json.loads((out/'state.json').read_text())
            record=content.get('records',{}).get('fresh.mp4')
            if record and record.get('sha256') and record['sha256']!=first:
                changed=record['sha256'];break
        assert changed is not None,'Watcher did not re-inspect revised export'
    finally:
        proc.terminate()
        try:proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill();proc.communicate(timeout=5)
    assert proc.returncode is not None


def test_idle_cycles_do_not_rewrite_reports(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();shutil.copyfile(sample_video,src/'v.mp4')
    out=tmp_path/'out'
    watch=WatchSession(src,out,quick=True,fail_on='fail',stable_seconds=0)
    assert watch.poll(now=0)['summary']['passed']==1
    files=[out/'state.json',out/'summary.csv',out/'index.html']
    old=[x.stat().st_mtime_ns for x in files]
    for now in range(1,12):assert watch.poll(now=float(now))['new_results']==[]
    assert old==[x.stat().st_mtime_ns for x in files]


def test_exclusive_lock_rejects_concurrent_writer(tmp_path):
    from aiwallet_release_lab.watch import exclusive_watch_lock
    with exclusive_watch_lock(tmp_path):
        with pytest.raises(AuditError,match='Sudah ada'):
            with exclusive_watch_lock(tmp_path):
                pass
    # OS lock is automatically released; a later watcher can proceed.
    with exclusive_watch_lock(tmp_path):
        assert (tmp_path/'.watch.lock').is_file()


def test_tampered_state_reference_is_rejected(sample_video,tmp_path):
    src=tmp_path/'src';src.mkdir();shutil.copyfile(sample_video,src/'v.mp4')
    out=tmp_path/'out'
    sess=WatchSession(src,out,quick=True,fail_on='fail',stable_seconds=0)
    sess.poll()
    state=json.loads((out/'state.json').read_text())
    state['records']['v.mp4']['report_json']='../../etc/passwd'
    (out/'state.json').write_text(json.dumps(state))
    with pytest.raises(AuditError, match='tidak valid'):
        WatchSession(src,out,quick=True,fail_on='fail')
