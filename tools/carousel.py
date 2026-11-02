#!/usr/bin/env python3
"""Build carousel slide HTML (1080x1350) from a JSON spec.

Usage: python3 tools/carousel.py posts/<name>/spec.json
Writes posts/<name>/build/slides.html and cropped images, then run
`node tools/render.js posts/<name>/build/slides.html posts/<name>/slides`.
"""
import html, json, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDLE = "@seoyun.dailylook"
# 공정위 추천·보증 심사지침(2026-06-01 시행): 가상인물이 나오는 동안 인물 가까이에 표시
BADGE = '<span class="badge">AI 가상인물</span>'

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&display=block');
:root{--bg:#F4EEE6;--ink:#2A2521;--muted:#7D7065;--accent:#9A7550;--line:#E2D7C9;--card:#FBF8F3}
*{margin:0;padding:0;box-sizing:border-box}
body{background:#ccc}
.slide{width:1080px;height:1350px;position:relative;overflow:hidden;background:var(--bg);color:var(--ink);
  font-family:'Noto Sans KR',sans-serif;font-size:40px;line-height:1.55;letter-spacing:-0.01em;margin-bottom:20px;word-break:keep-all}
.num{position:absolute;top:56px;right:72px;font-size:30px;color:var(--muted);letter-spacing:.04em}
.handle{position:absolute;bottom:50px;left:72px;font-size:30px;color:var(--muted)}
.serif{font-family:'Noto Serif KR',serif;font-weight:700;letter-spacing:-0.02em;line-height:1.3}
.pill{display:inline-block;border:2px solid var(--accent);color:var(--accent);border-radius:999px;padding:6px 26px;font-size:32px;font-weight:500}
.label{color:var(--accent);font-size:32px;font-weight:700;letter-spacing:.02em}
.muted{color:var(--muted)}
.note{font-size:32px;color:var(--muted);line-height:1.5}
/* cover */
.cover .top{position:absolute;top:96px;left:120px;right:120px}
.cover h1{font-size:84px;margin-top:26px}
.cover .sub{font-size:38px;color:var(--muted);margin-top:14px}
.pw{position:absolute;left:50%;transform:translateX(-50%)}
.pw img{width:100%;height:100%;object-fit:cover;border-radius:28px;display:block}
.badge{position:absolute;top:22px;left:22px;background:rgba(42,37,33,.80);color:#fff;font-size:32px;font-weight:500;line-height:1.2;padding:8px 20px;border-radius:999px}
.cover .pw{bottom:96px;width:600px;height:750px}
/* text slide */
.text .wrap{position:absolute;top:150px;bottom:170px;left:120px;right:120px;display:flex;flex-direction:column;justify-content:center}
.text p{font-size:44px}
.text ul.list li{font-size:42px}
.text h2{font-size:76px;margin:24px 0 48px}
.text p{margin-bottom:28px}
ul.list{list-style:none}
ul.list li{padding:26px 0;border-top:2px solid var(--line);display:flex;gap:28px;align-items:baseline}
ul.list li:last-child{border-bottom:2px solid var(--line)}
ul.list .k{color:var(--accent);font-weight:700;min-width:56px}
/* photo + text slide */
.item .pw{top:130px;width:720px;height:720px}
.item .pw.tall{width:420px;height:525px;top:120px}
.item .wrap{position:absolute;top:900px;left:120px;right:120px}
.item .wrap.lower{top:690px}
.item h2{font-size:62px;margin:10px 0 18px}
.item .body{font-size:38px}
.item ul.list li{padding:14px 0;font-size:36px}
/* recap */
.recap .wrap{position:absolute;top:200px;left:120px;right:120px}
.recap h2{font-size:76px;margin:20px 0 50px}
.row{display:flex;align-items:center;gap:32px;padding:24px 0;border-top:2px solid var(--line)}
.row:last-of-type{border-bottom:2px solid var(--line)}
.sw{width:76px;height:76px;border-radius:50%;flex:none;border:2px solid rgba(0,0,0,.08)}
.rule{margin-top:56px;background:var(--card);border-radius:24px;padding:34px 40px;font-size:42px}
/* cta */
.cta .wrap{position:absolute;top:300px;left:120px;right:120px;text-align:center}
.cta .big{font-size:110px;margin:36px 0 30px;color:var(--ink)}
.cta .sub{font-size:42px}
.cta .foot{position:absolute;bottom:130px;left:120px;right:120px;text-align:center}
"""

def esc(s):
    return html.escape(s).replace("\n", "<br>")

def crop(src, box, out, size):
    im = Image.open(os.path.join(ROOT, src)).convert("RGB")
    if box:
        im = im.crop(tuple(box))
    im.thumbnail((size * 2, size * 2), Image.LANCZOS)
    im.save(out, quality=92)
    return os.path.basename(out)

def slide(s, i, n, build):
    kind = s["type"]
    num = f'<div class="num">{i}/{n}</div>'
    foot = f'<div class="handle">{HANDLE}</div>'
    inner = ""
    if kind == "cover":
        img = crop(s["image"], s.get("crop"), os.path.join(build, f"img{i}.jpg"), 800)
        inner = (f'<div class="top"><span class="pill">{esc(s["pill"])}</span>'
                 f'<h1 class="serif">{esc(s["title"])}</h1><div class="sub">{esc(s["sub"])}</div></div>'
                 f'<div class="pw"><img src="{img}">{BADGE}</div>')
    elif kind == "text":
        body = "".join(f"<p>{esc(p)}</p>" for p in s.get("paras", []))
        if s.get("list"):
            body += '<ul class="list">' + "".join(
                f'<li><span class="k">{esc(k)}</span><span>{esc(v)}</span></li>' for k, v in s["list"]) + "</ul>"
        if s.get("note"):
            body += f'<p class="note" style="margin-top:40px">{esc(s["note"])}</p>'
        inner = (f'<div class="wrap"><div class="label">{esc(s.get("label",""))}</div>'
                 f'<h2 class="serif">{esc(s["title"])}</h2>{body}</div>')
    elif kind == "item":
        tall = s.get("tall", False)
        img = crop(s["image"], s.get("crop"), os.path.join(build, f"img{i}.jpg"), 720)
        body = f'<div class="body">{esc(s["body"])}</div>' if s.get("body") else ""
        if s.get("list"):
            body += '<ul class="list">' + "".join(
                f'<li><span class="k">{esc(k)}</span><span>{esc(v)}</span></li>' for k, v in s["list"]) + "</ul>"
        if s.get("note"):
            body += f'<p class="note" style="margin-top:22px">{esc(s["note"])}</p>'
        inner = (f'<div class="pw{" tall" if tall else ""}"><img src="{img}">{BADGE}</div>'
                 f'<div class="wrap{" lower" if tall else ""}"><div class="label">{esc(s["label"])}</div>'
                 f'<h2 class="serif">{esc(s["title"])}</h2>{body}</div>')
    elif kind == "recap":
        rows = "".join(f'<div class="row"><div class="sw" style="background:{c}"></div><div>{esc(t)}</div></div>'
                       for c, t in s["rows"])
        inner = (f'<div class="wrap"><div class="label">{esc(s.get("label",""))}</div>'
                 f'<h2 class="serif">{esc(s["title"])}</h2>{rows}'
                 f'<div class="rule serif">{esc(s["rule"])}</div></div>')
    elif kind == "cta":
        inner = (f'<div class="wrap"><div class="label">{esc(s.get("label",""))}</div>'
                 f'<div class="big serif">{esc(s["big"])}</div><div class="sub">{esc(s["sub"])}</div></div>'
                 f'<div class="foot note">{esc(s.get("note",""))}</div>')
    return f'<section class="slide {kind}">{num}{inner}{foot}</section>'

def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    build = os.path.join(os.path.dirname(os.path.abspath(spec_path)), "build")
    os.makedirs(build, exist_ok=True)
    n = len(spec["slides"])
    body = "".join(slide(s, i + 1, n, build) for i, s in enumerate(spec["slides"]))
    out = os.path.join(build, "slides.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>')
    print(out)

if __name__ == "__main__":
    main(sys.argv[1])
