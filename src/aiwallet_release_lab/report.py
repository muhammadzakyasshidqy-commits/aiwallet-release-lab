"""A portable audit receipt. All interpolated content is HTML escaped."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path
from typing import Any


def render_html(result: dict[str, Any], poster: Path | None = None) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    file = result["file"]
    summary = result["summary"]
    chips = {"pass": "PASS", "warn": "CHECK", "fail": "BLOCK"}
    poster_html = ""
    if poster and poster.is_file():
        b64 = base64.b64encode(poster.read_bytes()).decode("ascii")
        poster_html = f'<img class="poster" alt="Cuplikan video" src="data:image/jpeg;base64,{b64}">'
    rows = "".join(
        f'<article class="check"><span class="flag flag-{esc(c["level"])}">{chips.get(c["level"], "CHECK")}</span>'
        f'<div><h3>{esc(c["title"])}</h3><p>{esc(c["observation"])}</p>'
        f'<small>{esc(c["advice"])}</small></div></article>'
        for c in result["checks"]
    )
    # Timecoded evidence helps reviewers jump to a problem in their editor.
    segment_rows = []
    for kind, label in (("black_segments", "Bingkai hitam"),
                        ("freeze_segments", "Gambar beku"),
                        ("silence_segments", "Audio hening")):
        for event in result.get("measurements", {}).get(kind, []) or []:
            start = event.get("start", 0)
            end = event.get("end")
            length = event.get("seconds")
            if length is None and end is not None:
                length = round(end - start, 3)
            segment_rows.append(f'<tr><th scope="row">{esc(label)}</th><td>{esc(start)} s</td>'
                                f'<td>{esc(end) if end is not None else "Sampai akhir sampel"}</td>'
                                f'<td>{esc(length) if length is not None else "—"} s</td></tr>')
    timeline_html = ("<section class=\"timeline\"><h2>Timecode yang perlu ditinjau</h2>"
                     "<p>Deteksi berbasis sampel; beberapa cut atau jeda bisa disengaja.</p>"
                     "<table><thead><tr><th>Jenis</th><th>Mulai</th><th>Selesai</th><th>Durasi</th></tr></thead>"
                     "<tbody>" + "".join(segment_rows) + "</tbody></table></section>") if segment_rows else ""
    return f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(file['name'])} | Release Lab</title>
<style>*{{box-sizing:border-box}}body{{font:15px/1.6 system-ui,sans-serif;background:#f4f3ed;color:#202720;margin:0}}
main{{max-width:980px;margin:auto;padding:40px 22px 80px}}.top{{display:flex;justify-content:space-between;gap:16px;border-bottom:2px solid #222f29;padding-bottom:20px}}
.eyebrow{{font-size:11px;font-weight:800;letter-spacing:.17em;text-transform:uppercase}}h1{{font-size:clamp(34px,5vw,58px);line-height:1.06;letter-spacing:-.06em;margin:34px 0 15px;overflow-wrap:anywhere}}
.status{{display:inline-block;padding:8px 16px;background:#d9e5d2;border:1px solid #48654c;font-weight:800;text-transform:uppercase}}
.status-warn{{background:#fff0cb;border-color:#7a5b2a}}.status-fail{{background:#ffe0dc;border-color:#983d36}}
.intro{{max-width:670px;color:#48564b}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:26px;margin:36px 0}}
.panel{{background:#fff;border:1px solid #d5d8cc;padding:24px;border-radius:4px}}.poster{{max-height:390px;max-width:100%;object-fit:contain;display:block;margin:auto}}
.meta{{list-style:none;padding:0;margin:0}}.meta li{{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid #e8e9e2;padding:10px 0}}
.meta strong{{text-align:right;overflow-wrap:anywhere}}.check{{display:grid;grid-template-columns:75px 1fr;gap:19px;padding:22px 0;border-bottom:1px solid #d8ddcf}}
.check h3{{margin:0;font-size:20px;letter-spacing:-.035em}}.check p{{margin:2px 0 4px;color:#353d38}}.check small{{color:#58635b}}
.flag{{font-size:11px;letter-spacing:.08em;font-weight:800;margin-top:3px}}.flag-pass{{color:#216d42}}.flag-warn{{color:#a2650d}}.flag-fail{{color:#ba2b30}}
footer{{margin-top:50px;border-top:1px solid #b1b5ac;padding-top:20px;color:#58635b;font-size:12px}}code{{overflow-wrap:anywhere}}.timeline{{margin:34px 0}}.timeline table{{width:100%;border-collapse:collapse;text-align:left}}.timeline td,.timeline th{{padding:10px;border-bottom:1px solid #d8ddcf;font-size:13px;overflow-wrap:anywhere}}
@media(max-width:680px){{.columns{{grid-template-columns:1fr}}.top{{flex-direction:column}}.check{{grid-template-columns:55px 1fr;gap:10px}}}}</style></head><body>
<main><div class="top"><b>AIWALLET <span style="opacity:.55">/ RELEASE LAB</span></b><span class="eyebrow">Laporan QC · {esc(result['ruleset'])}</span></div>
<h1>{esc(file['name'])}</h1><p class="intro">Pemeriksaan teknis berbasis aturan yang dapat ditinjau, bukan janji performa konten atau persetujuan Instagram, YouTube, atau TikTok.</p>
<span class="status status-{esc(summary['status'])}">{chips[summary['status']]} · {summary['passed']} lulus / {summary['warnings']} perhatian</span>
<div class="columns"><div class="panel">{poster_html or 'Preview tidak tersedia'}<p style="font-size:11px;color:#657166">Sumber video tidak dibagikan atau diunggah ke layanan eksternal.</p></div>
<div class="panel"><b class="eyebrow">Data sumber</b><ul class="meta">
<li><span>Resolusi</span><strong>{result['metadata']['width']} × {result['metadata']['height']}</strong></li>
<li><span>Durasi</span><strong>{result['metadata']['duration_seconds']} dtk</strong></li>
<li><span>Frame rate</span><strong>{esc(result['metadata']['fps'])} fps</strong></li>
<li><span>Video / audio</span><strong>{esc(result['metadata']['video_codec'])} / {esc(result['metadata']['audio_codec'] or 'tanpa audio')}</strong></li>
<li><span>SHA-256</span><strong><code>{esc(file['sha256'][:18])}…</code></strong></li></ul></div></div>
<h2>Catatan pemeriksaan</h2>{rows}{timeline_html}<footer>{esc(result['caveat'])}<br>Dibuat {esc(result['created_at'])} · AIWallet Release Lab v{esc(result['software_version'])} · Apache-2.0</footer></main></body></html>"""


def save_report(result: dict[str, Any], dest: Path, poster: Path | None = None) -> tuple[Path, Path]:
    dest.mkdir(parents=True, exist_ok=True)
    json_path, html_path = dest / "audit.json", dest / "audit.html"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_html(result, poster), encoding="utf-8")
    return json_path, html_path
