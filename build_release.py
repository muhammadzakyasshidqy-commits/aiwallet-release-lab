"""Deterministic local artifacts; no networks and no signing claims."""
from __future__ import annotations
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
root = Path(__file__).resolve().parent
out = root / 'dist'
site = root / 'site'
site_rel = site/'releases'
site_rel.mkdir(exist_ok=True)
source_zip = out/'aiwallet-release-lab-v0.3.0.zip'
excludes={'dist','.pytest_cache','__pycache__','.git','*.egg-info','.mypy_cache','.venv','build'}
paths=[]
for p in root.rglob('*'):
    if not p.is_file():continue
    parts=p.relative_to(root).parts
    if any(x in excludes or x.endswith('.egg-info') for x in parts):continue
    if parts[0] in ('site','tests','src','docs','policies','cloud','examples','.github','.agents') or len(parts)==1 and parts[0] in (
        'README.md','CHANGELOG.md','CODE_OF_CONDUCT.md','CONTRIBUTING.md','Dockerfile','LICENSE','PRIVACY.md',
        'SECURITY.md','pyproject.toml','compose.yaml','.gitignore','.env.example','action.yml','build_release.py'):
        if 'site/releases' in p.as_posix():continue
        paths.append(p)
with zipfile.ZipFile(source_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(paths):
        arc=Path('aiwallet-release-lab')/p.relative_to(root)
        info=zipfile.ZipInfo(arc.as_posix(),(2026,11,10,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o644<<16)
        z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
for fname in ('aiwallet-release-lab-v0.3.0.zip','releaselab-0.3.0.pyz','aiwallet_release_lab-0.3.0-py3-none-any.whl'):
    shutil.copyfile(out/fname,site_rel/fname)
artifacts=[]
for p in sorted(site_rel.glob('*')):
    if p.name == 'manifest.json':continue
    artifacts.append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={
 'schema':'aiwallet.release-evidence/v1',
 'product':'AIWallet Release Lab',
 'version':'0.3.0',
 'publish_date':'2026-11-10',
 'code_license':'Apache-2.0',
 'verified_local_tests':45,
 'test_environment':'Python 3.13 / Linux, FFmpeg CLI available',
 'github_actions_verification':'NOT_VERIFIED',
 'github_source_repo_verification':'NOT_PUBLISHED',
 'subscription_payment_status':'NOT_ENABLED',
 'cloud_storage_of_user_video':False,
 'artifacts':artifacts
}
(site_rel/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
with zipfile.ZipFile(out/'AIWallet_ReleaseLab_Site_v0.3.0.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(site.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(site))
with zipfile.ZipFile(out/'AIWallet_ReleaseLab_OpenCore_v0.3.0.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in (source_zip,out/'releaselab-0.3.0.pyz',out/'aiwallet_release_lab-0.3.0-py3-none-any.whl',out/'AIWallet_ReleaseLab_Site_v0.3.0.zip'):
        z.write(p,p.name)
for p in sorted(out.glob('*.zip')):print(p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
