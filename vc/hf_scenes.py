"""Story 10：把 kind=anim 的段落產生成 HyperFrames 專案並渲染成 MP4。

每個段落、每個版本各一個資料夾：work/hf/<variant>/<scene>/index.html。
動畫時間點來自 timeline.json 的 at_frames（旁白念到某個字的影格），所以畫面跟旁白同步。
畫面下方 150 px 保留給字幕，範本不放內容。

輸出：work/hf/<variant>/<scene>.mp4 與 work/hf/manifest.json（快取）
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment

from vc.media import can_use_nvenc
from vc.project import load_project
from vc.tools import ROOT, find_tool

FONT_SRC = {"segoeui.ttf": Path("C:/Windows/Fonts/segoeui.ttf"), "segoeuib.ttf": Path("C:/Windows/Fonts/segoeuib.ttf")}
GSAP = ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"

BASE = """<!doctype html>
<html><head><meta charset="utf-8">
<style>
@font-face { font-family: "VC Sans"; src: url("assets/segoeui.ttf"); font-weight: 400; }
@font-face { font-family: "VC Sans"; src: url("assets/segoeuib.ttf"); font-weight: 700; }
#stage { position: relative; width: 1920px; height: 1080px; overflow: hidden;
         background-color: #0b1220;
         background-image:
           radial-gradient(1300px 750px at 25% 20%, rgba(30, 58, 102, 0.75) 0%, transparent 70%),
           radial-gradient(1000px 600px at 80% 80%, rgba(16, 37, 66, 0.6) 0%, transparent 70%),
           linear-gradient(to right, rgba(255, 255, 255, 0.035) 1px, transparent 1px),
           linear-gradient(to bottom, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
         background-size: 100% 100%, 100% 100%, 60px 60px, 60px 60px;
         font-family: "VC Sans"; }
