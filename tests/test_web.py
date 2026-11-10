from fastapi.testclient import TestClient

from aiwallet_release_lab.web import create_app


def test_health_and_static_ui(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        res = c.get('/api/health')
        assert res.status_code == 200
        assert res.json()['publishes_media'] is False
        html = c.get('/')
        assert html.status_code == 200
        assert 'text/html' in html.headers['content-type']
        assert 'Workbench' in html.text
        assert c.get('/static/style.css').status_code == 200
        assert c.get('/static/app.js').status_code == 200


def test_upload_audit_read_history_and_delete(sample_video, tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        with sample_video.open('rb') as file:
            res = c.post('/api/audits',files={'file': ('my_real.mp4',file,'video/mp4')})
        assert res.status_code == 201, res.text
        data = res.json()
        assert data['report']['file']['name'] == 'my_real.mp4'
        id_ = data['id']
        assert len(id_) == 32
        assert c.get('/api/reports').json()['reports'][0]['id'] == id_
        assert c.get('/api/reports/'+id_).status_code == 200
        html = c.get('/api/reports/'+id_+'/html')
        assert html.status_code == 200
        assert 'attachment' in html.headers['content-disposition']
        assert '<!doctype html>' in html.text
        poster = c.get('/api/reports/'+id_+'/poster')
        assert poster.status_code == 200
        assert poster.content.startswith(b'\xff\xd8')
        assert not list(tmp_path.glob('aiwallet_qc_*'))
        assert c.delete('/api/reports/'+id_).json()=={'deleted':True}
        assert c.get('/api/reports/'+id_).status_code == 404
        assert c.get('/api/reports/'+id_+'/poster').status_code == 404


def test_invalid_file_is_rejected_and_deleted(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        x = c.post('/api/audits', files={'file':('fake.mp4',b'no video'*200,'video/mp4')})
        assert x.status_code == 422
        assert not list(tmp_path.glob('aiwallet_qc_*'))
        assert c.get('/api/reports').json()['reports']==[]


def test_reject_disallowed_extension_and_mime(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.post('/api/audits',files={'file':('a.txt',b'bad data','text/plain')}).status_code==415
        assert c.post('/api/audits',files={'file':('a.mp4',b'bad data','text/plain')}).status_code==415


def test_enforce_upload_size_and_sanitize_filename(sample_video,tmp_path):
    with TestClient(create_app(tmp_path,max_bytes=1500)) as c:
        with sample_video.open('rb') as fh:
            assert c.post('/api/audits',files={'file':('foo.mp4',fh,'video/mp4')}).status_code==413
        assert not list(tmp_path.glob('aiwallet_qc_*'))


def test_path_traversal_cannot_read_local_files(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        assert c.get('/api/reports/../secret').status_code in (404,307)
        assert c.get('/api/reports/x'*2).status_code==404
        assert c.get('/api/reports/12345678901234567890123456789012/poster').status_code==404


def test_security_headers_and_cross_origin_write_rejected(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        r = c.get('/')
        assert r.headers['x-content-type-options'] == 'nosniff'
        assert r.headers['x-frame-options'] == 'DENY'
        blocked = c.post('/api/audits', headers={'Origin':'https://malicious.example'}, files={'file':('x.mp4',b'test','video/mp4')})
        assert blocked.status_code == 403
        assert not list(tmp_path.glob('aiwallet_qc_*'))


def test_dashboard_csp_blocks_external_waitlist_connections(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        csp = c.get('/').headers['content-security-policy']
        assert "connect-src 'self';" in csp
        assert "jwdxpigxgasybqaovsma" not in csp
        assert "unsafe-inline" not in csp
