"""07_features/script.feature 的步驟實作。以脫敏範例腳本為基準，每個情境只改一處。"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc.project import resolve_project_dir
from vc.script import check, load_facts, load_script

scenarios("script.feature")
scenarios("script_exec.feature")

PROJECT = resolve_project_dir("_sample")
PROJECT_EXEC = resolve_project_dir("_sample_exec")


@pytest.fixture
def ctx() -> dict:
    return {"rec": None}


def _scene(ctx, sid):
    return next(s for s in ctx["script"].scenes if s.id == sid)


@given("the sample script and fact table")
def base(ctx):
    ctx["script"] = load_script(PROJECT / "script.json")
    ctx["facts"] = load_facts(PROJECT / "facts.yaml")


@given("the executive script and fact table")
def base_exec(ctx):
    ctx["script"] = load_script(PROJECT_EXEC / "script.json")
    ctx["facts"] = load_facts(PROJECT_EXEC / "facts.yaml")


@given(parsers.parse('the recording "{rid}" is {dur:g} seconds long'))
def rec_len(ctx, rid, dur):
    # 多支錄影：每一行 Given 加一支，不覆蓋前面的
    ctx["rec"] = {**(ctx["rec"] or {}), rid: dur}


@when(parsers.parse('scene "{sid}" narration is "{text}"'))
def set_narration(ctx, sid, text):
    _scene(ctx, sid).narration = text


@when(parsers.parse('the fact "{fid}" is not confirmed'))
def unconfirm(ctx, fid):
    ctx["facts"][fid].confirmed = False


@when(parsers.parse('the fact "{fid}" has no scope'))
def no_scope(ctx, fid):
    ctx["facts"][fid].scope = None


@when(parsers.parse('the timer card of scene "{sid}" says "{text}"'))
def set_timer_card(ctx, sid, text):
    _scene(ctx, sid).visual.data["timer_card"]["text"] = text


@when(parsers.parse('the visual of scene "{sid}" retains its recording'))
def retain_recording(ctx, sid):
    assert _scene(ctx, sid).visual.kind == "recording"
    assert _scene(ctx, sid).visual.clips


@when(parsers.parse('the visual of scene "{sid}" adds the picture "{img}"'))
def add_picture(ctx, sid, img):
    _scene(ctx, sid).visual.images.append(img)


@when(parsers.parse('clip {k:d} of scene "{sid}" ends at {end:g} seconds'))
def clip_end(ctx, k, sid, end):
    clip = _scene(ctx, sid).visual.clips[k]
    clip.source = (clip.source[0], end)


@when(parsers.parse('callout {k:d} of scene "{sid}" is linked to the word "{word}"'))
def callout_word(ctx, k, sid, word):
    _scene(ctx, sid).visual.callouts[k].at_word = word


@when(parsers.parse('scenes "{a}" and "{b}" change places'))
def swap(ctx, a, b):
    sc = ctx["script"].scenes
    i, j = next(n for n, s in enumerate(sc) if s.id == a), next(n for n, s in enumerate(sc) if s.id == b)
    sc[i], sc[j] = sc[j], sc[i]


@when("I validate the script")
def validate(ctx):
    ctx["errors"], ctx["stats"] = check(ctx["script"], ctx["facts"], ctx["rec"], None)


@then("there are no errors")
def no_errors(ctx):
    assert ctx["errors"] == []


@then(parsers.parse("the estimated length is from {lo:g} to {hi:g} seconds"))
def est_len(ctx, lo, hi):
    assert lo <= ctx["stats"]["estimated_s"] <= hi


@then(parsers.parse("the Flesch-Kincaid grade level is {g:g} or lower"))
def fk(ctx, g):
    assert ctx["stats"]["fk_grade"] <= g


@then(parsers.parse('an error for "{where}" mentions "{text}"'))
def error_mentions(ctx, where, text):
    hits = [e for e in ctx["errors"] if e.startswith(f"{where}:") and text in e]
    assert hits, f"沒有找到 {where} 含「{text}」的錯誤；實際錯誤：{ctx['errors']}"