.clip { position: absolute; }
.hide { opacity: 0; }
.h1 { font-weight: 700; font-size: 60px; color: #fff; letter-spacing: -0.5px; }
.kicker { font-weight: 700; font-size: 26px; letter-spacing: 4px; color: #3fa9f5; text-transform: uppercase; }
.card { background: rgba(16, 26, 46, 0.72); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 16px 36px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.12);
        border-radius: 18px; box-sizing: border-box; }
.num { font-weight: 700; color: #3fa9f5; }
.t { font-weight: 700; color: #fff; }
.l { font-weight: 400; color: #b9c6dc; }
.cap { font-size: 26px; color: #b9c6dc; text-align: center; }
.shot { background: #fff; border-radius: 14px; box-sizing: border-box; padding: 10px;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.45); }
.shot img { width: 100%; height: 100%; object-fit: contain; display: block; }
{{ css }}
</style></head>
<body>
<div id="stage" data-composition-id="{{ comp_id }}" data-start="0" data-width="1920" data-height="1080"
     data-duration="{{ duration }}" data-fps="{{ fps }}">
{{ body }}
</div>
<script src="assets/gsap.min.js"></script>
<script>
const tl = gsap.timeline({ paused: true });
const D = {{ duration }};
function show(sel, t, from) { tl.fromTo(sel, Object.assign({ opacity: 0, y: 24 }, from || {}),
  { opacity: 1, y: 0, x: 0, scale: 1, duration: 0.45, ease: "power2.out" }, t); }
{{ script }}
tl.to("#stage", { opacity: 1, duration: 0.01 }, D - 0.01);
window.__timelines = window.__timelines || {};
window.__timelines["{{ comp_id }}"] = tl;
</script>
</body></html>
"""


def clip(cid: str, track: int, duration: float, style: str, inner: str, cls: str = "") -> str:
    return (f'<div id="{cid}" class="clip {cls}" data-start="0" data-duration="{duration}" '
            f'data-track-index="{track}" style="{style}">{inner}</div>')


# ---------- 示意圖（public 版與概念段使用）----------

SVG_HOLE = """<svg width="840" height="560" viewBox="0 0 840 560">
<polygon points="120,330 520,180 760,260 360,410" fill="#8fb3e8" stroke="#dbe7ff" stroke-width="3"/>
<polygon points="120,330 360,410 360,450 120,370" fill="#5f84bd"/><polygon points="360,410 760,260 760,300 360,450" fill="#4d6fa5"/>
<ellipse cx="450" cy="300" rx="70" ry="32" fill="#0b1220" stroke="#ff6b4a" stroke-width="4" stroke-dasharray="10 8"/>
<text x="450" y="110" fill="#ff6b4a" font-size="30" font-weight="700" text-anchor="middle">missing face</text>
<line x1="450" y1="124" x2="450" y2="266" stroke="#ff6b4a" stroke-width="3"/></svg>"""

SVG_OFFSET = """<svg width="760" height="330" viewBox="0 0 760 330">
<rect x="80" y="70" width="600" height="160" fill="#8fb3e8" opacity="0.35" stroke="#dbe7ff" stroke-width="3"/>
<line x1="80" y1="70" x2="680" y2="70" stroke="#ffffff" stroke-width="6"/>
<line x1="80" y1="150" x2="680" y2="150" stroke="#3fe08a" stroke-width="6" stroke-dasharray="18 10"/>
<line x1="720" y1="70" x2="720" y2="150" stroke="#ffd166" stroke-width="3"/><text x="732" y="120" fill="#ffd166" font-size="28">½</text>
<text x="380" y="52" fill="#fff" font-size="26" text-anchor="middle">outer surface</text>
<text x="380" y="190" fill="#3fe08a" font-size="26" text-anchor="middle">mid-plane shell</text>
<text x="380" y="285" fill="#b9c6dc" font-size="24" text-anchor="middle">plate thickness</text></svg>"""


def _t(at: dict, term: str | None, fallback: float, fps: int) -> float:
    f = at.get(term) if term else None
    return round(f / fps, 3) if f is not None else fallback


# ---------- 範本 ----------

def tpl_title(d, at, D, fps, images, variant):
    t0 = _t(at, d.get("at_word"), 0.6, fps)
    body = [
        clip("bar", 1, D, "left:160px;top:380px;width:360px;height:8px;background:#3fa9f5;transform-origin:left;", ""),
        clip("title", 2, D, "left:160px;top:410px;font-size:110px;", d["title"], "t hide"),
        clip("sub", 3, D, "left:164px;top:560px;font-size:46px;color:#3fa9f5;", d["subtitle"], "hide"),
    ]
    script = ['tl.fromTo("#bar", {scaleX: 0}, {scaleX: 1, duration: 0.6, ease: "power2.out"}, 0.1);',
              'show("#title", 0.25);', f'show("#sub", {t0});']
    if d.get("logo") and images.get("primary"):
        body.append(clip("logos", 4, D, "right:120px;top:90px;height:56px;display:flex;align-items:center;gap:56px;",
                         _logo_row(images, 56), "hide"))
        script.append('show("#logos", 0.9);')
    return "\n".join(body), "\n".join(script), ""


def _logo_row(images: dict, h: int) -> str:
    """兩組品牌標誌並排，中間一條細分隔線；高度用 h 控制，原圖解析度高，縮小不糊。"""
    sep = f'<div style="width:2px;height:{int(h * 0.9)}px;background:rgba(255,255,255,0.35)"></div>'
    return (f'<img src="{images["primary"]}" style="height:{h}px;display:block">{sep}'
            f'<img src="{images["secondary"]}" style="height:{int(h * 1.25)}px;display:block">')


def tpl_concept(d, at, D, fps, images, variant):
    r = {x["what"]: _t(at, x["at_word"], 0, fps) for x in d.get("reveal", [])}
    lab_solid, lab_mid = d["labels"]
    kicker = d.get("kicker", "WHAT IS A THIN SHELL?")
    svg = """<svg width="1300" height="520" viewBox="0 0 1300 520">
<g id="slab"><polygon points="150,300 450,140 1150,140 850,300" fill="#8fb3e8"/>
<polygon points="150,300 850,300 850,400 150,400" fill="#5f84bd"/><polygon points="850,300 1150,140 1150,240 850,400" fill="#4d6fa5"/></g>
<g id="mid"><polygon points="150,350 450,190 1150,190 850,350" fill="none" stroke="#3fe08a" stroke-width="7"/></g></svg>"""
    body = [
        clip("kick", 1, D, "left:120px;top:90px;", kicker, "kicker"),
        clip("art", 2, D, "left:310px;top:250px;width:1300px;height:520px;", svg, "hide"),
        clip("lsolid", 3, D, "left:300px;top:720px;font-size:40px;", lab_solid, "t hide"),
        # 標籤放在板子右側，避免壓到綠色中面線（中面線約在 x 460–1460、y 440–600）
        clip("lmid", 4, D, "left:1490px;top:470px;font-size:52px;color:#3fe08a;", lab_mid, "t hide"),
    ]
    script = [f'show("#art", {max(r.get("solid", 0.8) - 0.4, 0.1)});', f'show("#lsolid", {r.get("solid", 1.0)});',
              f'tl.to("#slab", {{opacity: 0.25, duration: 0.6}}, {r.get("mid", D * 0.5)});',
              f'tl.fromTo("#mid", {{opacity: 0}}, {{opacity: 1, duration: 0.6}}, {r.get("mid", D * 0.5)});',
              f'show("#lmid", {r.get("name", D * 0.8)}, {{x: -30, y: 0}});']
    return "\n".join(body), "\n".join(script), ""


def _inset(d, at, D, fps, images, style, track):
    ins = d.get("inset") or {}
    t = _t(at, ins.get("at_word"), D * 0.6, fps)
    if "image" in ins:
        inner = f'<img src="{images["list"][ins["image"]]}">'
        el = clip("inset", track, D, style, inner, "shot hide")
    else:
        art = {"hole_in_plate": SVG_HOLE, "offset_half": SVG_OFFSET}[ins["drawing"]]
        el = clip("inset", track, D, style + "display:grid;place-items:center;", art, "hide")
    return el, t, ins.get("caption", "")


def tpl_cards3(d, at, D, fps, images, variant):
    body = [clip("head", 1, D, "left:120px;top:80px;", d["heading"], "h1")]
    script = ['show("#head", 0.1);']
    for i, c in enumerate(d["cards"]):
        t = _t(at, c.get("at_word"), 1.0 + i * 3, fps)
        inner = (f'<div class="num" style="font-size:34px;position:absolute;left:32px;top:28px">0{i + 1}</div>'
                 f'<div class="t" style="font-size:44px;position:absolute;left:110px;top:22px">{c["title"]}</div>'
                 f'<div class="l" style="font-size:30px;position:absolute;left:110px;top:92px;right:24px">{c["label"]}</div>')
        body.append(clip(f"card{i}", 2 + i, D, f"left:120px;top:{200 + i * 225}px;width:760px;height:195px;", inner, "card hide"))
        script.append(f'show("#card{i}", {t}, {{x: -40, y: 0}});')
        script.append(f'tl.to("#card{i}", {{borderColor: "#3fa9f5", duration: 0.3}}, {t});')
        if i:
            script.append(f'tl.to("#card{i - 1}", {{borderColor: "rgba(255,255,255,0.12)", duration: 0.3}}, {t});')
    el, t, cap = _inset(d, at, D, fps, images, "left:960px;top:200px;width:840px;height:600px;", 6)
    body += [el, clip("icap", 7, D, "left:960px;top:820px;width:840px;", cap, "cap hide")]
    script += [f'show("#inset", {t}, {{scale: 0.96, y: 0}});', f'show("#icap", {t + 0.2});']
    return "\n".join(body), "\n".join(script), ""


def tpl_steps4(d, at, D, fps, images, variant):
    body = [clip("head", 1, D, "left:120px;top:80px;", d["heading"], "h1")]
    script = ['show("#head", 0.1);']
    for i, s in enumerate(d["steps"]):
        t = _t(at, s.get("at_word"), 2.0 + i * 3, fps)
        inner = (f'<div class="num" style="font-size:56px;position:absolute;left:30px;top:18px">{i + 1}</div>'
                 f'<div class="t" style="font-size:42px;position:absolute;left:30px;top:100px">{s["title"]}</div>'
                 f'<div class="l" style="font-size:27px;position:absolute;left:30px;top:162px;right:20px">{s["label"]}</div>')
        body.append(clip(f"step{i}", 2 + i, D, f"left:{120 + i * 430}px;top:200px;width:400px;height:260px;", inner, "card hide"))
        script.append(f'show("#step{i}", {t});')
        script.append(f'tl.to("#step{i}", {{borderColor: "#3fa9f5", background: "rgba(63,169,245,0.14)", duration: 0.3}}, {t});')
        if i:
            script.append(f'tl.to("#step{i - 1}", {{borderColor: "rgba(255,255,255,0.12)", background: "rgba(255,255,255,0.06)", duration: 0.3}}, {t});')
    el, t, cap = _inset(d, at, D, fps, images, "left:600px;top:500px;width:720px;height:330px;", 7)
    body += [el, clip("icap", 8, D, "left:600px;top:845px;width:720px;", cap, "cap hide")]
    script += [f'show("#inset", {t}, {{scale: 0.96, y: 0}});', f'show("#icap", {t + 0.2});']
    return "\n".join(body), "\n".join(script), ""


def tpl_result(d, at, D, fps, images, variant):
    a, b = d["after"], d["before"]
    ta, tb = _t(at, a.get("at_word"), 1.5, fps), _t(at, b.get("at_word"), D * 0.6, fps)

    # 數字動態計數（Number count-up via GSAP）
    val_a = a["value"]
    m_a = re.search(r"\d+", val_a)
    num_script = []
    if m_a:
        num_str = m_a.group(0)
        num_val = int(num_str)
        val_a_html = val_a.replace(num_str, f'<span id="cnt_after">{num_str}</span>', 1)
        num_script.append(
            f'let _cntObj = {{ n: 0 }}; '
            f'tl.to(_cntObj, {{ n: {num_val}, duration: 0.8, ease: "power2.out", '
            f'onUpdate: () => {{ const el = document.getElementById("cnt_after"); if (el) el.textContent = Math.round(_cntObj.n); }} }}, {ta});'
        )
    else:
        val_a_html = val_a

    body = [
        clip("kick", 1, D, "left:120px;top:90px;", "RESULT", "kicker"),
        clip("after", 2, D, "left:160px;top:260px;width:760px;",
             f'<div class="t" style="font-size:150px;color:#3fe08a">{val_a_html}</div><div class="l" style="font-size:40px">{a["label"]}</div>', "hide"),
        clip("before", 3, D, "left:1040px;top:260px;width:760px;",
             f'<div class="t" style="font-size:150px;color:#ff8f6b">{b["value"]}</div><div class="l" style="font-size:40px">{b["label"]}</div>', "hide"),
        clip("vs", 4, D, "left:930px;top:330px;font-size:60px;color:#5d6b85;", "vs", "t hide"),
        clip("foot", 5, D, "left:160px;top:640px;font-size:38px;", d["footnote"], "l hide"),
    ]
    script = [f'show("#after", {ta}, {{scale: 0.9, y: 0}});'] + num_script + [
              f'show("#foot", {ta + 1.2});',
              f'show("#vs", {tb - 0.2});', f'show("#before", {tb}, {{scale: 0.9, y: 0}});']
    # 片尾：旁白結束後，數字往上淡出，換成片名（internal 版加 logo），停留到影片結束
    t_end = round(min(d.get("outro_at_s", D - 2.8), D - 1.5), 3)
    body.append(clip("outro", 7, D, "left:0;top:300px;width:1920px;display:flex;flex-direction:column;"
                     "align-items:center;gap:40px;",
                     f'<div class="t" style="font-size:72px">{d.get("outro_title", "")}</div>'
                     + (f'<div style="display:flex;align-items:center;gap:72px">{_logo_row(images, 84)}</div>'
                        if d.get("logo") and images.get("primary") else ""), "hide"))
    script += [f'tl.to(["#after", "#before", "#vs", "#foot", "#kick"], {{opacity: 0, y: -30, duration: 0.6}}, {t_end});',
               f'show("#outro", {t_end + 0.3}, {{scale: 0.96, y: 0}});']
    return "\n".join(body), "\n".join(script), ""


def tpl_demo_mock(d, at, D, fps, images, variant):
    """public 版的操作示意：不用真實錄影，只畫出工具視窗、模型與結果。"""
    steps = d["steps"]
    times = [_t(at, s.get("at_word"), 1 + i * 2, fps) for i, s in enumerate(steps)]
    t_res = _t(at, (d.get("result_at_word") or {}).get("at_word"), times[2] + 1.0, fps)
    box = """<svg width="900" height="560" viewBox="0 0 900 560"><g id="model">
<polygon id="mtop" points="120,260 420,110 800,170 500,320" fill="#b98fd8"/>
<polygon id="mfront" points="120,260 500,320 500,450 120,390" fill="#8c63b0"/>
<polygon id="mside" points="500,320 800,170 800,300 500,450" fill="#7550a0"/></g></svg>"""
    body = [clip("win", 1, D, "left:120px;top:80px;width:1680px;height:800px;", "", "card"),
            clip("art", 2, D, "left:180px;top:170px;width:900px;height:560px;", box, "")]
    script = []
    for i, s in enumerate(steps):
        body.append(clip(f"chip{i}", 3 + i, D, f"left:1180px;top:{180 + i * 120}px;width:560px;height:96px;",
                         f'<div class="t" style="font-size:36px;padding:24px 30px">{i + 1}. {s["title"]}</div>', "card hide"))
        script.append(f'show("#chip{i}", {times[i]}, {{x: 30, y: 0}});')
        script.append(f'tl.to("#chip{i}", {{borderColor: "#3fa9f5", duration: 0.3}}, {times[i]});')
    body.append(clip("bar", 8, D, "left:180px;top:760px;width:900px;height:16px;background:rgba(255,255,255,0.12);border-radius:8px;", "", ""))
    body.append(clip("fill", 9, D, "left:180px;top:760px;width:900px;height:16px;background:#3fa9f5;border-radius:8px;transform-origin:left;", "", ""))
    body.append(clip("res", 10, D, "left:180px;top:800px;width:1500px;font-size:34px;color:#3fe08a;", d["result_line"], "t hide"))
    script += [
        'tl.set("#fill", {scaleX: 0}, 0);',
        f'tl.to(["#mtop", "#mfront", "#mside"], {{fill: "#ff7a1a", duration: 0.3}}, {times[1]});',
        f'tl.to("#fill", {{scaleX: 1, duration: {max(t_res - times[2], 0.5)}, ease: "none"}}, {times[2]});',
        f'tl.to("#mtop", {{fill: "#9fe0bf", duration: 0.4}}, {t_res});',
        f'tl.to("#mfront", {{fill: "#6cc49a", duration: 0.4}}, {t_res});',
        f'tl.to("#mside", {{fill: "#56a983", duration: 0.4}}, {t_res});',
        f'show("#res", {t_res});',
    ]
    return "\n".join(body), "\n".join(script), ""


def tpl_vs_intro_mock(d, at, D, fps, images, variant):
    t_act = _t(at, "Version", D * 0.5, fps)

    left_svg = """<svg width="600" height="340" viewBox="0 0 600 340">
<polygon points="60,200 240,110 540,150 360,240" fill="#3b2b35" stroke="#fc6255" stroke-width="2.5" stroke-dasharray="8 6"/>
<ellipse cx="300" cy="180" rx="45" ry="22" fill="#0b1220" stroke="#fc6255" stroke-width="3"/>
<text x="300" y="80" fill="#fc6255" font-size="24" font-weight="700" text-anchor="middle">Missing Faces & Disconnected Pieces</text>
<text x="300" y="280" fill="#fc6255" font-size="28" font-weight="700" text-anchor="middle">Operation Failed</text>
</svg>"""

    right_svg = """<svg width="600" height="340" viewBox="0 0 600 340">
<polygon points="60,200 240,110 540,150 360,240" fill="rgba(63,224,138,0.2)" stroke="#3fe08a" stroke-width="3.5"/>
<ellipse cx="300" cy="180" rx="45" ry="22" fill="rgba(63,224,138,0.3)" stroke="#3fe08a" stroke-width="2.5"/>
<text x="300" y="80" fill="#3fe08a" font-size="24" font-weight="700" text-anchor="middle">1 Continuous Shell Body</text>
<text x="300" y="280" fill="#3fe08a" font-size="28" font-weight="700" text-anchor="middle">Automated & Watertight</text>
</svg>"""

    left_title = d.get("left_title", "Built-in Manual Tool")
    left_sub = d.get("left_subtitle", "Breaks geometry into pieces · Hours of manual repair")
    right_title = d.get("right_title", "Batch Validator v3.0")
    right_sub = d.get("right_subtitle", "One clean surface in seconds · Zero manual repair")
    body = [
        clip("kick", 1, D, "left:120px;top:80px;", d.get("badge", "BEFORE VS AFTER"), "kicker"),
        clip("head", 2, D, "left:120px;top:125px;font-size:56px;", d["title"], "t"),
        clip("sub", 3, D, "left:120px;top:195px;font-size:32px;color:#3fa9f5;", d["subtitle"], "hide"),
        clip("panel_left", 4, D, "left:160px;top:280px;width:760px;height:520px;padding:30px;",
             f'<div class="t" style="font-size:38px;color:#fc6255;margin-bottom:20px;">{left_title}</div>'
             f'<div style="display:grid;place-items:center;">{left_svg}</div>'
             f'<div class="l" style="font-size:26px;color:#ff8f6b;text-align:center;margin-top:10px;">{left_sub}</div>',
             "card hide"),
        clip("panel_right", 5, D, "left:1000px;top:280px;width:760px;height:520px;padding:30px;border-color:rgba(63,224,138,0.4);",
             f'<div class="t" style="font-size:38px;color:#3fe08a;margin-bottom:20px;">{right_title}</div>'
             f'<div style="display:grid;place-items:center;">{right_svg}</div>'
             f'<div class="l" style="font-size:26px;color:#a3f3cb;text-align:center;margin-top:10px;">{right_sub}</div>',
             "card hide"),
    ]
    script = [
        'show("#kick", 0.1);',
        'show("#head", 0.2);',
        'show("#sub", 0.4);',
        'show("#panel_left", 0.8, {x: -30, y: 0});',
        f'show("#panel_right", {t_act}, {{x: 30, y: 0}});',
        f'tl.to("#panel_right", {{boxShadow: "0 0 30px rgba(63,224,138,0.3)", duration: 0.5}}, {t_act});',
    ]
    return "\n".join(body), "\n".join(script), ""


def tpl_chassis_mock(d, at, D, fps, images, variant):
    t_res = _t(at, d.get("at_word"), D * 0.75, fps)

    chassis_svg = """<svg width="760" height="480" viewBox="0 0 760 480">
<rect x="40" y="60" width="680" height="340" rx="16" fill="rgba(26,46,76,0.6)" stroke="#3fa9f5" stroke-width="3"/>
<rect x="70" y="90" width="620" height="50" rx="8" fill="rgba(63,169,245,0.15)" stroke="#3fa9f5" stroke-width="1.5"/>
<rect x="70" y="160" width="620" height="50" rx="8" fill="rgba(63,169,245,0.15)" stroke="#3fa9f5" stroke-width="1.5"/>
<rect x="70" y="230" width="620" height="50" rx="8" fill="rgba(63,169,245,0.15)" stroke="#3fa9f5" stroke-width="1.5"/>
<rect x="70" y="300" width="620" height="50" rx="8" fill="rgba(63,169,245,0.15)" stroke="#3fa9f5" stroke-width="1.5"/>
<circle cx="110" cy="115" r="12" fill="#3fe08a"/>
<circle cx="150" cy="115" r="12" fill="#3fe08a"/>
<circle cx="190" cy="115" r="12" fill="#3fe08a"/>
<circle cx="110" cy="185" r="12" fill="#3fe08a"/>
<circle cx="150" cy="185" r="12" fill="#3fe08a"/>
<circle cx="190" cy="185" r="12" fill="#3fe08a"/>
<text x="650" y="125" fill="#3fe08a" font-size="22" font-weight="700" text-anchor="end">OK</text>
<text x="650" y="195" fill="#3fe08a" font-size="22" font-weight="700" text-anchor="end">OK</text>
<text x="650" y="265" fill="#3fe08a" font-size="22" font-weight="700" text-anchor="end">OK</text>
<text x="650" y="335" fill="#3fe08a" font-size="22" font-weight="700" text-anchor="end">OK</text>
</svg>"""

    count = int(d.get("count", 24))
    depth_label = d.get("depth_label", "Assembly Hierarchy: 4–6 Levels Deep")
    body = [
        clip("kick", 1, D, "left:120px;top:80px;", d.get("kicker", "FULL ASSEMBLY BATCH VALIDATION"), "kicker"),
        clip("head", 2, D, "left:120px;top:125px;font-size:56px;", d["title"], "t"),
        clip("chassis", 3, D, "left:140px;top:240px;width:760px;height:480px;", chassis_svg, "hide"),
        clip("info_card", 4, D, "left:980px;top:240px;width:780px;height:480px;padding:36px;",
             f'<div class="t" style="font-size:36px;color:#3fa9f5;margin-bottom:16px;">{depth_label}</div>'
             f'<div class="l" style="font-size:26px;color:#b9c6dc;margin-bottom:30px;">Recursive tree traversal detects all nested sheet metal bodies automatically.</div>'
             f'<div style="font-size:80px;font-weight:700;color:#3fe08a;margin-bottom:10px;"><span id="chassis_cnt">0</span> / {count}</div>'
             f'<div class="l" style="font-size:26px;color:#3fe08a;margin-bottom:24px;">Parts Processed Successfully</div>'
             f'<div style="width:100%;height:16px;background:rgba(255,255,255,0.12);border-radius:8px;overflow:hidden;">'
             f'  <div id="pbar" style="width:0%;height:100%;background:#3fe08a;border-radius:8px;"></div>'
             f'</div>'
             f'<div id="res_badge" class="hide" style="margin-top:24px;padding:16px 24px;background:rgba(63,224,138,0.15);border:1.5px solid #3fe08a;border-radius:12px;font-size:26px;font-weight:700;color:#3fe08a;text-align:center;">'
             f'  {d["result_line"]}'
             f'</div>',
             "card hide"),
    ]
    script = [
        'show("#kick", 0.1);',
        'show("#head", 0.2);',
        'show("#chassis", 0.5, {scale: 0.95, y: 0});',
        'show("#info_card", 0.8, {x: 30, y: 0});',
        'let _cObj = { n: 0, p: 0 };',
        f'tl.to(_cObj, {{ n: {count}, p: 100, duration: {max(t_res - 1.2, 1.0)}, ease: "power1.inOut", ',
        f'onUpdate: () => {{ '
        f'  const el = document.getElementById("chassis_cnt"); if (el) el.textContent = Math.round(_cObj.n); '
        f'  const pb = document.getElementById("pbar"); if (pb) pb.style.width = _cObj.p + "%"; '
        f'}} }}, 1.2);',
        f'show("#res_badge", {t_res}, {{scale: 0.9, y: 0}});',
    ]
    return "\n".join(body), "\n".join(script), ""


TEMPLATES = {"title": tpl_title, "concept": tpl_concept, "cards3": tpl_cards3, "steps4": tpl_steps4,
             "result": tpl_result, "demo_mock": tpl_demo_mock, "vs_intro_mock": tpl_vs_intro_mock,
             "chassis_mock": tpl_chassis_mock}


# ---------- 產生與渲染 ----------

def brand_logos(work: Path) -> dict[str, Path]:
    """產生深色背景適用的高解析度透明 PNG 品牌標誌（internal 版使用）。"""
    from vc.brand import TEMPLATES, make_logos

    out = work / "brand"
    files = {"primary": out / "primary_white.png", "secondary": out / "secondary_white.png"}
    custom = [TEMPLATES / "primary_logo.png", TEMPLATES / "secondary_logo.png"]
    custom_mtime = max((s.stat().st_mtime for s in custom if s.is_file()), default=0.0)
    if not all(f.is_file() for f in files.values()) or (
        custom_mtime and custom_mtime > min(f.stat().st_mtime for f in files.values())
    ):
        files = make_logos(out)
    return files


def build_project(scene: dict, variant: str, tl: dict, work: Path) -> Path:
    vis = scene["visuals"][variant]
    fps = tl["fps"]
    D = round(scene["duration_frames"] / fps, 4)
    folder = work / "hf" / variant / scene["id"]
    assets = folder / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GSAP, assets / "gsap.min.js")
    for name, src in FONT_SRC.items():
        shutil.copyfile(src, assets / name)
    images = {"list": []}
    for i, img in enumerate(vis.get("images", [])):
        dst = assets / f"img{i}{Path(img).suffix}"
        shutil.copyfile(img, dst)
        images["list"].append(f"assets/{dst.name}")
    if variant == "internal":
        for name, f in brand_logos(work).items():
            shutil.copyfile(f, assets / f.name)
            images[name] = f"assets/{f.name}"
    data = dict(vis["data"])
    # 旁白念完後 0.4 s 才換片尾，避免最後一句還沒講完畫面就變
    data["outro_at_s"] = round((scene["narration_start_frame"] + scene["narration_frames"]) / fps + 0.4, 3)
    body, script, css = TEMPLATES[vis["template"]](data, scene["at_frames"], D, fps, images, variant)
    html = Environment(autoescape=False).from_string(BASE).render(
        comp_id=f"{scene['id']}-{variant}", duration=D, fps=fps, body=body, script=script, css=css)
    (folder / "index.html").write_text(html, encoding="utf-8")
    return folder


def _hf() -> str:
    exe = find_tool("hyperframes")
    if not exe:
        raise FileNotFoundError("找不到 hyperframes，在專案根目錄執行 npm install")
    return exe


def folder_key(folder: Path) -> str:
    h = hashlib.sha1()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and ".hyperframes" not in p.parts:
            h.update(p.relative_to(folder).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def lint(folder: Path) -> tuple[int, str]:
    res = _run_in(folder, [_hf(), "lint"], timeout=300)
    text = res.stdout + res.stderr
    m = re.search(r"(\d+) error", text)
    return (int(m.group(1)) if m else (0 if res.returncode == 0 else 1)), text


def _run_in(folder: Path, cmd: list[str], timeout: float = 900):
    env = dict(os.environ, NODE_USE_SYSTEM_CA="1")
    env["PATH"] = str(Path(find_tool("ffmpeg")).parent) + os.pathsep + env["PATH"]
    return subprocess.run(cmd, cwd=str(folder), capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, env=env)


def render_all(tl: dict, work: Path, quality: str = "draft", use_gpu: bool = True) -> list[dict]:
    man_path = work / "hf" / "manifest.json"
    old = json.loads(man_path.read_text(encoding="utf-8")) if man_path.is_file() else {}
    gpu_ready = use_gpu and can_use_nvenc()
    new, report = {}, []
    for sc in tl["scenes"]:
        for variant in ("internal", "public"):
            if sc["visuals"][variant]["kind"] != "anim":
                continue
            folder = build_project(sc, variant, tl, work)
            out = work / "hf" / variant / f"{sc['id']}.mp4"
            key = folder_key(folder) + quality
            entry = {"scene": sc["id"], "variant": variant, "file": str(out.relative_to(work)).replace("\\", "/")}
            if old.get(entry["file"]) == key and out.is_file():
                entry["made"] = False
            else:
                errors, text = lint(folder)
                if errors:
                    raise RuntimeError(f"{sc['id']}/{variant} lint 有 {errors} 個錯誤：\n{text[-1500:]}")
                out.unlink(missing_ok=True)
                cpu_cmd = [_hf(), "render", "--quality", quality, "--output", str(out)]
                if gpu_ready:
                    gpu_cmd = [_hf(), "render", "--gpu", "--browser-gpu", "--quality", quality, "--output", str(out)]
                    res = _run_in(folder, gpu_cmd)
                    if res.returncode != 0 or not out.is_file():
                        out.unlink(missing_ok=True)
                        res = _run_in(folder, cpu_cmd)
                else:
                    res = _run_in(folder, cpu_cmd)
                if res.returncode != 0 or not out.is_file():
                    raise RuntimeError(f"{sc['id']}/{variant} 渲染失敗：\n{(res.stdout + res.stderr)[-1500:]}")
                entry["made"] = True
            new[entry["file"]] = key
            report.append(entry)
            man_path.write_text(json.dumps(new, indent=2), encoding="utf-8")
    return report


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc hf <project> [--quality draft|looks|delivery] [--no-gpu]")
        return 2
    proj = load_project(argv[0])
    quality = argv[argv.index("--quality") + 1] if "--quality" in argv else "draft"
    use_gpu = "--no-gpu" not in argv
    tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
    from vc.fit import count_frames

    report = render_all(tl, proj.work, quality, use_gpu=use_gpu)
    frames = {s["id"]: s["duration_frames"] for s in tl["scenes"]}
    bad = []
    for r in report:
        n = count_frames(proj.work / r["file"])
        ok = abs(n - frames[r["scene"]]) <= 1
        bad += [] if ok else [r["file"]]
        print(f"{r['file']:<28} 影格 {n:>4} / {frames[r['scene']]:<4} {'重新渲染' if r['made'] else '快取'}")
    if bad:
        print(f"影格數不符：{bad}", file=sys.stderr)
        return 1
    print("全部動畫段落渲染完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
