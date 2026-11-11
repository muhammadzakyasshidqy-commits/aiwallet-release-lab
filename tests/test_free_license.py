"""Core remains free while managed hosting can be offered separately."""
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_community_core_is_always_free_and_licensed():
    s=(ROOT/'site/index.html').read_text(encoding='utf8')
    assert 'id="free"' in s and 'Rp0' in s and 'APACHE-2.0' in s.upper()
    assert 'SELF-HOST FREE' in s
    assert (ROOT/'LICENSE').is_file()
    assert 'Apache-2.0' in (ROOT/'docs/BUSINESS.md').read_text()


def test_optional_managed_plans_disclosed_as_not_yet_active():
    s=(ROOT/'site/index.html').read_text(encoding='utf8')
    for val in ('id="managed"','creator_cloud','studio_workspace','Rp149.000','Rp499.000',
                'Belum ada checkout','name="consent"','id="managed-interest-form"'):
        assert val in s,val
    assert 'NO SUBSCRIPTIONS' not in s


def test_local_dashboard_does_not_require_subscription_or_track_users():
    h=(ROOT/'src/aiwallet_release_lab/static/index.html').read_text(encoding='utf8')
    js=(ROOT/'src/aiwallet_release_lab/static/app.js').read_text(encoding='utf8')
    for term in ('waitlist-form','waitlist-open','creator_cloud','studio_workspace','aiwallet-release-interest','midtrans'):
        assert term not in h.lower() and term not in js.lower(),term
    assert 'id="free"' in h


def test_marketing_client_has_no_payment_provider_or_secret():
    s=(ROOT/'site/app.js').read_text(encoding='utf8').lower()
    assert 'aiwallet-release-interest' in s
    assert 'consent' in s
    for secret in ('service_role','server_key','authorization: bearer','payment_token','create-subscription'):
        assert secret not in s


def test_cloud_interest_is_idempotent_and_nonbillable():
    s=(ROOT/'cloud/interest/index.ts').read_text(encoding='utf8')
    assert 'resolution=ignore-duplicates' in s
    for phrase in ('billing_live:false','managed_cloud_available:false','owner_paid_subscription_required:false',
                   'charged:false','v.consent!==true','new Set(["creator_cloud","studio_workspace"])'):
        assert phrase in s
    assert '/v1/subscriptions' not in s


def test_one_time_help_does_not_limit_core():
    s=(ROOT/'docs/BUSINESS.md').read_text(encoding='utf8')
    assert 'Apache-2.0' in s and 'one-time' in s.lower()
    assert 'without an AIWallet subscription' in s


def test_billing_design_explicitly_not_active():
    for fn in ('docs/BILLING_READINESS.md','docs/SUBSCRIPTION_CONTRACT.md'):
        s=(ROOT/fn).read_text(encoding='utf8').lower()
        assert 'not active' in s and 'consent' in s


def test_package_version_matches_runtime_version():
    import tomllib
    meta=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf8'))
    version=meta['project']['version']
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    import aiwallet_release_lab
    assert aiwallet_release_lab.__version__==version


def test_github_publisher_restricts_target_and_forbids_force_push():
    p=(ROOT/'scripts/Publish-GitHub.ps1').read_text(encoding='utf8')
    assert "muhammadzakyasshidqy-commits" in p and "aiwallet-release-lab" in p
    assert '--web' in p and 'github.com' in p
    assert '98d0cfa794721665d7973dd728c78aff7bd836d58f10f6d7a03568eccb0a22e0' in p
    assert 'git --force' not in p and 'push --force' not in p
    assert 'PUBLISH_RESULT.json' in p and 'GitHub CLI' in p
