"""Editorial review cannot be fabricated from an FFmpeg PASS."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aiwallet_release_lab.core import AuditError, audit_video
from aiwallet_release_lab.cli import main
from aiwallet_release_lab.editorial import SCHEMA, CRITERIA, create_review, read_review, review_gate
from aiwallet_release_lab.web import create_app


@pytest.fixture
def report(sample_video):
    return audit_video(sample_video,quick=True)


def values(state='pass'):
    return {k:state for k in CRITERIA}


def test_missing_and_invalid_review_fails_closed(report):
    r=review_gate(report,None)
    assert not r['passed'] and 'review:missing' in r['blocking_check_codes']
    assert review_gate(report,{'schema':'fake'})['blocking_check_codes']==['review:invalid_schema']
    with pytest.raises(AuditError):
        create_review(report,reviewer='X',criteria=values())
    with pytest.raises(AuditError):
        create_review(report,reviewer='Editor',criteria={k:'pass' for k in CRITERIA[:-1]})
    with pytest.raises(AuditError):
        create_review(report,reviewer='Editor',criteria=values('not_applicable'))


def test_review_human_pass_does_not_certify_identity(report):
    review=create_review(report,reviewer='Editor Manusia',criteria=values(),notes='Sudah dicek langsung')
    assert review['schema']==SCHEMA
    assert review['outcome']=='approved'
    assert review['identity_verified'] is False
    assert review_gate(report,review)['passed']
    review['identity_verified']=True
    assert 'review:identity_claim_invalid' in review_gate(report,review)['blocking_check_codes']


def test_revision_request_and_tampering_fail_closed(report):
    checks=values();checks['pacing']='changes_requested'
    review=create_review(report,reviewer='Editor',criteria=checks,notes='<img src=x onerror=alert(1)>')
    assert review['outcome']=='changes_requested'
    assert not review_gate(report,review)['passed']
    review['outcome']='approved'
    assert 'review:outcome_inconsistent' in review_gate(report,review)['blocking_check_codes']
    review=create_review(report,reviewer='Editor',criteria=values())
    review['file_sha256']='a'*64
    assert 'review:source_changed' in review_gate(report,review)['blocking_check_codes']
    review=create_review(report,reviewer='Editor',criteria=values())
    review['ruleset']='old rules'
    assert 'review:ruleset_changed' in review_gate(report,review)['blocking_check_codes']


def test_cli_create_review_require_for_gate(sample_video,report,tmp_path,capsys):
    receipt=tmp_path/'audit.json';receipt.write_text(json.dumps(report),encoding='utf8')
    approved=tmp_path/'editorial.json'
    argv=['editorial',str(receipt),'--reviewer','Local editor','--output',str(approved)]
    for key in CRITERIA:
        argv.extend(['--'+key.replace('_','-'),'pass'])
    assert main(argv)==0
    capsys.readouterr()
    assert read_review(approved)['outcome']=='approved'
    assert main(['gate',str(sample_video),'--quick','--fail-on','none','--editorial-review',str(approved)])==0
    result=json.loads(capsys.readouterr().out)
    assert result['passed'] and result['editorial_gate']['passed']
    assert main(['gate',str(sample_video),'--quick','--fail-on','none','--editorial-review',str(tmp_path/'not_found.json')])==3
    result=json.loads(capsys.readouterr().out)
    assert 'review:missing_or_unreadable' in result['blocking_check_codes']
    approved.write_text('{broken',encoding='utf8')
    assert main(['gate',str(sample_video),'--quick','--fail-on','none','--editorial-review',str(approved)])==3
    capsys.readouterr()


def test_cli_review_request_exit_three(sample_video,report,tmp_path,capsys):
    receipt=tmp_path/'audit.json';receipt.write_text(json.dumps(report),encoding='utf8')
    note=tmp_path/'editorial.json'
    argv=['editorial',str(receipt),'--reviewer','Editorial editor','--notes','Audio perlu diseimbangkan','-o',str(note)]
    for key in CRITERIA:
        argv.extend(['--'+key.replace('_','-'),'changes_requested' if key=='sound_design' else 'pass'])
    assert main(argv)==3
    assert json.loads(capsys.readouterr().out)['status']=='changes_requested'
    assert not review_gate(report,read_review(note))['passed']


def test_local_api_persists_revisions_and_deletes(sample_video,tmp_path):
    base=tmp_path/'data'
    with TestClient(create_app(base)) as c:
        with sample_video.open('rb') as f:
            created=c.post('/api/audits',files={'file':('scene.mp4',f,'video/mp4')})
        assert created.status_code==201
        id_=created.json()['id']
        assert c.get('/api/reports/'+id_+'/review').json()=={'latest':None}
        criteria=values();criteria['story_hook']='changes_requested'
        data={'reviewer':'Editor','criteria':criteria,'notes':'Slow hook <script>alert(1)</script>'}
        wrong=c.post('/api/reports/'+id_+'/review',json=data,headers={'Origin':'https://malicious.example'})
        assert wrong.status_code==403
        first=c.post('/api/reports/'+id_+'/review',json=data)
        assert first.status_code==201,first.text
        assert first.json()['revision']==1
        assert first.json()['review']['outcome']=='changes_requested'
        criteria['story_hook']='pass'
        second=c.post('/api/reports/'+id_+'/review',json={**data,'criteria':criteria,'notes':'Checked visually'})
        assert second.status_code==201
        assert second.json()['revision']==2
        recent=c.get('/api/reports/'+id_+'/review').json()['latest']
        assert recent['revision']==2
        assert recent['review']['outcome']=='approved'
        exported=c.get('/api/reports/'+id_+'/review.json')
        assert exported.status_code==200
        assert exported.headers['content-disposition'].startswith('attachment')
        assert json.loads(exported.text)['identity_verified'] is False
        bad=c.post('/api/reports/'+id_+'/review',json={**data,'criteria':{'foo':'pass'}})
        assert bad.status_code==422
        assert c.delete('/api/reports/'+id_).json()=={'deleted':True}
        assert c.get('/api/reports/'+id_+'/review').status_code==404
        assert c.get('/api/reports/'+id_+'/review.json').status_code==404
    import sqlite3
    with sqlite3.connect(base/'reports.sqlite3') as db:
        assert db.execute('select count(*) from editorial_reviews').fetchone()[0]==0


def test_untrusted_client_cannot_inject_review(report):
    criterion=values();criterion['pacing']='not_applicable'
    review=create_review(report,reviewer='Author self-declared',criteria=criterion)
    assert review_gate(report,review)['passed']
    review['created_at']='not-a-timestamp'
    assert 'review:timestamp_invalid' in review_gate(report,review)['blocking_check_codes']
