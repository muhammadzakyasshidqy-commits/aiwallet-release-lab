"""Build portable release artifacts offline after wheel + zipapp have been built.

This script never publishes or charges. Public URL, source repository and CI
checks are verified separately, not inferred from creation of a ZIP file.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import re
import tomllib
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
version = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf8'))['project']['version']
release_date = (2026, 11, 10, 0, 0, 0)
test_proof = root / 'dist' / 'test-results.txt'
if not test_proof.is_file():
    raise SystemExit('Run pytest and save its stdout to dist/test-results.txt before building')
proof_match = re.search(r'(\d+) passed(?:,| in)', test_proof.read_text(encoding='utf8'))
if not proof_match:
    raise SystemExit('No passing test count in dist/test-results.txt')
tests_passed = int(proof_match.group(1))
out = root / 'dist'
site = root / 'site'
site_rel = site / 'releases'
site_rel.mkdir(parents=True, exist_ok=True)
source_zip = out / f'aiwallet-release-lab-v{version}.zip'
wheel = out / f'aiwallet_release_lab-{version}-py3-none-any.whl'
zipapp = out / f'releaselab-{version}.pyz'
bundle = out / f'AIWallet_ReleaseLab_v{version}.git.bundle'
for artifact in (wheel, zipapp, bundle):
    if not artifact.is_file():
        raise SystemExit(f'Missing prebuilt artifact: {artifact.name}')
for file in site_rel.iterdir():
    if file.is_file():
        file.unlink()
allowed_dirs = {'site','tests','src','docs','policies','cloud','examples','.github','.agents'}
allowed_files = {
    'README.md','CHANGELOG.md','CODE_OF_CONDUCT.md','CONTRIBUTING.md','Dockerfile',
    'LICENSE','PRIVACY.md','SECURITY.md','pyproject.toml','compose.yaml',
    '.gitignore','.env.example','action.yml','build_release.py'
}
excluded_dirs = {'dist','build','.pytest_cache','__pycache__','.git','.venv','.mypy_cache'}
files=[]
for path in root.rglob('*'):
    if not path.is_file():continue
    parts=path.relative_to(root).parts
    if any(x in excluded_dirs or x.endswith('.egg-info') for x in parts):continue
    if len(parts)>2 and parts[0]=='site' and parts[1]=='releases':continue
    if parts[0] in allowed_dirs or len(parts)==1 and parts[0] in allowed_files:
        files.append(path)
with zipfile.ZipFile(source_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for path in sorted(files):
        name=(Path('aiwallet-release-lab')/path.relative_to(root)).as_posix()
        info=zipfile.ZipInfo(name,release_date)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o644 << 16)
        z.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
for path in (source_zip,zipapp,wheel,bundle):
    shutil.copyfile(path,site_rel/path.name)
artifacts=[]
for path in sorted(site_rel.iterdir()):
    if not path.is_file():continue
    artifacts.append({'name':path.name,'bytes':path.stat().st_size,
                      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
manifest={
    'schema':'aiwallet.release-evidence/v1',
    'product':'AIWallet Release Lab',
    'version':version,
    'publish_date':'2026-11-10',
    'code_license':'Apache-2.0',
    'verified_local_tests':tests_passed,
    'test_evidence_sha256':hashlib.sha256(test_proof.read_bytes()).hexdigest(),
    'test_environment':'Python 3.13 / Linux, FFmpeg (local runtime)',
    'github_actions_verification':'NOT_VERIFIED',
    'github_source_repo_verification':'NOT_PUBLISHED',
    'subscription_payment_status':'NOT_ENABLED',
    'hosted_processing_status':'NOT_ENABLED',
    'cloud_storage_of_user_video':False,
    'artifacts':artifacts,
}
(site_rel/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(site_rel/'SHA256SUMS.txt').write_text(''.join(f"{row['sha256']}  {row['name']}\n" for row in artifacts),encoding='utf8')
site_zip = out / f'AIWallet_ReleaseLab_Site_v{version}.zip'
with zipfile.ZipFile(site_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for path in sorted(site.rglob('*')):
        if path.is_file():
            name=path.relative_to(site).as_posix()
            info=zipfile.ZipInfo(name,release_date)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o644 << 16)
            z.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
all_zip = out / f'AIWallet_ReleaseLab_OpenCore_v{version}.zip'
with zipfile.ZipFile(all_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in (source_zip,zipapp,wheel,bundle,site_zip):
        info=zipfile.ZipInfo(p.name,release_date)
        info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o644 << 16)
        z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
for p in (source_zip,zipapp,wheel,bundle,site_zip,all_zip):
    print(p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
