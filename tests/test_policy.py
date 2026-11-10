"""Regression coverage for studio policy, unmeasured scans and loopback security."""
import copy
import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aiwallet_release_lab.cli import main
from aiwallet_release_lab.core import AuditError, audit_video
from aiwallet_release_lab.policy import evaluate_policy, read_policy, validate_policy
from aiwallet_release_lab.web import create_app
from aiwallet_release_lab.workflow import audit_batch, compare_reports, gate_report

BASE = {"schema":"aiwallet.release-policy/v1","name":"Team 9:16","min_width":720,
        "min_height":1280,"require_full_scan":True,"require_audio":True,
        "max_black_segment_seconds":1.0,"allowed_codecs":["h264"]}


def test_policy_validation_rejects_typos_and_bad_values(tmp_path):
    for field,value in [("widht",720),("max_black_segment_seconds",float('nan')),
                        ("require_audio","yes"),("allowed_codecs",[]),
                        ("min_width",True),("min_width",0)]:
        with pytest.raises(AuditError):
            validate_policy({**BASE,field:value})
    with pytest.raises(AuditError):
        validate_policy({**BASE,"min_fps":60,"max_fps":24})
    with pytest.raises(AuditError):
        validate_policy({**BASE,"schema":"wrong"})
    p=tmp_path/'policy.json'
    p.write_text(json.dumps(BASE))
    assert read_policy(p)==BASE
    p2=tmp_path/'link.json'
    p2.symlink_to(p)
    with pytest.raises(AuditError,match='symlink'):
        read_policy(p2)


def test_quick_scan_is_explicitly_warned(sample_video):
    report=audit_video(sample_video,quick=True)
    assert report['measurements']['limited_scan'] is True
    assert any(c['code']=='scan_scope' and c['level']=='warn' for c in report['checks'])


def test_policy_fail_closed_if_quick_or_missing_measurement(sample_video):
    report=audit_video(sample_video,quick=True)
    findings=evaluate_policy(report,BASE)
    assert {'min_width','min_height','require_full_scan','max_black_segment_seconds'} <= {f['code'] for f in findings}
    strict=gate_report(report,policy=BASE,fail_on='none')
    assert strict['passed'] is False
    assert 'policy:require_full_scan' in strict['blocking_check_codes']
    assert strict['policy_name']=='Team 9:16'


def test_policy_with_full_scan_without_resolution_violation(sample_video):
    p={'schema':BASE['schema'],'name':'Sane checks','require_full_scan':True,
       'min_width':320,'min_height':640,'allowed_codecs':['h264']}
    report=audit_video(sample_video,quick=False)
    assert evaluate_policy(report,p)==[]
    assert gate_report(report,policy=p,fail_on='none')['passed'] is True


def test_missing_check_regression_even_if_before_pass(sample_video):
    a=audit_video(sample_video,quick=False)
    b=copy.deepcopy(a)
    b['checks']=[c for c in b['checks'] if c['code']!='black_segments']
    result=compare_reports(a,b)
    assert result['regression_count']==1
    assert next(c for c in result['changed_checks'] if c['code']=='black_segments')['regression'] is True


def test_silence_detector_real_ffmpeg(tmp_path):
    p=tmp_path/'silence.mp4'
    cmd=['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=360x640:r=24:d=3',
         '-f','lavfi','-i','anullsrc=channel_layout=mono:sample_rate=48000',
         '-t','3','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-y',str(p)]
    subprocess.run(cmd,check=True,timeout=25)
    report=audit_video(p)
    silences=report['measurements']['silence_segments']
    assert silences and silences[0]['start']<=0.2
    assert silences[0]['seconds']>=2.5
    p2={'schema':BASE['schema'],'name':'Silence gate','max_silence_segment_seconds':1.5}
    assert any(f['code']=='max_silence_segment_seconds' for f in evaluate_policy(report,p2))


def test_cli_policy_gate_and_batch_work(sample_video,tmp_path,capsys):
    policy=tmp_path/'strict.json';policy.write_text(json.dumps(BASE))
    result=main(['gate',str(sample_video),'--quick','--policy',str(policy),'--fail-on','none'])
    obj=json.loads(capsys.readouterr().out)
    assert result==3 and obj['policy_name']=='Team 9:16'
    out=tmp_path/'batch'
    batch=audit_batch(sample_video.parent,out,quick=True,policy=BASE,max_files=20,fail_on='none')
    assert batch['summary']['blocked']>=1
    assert batch['policy_name']=='Team 9:16'


def test_loopback_host_gate_disallows_dns_rebinding(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        good=client.get('/api/health',headers={'Host':'localhost:7860'})
        assert good.status_code==200
        hostile=client.get('/api/reports',headers={'Host':'attacker.example:7860'})
        assert hostile.status_code==400
        blocked=client.post('/api/audits',headers={'Host':'attacker.example','Origin':'http://attacker.example'},
                            files={'file':('x.mp4',b'bad','video/mp4')})
        assert blocked.status_code in (400,403)


def test_scan_failure_never_meets_full_scan_policy(sample_video):
    import copy
    report=audit_video(sample_video,quick=False)
    damaged=copy.deepcopy(report)
    damaged['measurements']['scan_errors']=['black_segments']
    damaged['measurements']['black_segments']=None
    check=evaluate_policy(damaged,{
        'schema':BASE['schema'],'name':'full scan required',
        'require_full_scan':True,'max_black_segment_seconds':0.5})
    assert {'require_full_scan','max_black_segment_seconds'} <= {x['code'] for x in check}


def test_html_timeline_is_escaped(sample_video):
    from aiwallet_release_lab.report import render_html
    report=audit_video(sample_video,quick=True)
    report['measurements']['black_segments']=[{'start':0.25,'end':0.75,'seconds':0.5}]
    page=render_html(report)
    assert 'Timecode yang perlu ditinjau' in page
    assert '0.25 s' in page
    assert '<td>0.75</td>' in page


def test_strict_policy_does_not_blindly_pass_when_audio_scan_missing(sample_video):
    import copy
    report=audit_video(sample_video,quick=False)
    broken=copy.deepcopy(report)
    broken['measurements']['integrated_lufs']=None
    p={'schema':BASE['schema'],'name':'audio sample','min_lufs':-25,
       'max_lufs':-8,'require_full_scan':True}
    assert any(f['code']=='min_lufs' for f in evaluate_policy(broken,p))
