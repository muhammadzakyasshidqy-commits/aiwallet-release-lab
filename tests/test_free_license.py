"""Regression guard: no paid subscription or waitlist is shipped."""
from pathlib import Path

ROOT=Path(__file__).parents[1]


def test_no_paid_plan_in_public_marketing():
    html=(ROOT/'site/index.html').read_text(encoding='utf8')
    assert 'id="free"' in html
    assert 'Rp0' in html
    assert 'Apache-2.0' in html
    for disallowed in ('Creator Cloud','Studio Workspace','149rb','499rb','/ bulan','waitlist-dialog','waitlist-open','Minta akses awal'):
        assert disallowed not in html, disallowed

def test_local_dashboard_has_no_subscription_cta():
    html=(ROOT/'src/aiwallet_release_lab/static/index.html').read_text(encoding='utf8')
    for term in ('waitlist-form','waitlist-open','Creator Cloud','Studio Workspace','149rb','499rb'):
        assert term not in html, term
    assert 'id="free"' in html

def test_no_waitlist_api_or_telemetry_in_frontend_js():
    for fn in ('site/app.js','src/aiwallet_release_lab/static/app.js'):
        js=(ROOT/fn).read_text(encoding='utf8')
        assert 'aiwallet-release-interest' not in js
        assert 'waitlist' not in js.lower()
        assert 'stripe' not in js.lower()
        assert 'midtrans' not in js.lower()

def test_one_time_help_does_not_restrict_open_core():
    s=(ROOT/'docs/BUSINESS.md').read_text(encoding='utf8')
    assert 'one-time' in s.lower()
    assert 'Apache-2.0' in s
    assert 'No license key' in s
    assert (ROOT/'LICENSE').is_file()

def test_retiral_docs_not_billing_schema():
    for fn in ('docs/BILLING_READINESS.md','docs/SUBSCRIPTION_CONTRACT.md'):
        s=(ROOT/fn).read_text(encoding='utf8').lower()
        assert 'retired' in s
        assert 'not active' in s or 'no recurring' in s
