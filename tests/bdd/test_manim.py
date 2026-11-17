"""features/manim.feature 的步驟實作。只測觸發時間的換算與延遲判定，不呼叫 Manim。"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc import manim_render, plan
from vc.project import resolve_project_dir
from vc.script import load_script
from vc.tools import ROOT

scenarios("manim.feature")


@pytest.fixture
def ctx(tmp_path) -> dict:
    return {"work": tmp_path / "work"}


@given("the sample script")
def script(ctx):
    ctx["script"] = load_script(resolve_project_dir("_sample") / "script.json")


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


@given(parsers.parse('the cue word of "{what}" in scene "{sid}" is "{word}"'))
def bad_cue(ctx, what, sid, word):
    ctx["bad_word"] = (sid, what, word)


@given("the timeline is built")
def timeline(ctx):
    _build(ctx)


def _build(ctx):
    voice = {sid: f"{sid}.wav" for sid in ctx["manifest"]["scenes"]}
    ctx["tl"] = plan.build_timeline(ctx["script"], ctx["manifest"], ctx["aligned"], voice,
                                    {"rec01": "a.mp4", "rec02": "b.mp4", "rec03": "c.mp4"}, ctx["work"])


def _scene(ctx, sid):
    return next(s for s in ctx["tl"]["scenes"] if s["id"] == sid)


@when(parsers.parse('I make the cue file of scene "{sid}" for "{variant}"'))
def make_cues(ctx, sid, variant):
    ctx["sid"] = sid
    ctx["cues"] = manim_render.scene_cues(_scene(ctx, sid), variant, ctx["tl"]["fps"])


@when(parsers.parse('I try to make the cue file of scene "{sid}" for "{variant}"'))
def try_cues(ctx, sid, variant):
    # 時間軸已建好之後才改觸發字，模擬「字不在旁白裡、沒有時間」的情況
    s_id, what, word = ctx["bad_word"]
    sc = _scene(ctx, s_id)
    for c in sc["visuals"][variant]["data"]["cues"]:
        if c["what"] == what:
            c["at_word"] = word
    try:
        manim_render.scene_cues(sc, variant, ctx["tl"]["fps"])
        ctx["err"] = None
    except ValueError as exc:
        ctx["err"] = str(exc)


@then(parsers.parse('the cue "{what}" is at the time of the word "{word}"'))
def cue_time(ctx, what, word):
    sc = _scene(ctx, ctx["sid"])
    w = next(x for x in ctx["aligned"]["scenes"][ctx["sid"]]["words"] if x["word"].strip(".,?") == word)
    expected = (sc["narration_start_frame"] + round(w["start"] * 30)) / 30
    assert ctx["cues"]["cues"][what] == pytest.approx(expected, abs=1e-3)


@then("the cue file duration equals the scene length in seconds")
def cue_duration(ctx):
    assert ctx["cues"]["duration"] == pytest.approx(_scene(ctx, ctx["sid"])["duration_frames"] / 30, abs=1e-3)


@then("every cue is inside the scene")
def cues_inside(ctx):
    assert all(0 <= t < ctx["cues"]["duration"] for t in ctx["cues"]["cues"].values())


@then(parsers.parse('the cue file is rejected with a message that contains "{text}"'))
def rejected(ctx, text):
    assert ctx["err"] and text in ctx["err"]


@when(parsers.parse("an animation for a cue at {target:g} seconds starts at {actual:g} seconds"))
def lateness(ctx, target, actual):
    ctx["late"] = manim_render.max_lateness_frames({"events": [{"target": target, "actual": actual}]}, 30)


@then(parsers.parse("it is {n:d} frames late"))
def late_is(ctx, n):
    assert round(ctx["late"]) == n
