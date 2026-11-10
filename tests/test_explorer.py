"""Zero-upload browser Report Explorer should remain functional and safe to distribute."""
from html.parser import HTMLParser
from pathlib import Path


class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=set();self.dupe=set();self.refs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids:self.dupe.add(a['id'])
            self.ids.add(a['id'])
        if tag in ('script','link') and (a.get('src') or a.get('href')):
            self.refs.append(a.get('src') or a.get('href'))


def test_receipt_explorer_is_self_contained_no_external_js():
    root=Path(__file__).parents[1]/'site'
    html=(root/'tools/receipt-explorer.html').read_text('utf8')
    parsed=TagChecker();parsed.feed(html)
    assert parsed.dupe==set()
    assert {'receipt-file','open-sample','download-csv','timeline-scale','markers','filename'}<=parsed.ids
    for ref in parsed.refs:
        assert not ref.startswith('https://')
        assert (root/'tools'/ref).exists()
    assert 'site' in str(root)


def test_explorer_uses_textcontent_and_local_file_api():
    root=Path(__file__).parents[1]/'site/tools'
    js=(root/'receipt-explorer.js').read_text('utf8')
    assert '.textContent=' in js
    assert '.innerHTML=' not in js
    assert 'file.text()' in js
    assert "fetch('../demo/audit.json'" in js
    assert "fetch('https://" not in js
    assert 'maxBytes=2*1024*1024' in js
    assert 'download-csv' in js


def test_marketing_site_links_to_explorer_and_source():
    root=Path(__file__).parents[1]/'site'
    source=(root/'index.html').read_text('utf8')
    assert 'tools/receipt-explorer.html' in source
    assert 'aiwallet-release-lab-v0.5.0.zip' in source
    assert '0.4.0' not in source
    assert (root/'demo/issue-markers.csv').exists()
