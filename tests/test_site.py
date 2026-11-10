from html.parser import HTMLParser
from pathlib import Path


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = set()
        self.duplicates = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            if data['id'] in self.ids:
                self.duplicates.add(data['id'])
            self.ids.add(data['id'])
        if tag == 'a' and data.get('href', '').startswith('#') and len(data['href']) > 1:
            self.references.add(data['href'][1:])


def test_both_frontends_have_valid_internal_links():
    root = Path(__file__).parents[1]
    for path in [root/'site'/'index.html', root/'src'/'aiwallet_release_lab'/'static'/'index.html']:
        parser = Structure()
        parser.feed(path.read_text('utf-8'))
        assert not parser.duplicates
        assert not (parser.references - parser.ids)
        assert 'waitlist-dialog' in parser.ids
        assert 'waitlist-form' in parser.ids


def test_static_website_does_not_claim_paid_product_is_running():
    src = (Path(__file__).parents[1]/'site'/'index.html').read_text('utf-8')
    assert 'belum ada tagihan otomatis' in src.lower()
    assert 'Bukan skor viralitas AI' in src
    assert 'synthetic-black-example.mp4' in src
    assert 'Apache-2.0' in src


def test_no_payment_credentials_or_tracking_scripts_in_static_site():
    root=Path(__file__).parents[1]/'site'
    html=(root/'index.html').read_text('utf-8')
    js=(root/'app.js').read_text('utf-8')
    assert '<script defer src="./app.js"></script>' in html
    assert 'stripe.com' not in js and 'midtrans' not in js
    assert 'google-analytics' not in js and 'analytics.js' not in js
    assert "data.consent" in js
