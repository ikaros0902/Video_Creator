"""features/compose.feature 的步驟實作。時間軸用合成的配音資料建立，不呼叫 HyperFrames 或 Remotion。"""
from __future__ import annotations

import re

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc import hf_scenes, plan, render
from vc.script import load_script
from vc.tools import ROOT

scenarios("compose.feature")


@pytest.fixture
def ctx(tmp_path) -> dict:
    return {"work": tmp_path / "work"}


@given("the sample script")
def script(ctx):
    ctx["script"] = load_script(ROOT / "06_projects" / "_sample" / "script.json")


@given(parsers.parse("narration audio where every word lasts {per:g} seconds"))
def fake_audio(ctx, per):
    manifest = {"engine": "fake", "voice": "fake", "rate": "1", "scenes": {}}
    aligned = {"scenes": {}}
    for s in ctx["script"].scenes:
        ws = s.narration.split()
        words = [{"word": w, "start": round(i * per, 3), "end": round((i + 1) * per, 3)} for i, w in enumerate(ws)]
        manifest["scenes"][s.id] = {"duration_s": len(ws) * per + 0.1, "file": f"{s.id}.wav"}
        aligned["scenes"][s.id] = {"words": words, "at_word": {}, "cues": []}
    ctx["manifest"], ctx["aligned"] = manifest, aligned


@given("a work folder with dummy slide pictures")
def dummy_pictures(ctx):
    for s in ctx["script"].scenes:
        for v in s.visuals.values():
            for img in v.images:
                p = ctx["work"] / img
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"\x89PNG dummy")


@given("the timeline is built")
def timeline(ctx):
    voice = {sid: str(ctx["work"] / "voice" / f"{sid}.wav") for sid in ctx["manifest"]["scenes"]}
    recs = {"rec01": str(ctx["work"] / "rec01.mp4"),
            "rec02": str(ctx["work"] / "rec02.mp4"),
            "rec03": str(ctx["work"] / "rec03.mp4")}
    ctx["tl"] = plan.build_timeline(ctx["script"], ctx["manifest"], ctx["aligned"], voice,
                                    recs, ctx["work"])


def _scene(ctx, sid):
    return next(s for s in ctx["tl"]["scenes"] if s["id"] == sid)


@when(parsers.parse('I build the HyperFrames project of scene "{sid}" for "{variant}"'))
def build_one(ctx, sid, variant):
    ctx["sid"] = sid
    ctx["variant"] = variant
    ctx["folder"] = hf_scenes.build_project(_scene(ctx, sid), variant, ctx["tl"], ctx["work"])
    ctx["html"] = (ctx["folder"] / "index.html").read_text(encoding="utf-8")


@when(parsers.parse('I build the HyperFrames project of every animated scene for "{variant}"'))
def build_all(ctx, variant):
    ctx["folders"] = [hf_scenes.build_project(s, variant, ctx["tl"], ctx["work"])
                      for s in ctx["tl"]["scenes"] if s["visuals"][variant]["kind"] == "anim"]


@then(parsers.parse('the composition id is "{cid}"'))
def comp_id(ctx, cid):
    assert f'data-composition-id="{cid}"' in ctx["html"]


@then("the composition duration equals the scene length in seconds")
def comp_duration(ctx):
    sc = _scene(ctx, ctx["sid"])
    m = re.search(r'id="stage"[^>]*data-duration="([\d.]+)"', ctx["html"], re.S)
    assert m and abs(float(m.group(1)) - sc["duration_frames"] / ctx["tl"]["fps"]) < 1e-3


@then("the timeline is created paused and registered under the composition id")
def paused(ctx):
    assert "gsap.timeline({ paused: true })" in ctx["html"]
    assert f'window.__timelines["{ctx["sid"]}-{ctx["variant"]}"] = tl' in ctx["html"]


