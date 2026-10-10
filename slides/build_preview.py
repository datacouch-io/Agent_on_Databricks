#!/usr/bin/env python3
"""Build preview.html - a standalone local view of the whole deck.

Reads project/deck.json and project/slides/*.html, rewrites the artifact
asset ids (/_blob/<id>) to local files using assets/MAPPING.md, and writes
every slide scaled to 1280px with its speaker notes underneath.

    python3 build_preview.py && python3 -m http.server 8777
    open http://127.0.0.1:8777/preview.html
"""
import json, re, pathlib, html as _html

ROOT = pathlib.Path(__file__).parent
deck = json.loads((ROOT/"project/deck.json").read_text())

blob = dict(re.findall(r"\|\s*`([0-9a-f]{32})`\s*\|\s*`([^`]+)`\s*\|",
                       (ROOT/"assets/MAPPING.md").read_text()))

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
 body{margin:0;background:#5A5F66;font-family:'IBM Plex Sans',Arial,sans-serif}
 .wrap{margin:0 auto 54px;width:1280px;max-width:96vw}
 .num{color:#D7DBE0;font-size:13px;letter-spacing:1px;text-transform:uppercase;padding:14px 2px 8px}
 .stage{width:1280px;height:720px;overflow:hidden;position:relative;box-shadow:0 10px 30px rgba(0,0,0,.35);background:#FBFBF8}
 .stage>section p,.stage>section h1,.stage>section h2,.stage>section h3,
 .stage>section ul,.stage>section ol,.stage>section li,.stage>section figure{margin:0}
 .stage>section *{box-sizing:border-box}
 .stage>section{position:absolute;top:0;left:0;width:1920px;height:1080px;transform:scale(.6667);transform-origin:top left;box-sizing:border-box;margin:0}
 .notes{background:#2B3038;color:#C7CED6;font-size:14px;line-height:1.55;padding:16px 20px;white-space:pre-wrap;border-radius:0 0 4px 4px}
 .notes b{color:#F2F4F7}
 h1.t{color:#F2F4F7;text-align:center;font-size:22px;padding:30px 0 6px;margin:0}
 p.sub{color:#AEB6BF;text-align:center;font-size:14px;margin:0 0 26px}
</style></head><body>
<h1 class="t">%s</h1><p class="sub">%d slides &middot; local preview</p>
"""

def localise(s):
    for bid, path in blob.items():
        s = s.replace(f"/_blob/{bid}", path)
    return s

parts = [HEAD % (deck["title"], deck["title"], len(deck["order"]))]
for i, sid in enumerate(deck["order"], 1):
    raw = (ROOT/f"project/slides/{sid}.html").read_text()
    m = re.search(r"<aside>(.*?)</aside>", raw, re.S)
    notes = _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    body = localise(re.sub(r"<aside>.*?</aside>", "", raw, flags=re.S))
    parts.append(f'<div class="wrap"><div class="num">{i} &nbsp;/&nbsp; {sid}</div>'
                 f'<div class="stage">{body}</div>'
                 f'<div class="notes">{_html.escape(notes) or "<i>no notes</i>"}</div></div>')
parts.append("</body></html>")
out = ROOT/"preview.html"
out.write_text("".join(parts))
print(f"wrote {out} - {len(deck['order'])} slides, {out.stat().st_size//1024} KB")