@then(parsers.parse('card {n:d} appears at the time of the word "{word}"'))
def card_time(ctx, n, word):
    sc = _scene(ctx, ctx["sid"])
    t = round(sc["at_frames"][word] / ctx["tl"]["fps"], 3)
    assert f'show("#card{n - 1}", {t},' in ctx["html"]


@then("no public project contains an image file")
def no_images(ctx):
    for f in ctx["folders"]:
        assert not list((f / "assets").glob("img*")), f


@then("no public project contains the logo")
def no_logo(ctx):
    for f in ctx["folders"]:
        assert not (f / "assets" / "primary_white.png").exists()
        assert not (f / "assets" / "secondary_white.png").exists()
        assert not (f / "assets" / "logo.png").exists()
        assert "primary_white" not in (f / "index.html").read_text(encoding="utf-8").lower()


@then("the project contains brand logos")
def has_logos(ctx):
    assert (ctx["folder"] / "assets" / "primary_white.png").exists()
    assert (ctx["folder"] / "assets" / "secondary_white.png").exists()


@when(parsers.parse('I build the Remotion props for "{variant}"'))
def props(ctx, variant):
    ctx["props"] = render.build_props(ctx["tl"], variant, ctx["work"], (1914, 1020))


@when(parsers.parse('I build the Remotion props for "{variant}" with recording sizes "{spec}"'))
def props_sizes(ctx, variant, spec):
    sizes = {k: tuple(int(n) for n in v.split("x")) for k, v in (p.split("=") for p in spec.split(","))}
    ctx["props"] = render.build_props(ctx["tl"], variant, ctx["work"], sizes)
    # 依片段的 src 對回時間軸，找出它來自哪支錄影
    ctx["clip_rec"] = {c["file"]: c["recording"] for s in ctx["tl"]["scenes"]
                       for c in s["visuals"][variant].get("clips", [])}


@then(parsers.parse('every clip from "{rid}" has the size {w:d}x{h:d}'))
def clip_size_from(ctx, rid, w, h):
    clips = [c for s in ctx["props"]["scenes"] for c in s["clips"] if ctx["clip_rec"][c["src"]] == rid]
    assert clips, f"腳本沒有來自 {rid} 的片段"
    assert all(c["rec_size"] == [w, h] for c in clips), clips


@when(parsers.parse("the music is {music:g} LUFS and the narration is {voice:g} LUFS"))
def music_levels(ctx, music, voice):
    ctx["music"], ctx["voice"] = music, voice
    ctx["gains"] = render.bgm_gains(music, voice)


def _music_after_gain(ctx, g):
    import math
    return ctx["music"] + 20 * math.log10(g)


@then("during narration the music is 20 dB below the narration")
def under_speech(ctx):
    assert _music_after_gain(ctx, ctx["gains"][0]) == pytest.approx(ctx["voice"] - 20, abs=0.05)


@then("during pauses the music is 14 dB below the narration")
def under_gap(ctx):
    assert _music_after_gain(ctx, ctx["gains"][1]) == pytest.approx(ctx["voice"] - 14, abs=0.05)


@then("every audio path is relative and has no drive letter")
def rel_audio(ctx):
    for a in ctx["props"]["audio"]:
        assert not re.match(r"^[A-Za-z]:", a["src"]) and not a["src"].startswith("/") and "\\" not in a["src"]


@then(parsers.parse('scene "{sid}" is a recording with {n:d} clips'))
def rec_scene(ctx, sid, n):
    s = next(x for x in ctx["props"]["scenes"] if x["id"] == sid)
    assert s["kind"] == "recording" and len(s["clips"]) == n


@then("an animated scene without a rendered clip uses a placeholder")
def placeholder(ctx):
    anim = [s for s in ctx["props"]["scenes"] if s["kind"] in ("anim", "manim")]
    assert anim and all(s["anim_src"] is None for s in anim)


@then("no scene is a recording")
def no_rec(ctx):
    assert all(s["kind"] != "recording" for s in ctx["props"]["scenes"])
