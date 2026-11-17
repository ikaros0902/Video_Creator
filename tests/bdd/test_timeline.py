"""features/timeline.feature 的步驟實作。配音長度與逐字時間是合成的，錄影用 FFmpeg 產生。"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc import fit, plan
from vc.media import ffmpeg_run, probe
from vc.project import resolve_project_dir
from vc.script import load_script
from vc.tools import ROOT, run
from vc.media import ffmpeg

scenarios("timeline.feature")


@pytest.fixture
def ctx(tmp_path) -> dict:
    return {"tmp": tmp_path}


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
        aligned["scenes"][s.id] = {"words": words, "at_word": {},
                                   "cues": [{"text": s.narration, "start": 0.0, "end": words[-1]["end"]}]}
    ctx["manifest"], ctx["aligned"] = manifest, aligned


def _build(ctx):
    return plan.build_timeline(ctx["script"], ctx["manifest"], ctx["aligned"],
                               {sid: f"{sid}.wav" for sid in ctx["manifest"]["scenes"]},
                               {"rec01": "rec01.mp4", "rec02": "rec02.mp4", "rec03": "rec03.mp4"})


@when("I build the timeline")
def build(ctx):
    ctx["tl"] = _build(ctx)


@given(parsers.parse('clip {k:d} of scene "{sid}" uses {sec:g} seconds of source video'))
def long_clip(ctx, k, sid, sec):
    clip = next(s for s in ctx["script"].scenes if s.id == sid).visuals["internal"].clips[k]
    clip.source = (clip.source[0], clip.source[0] + sec)


@when("I try to build the timeline")
def try_build(ctx):
    try:
        ctx["tl"], ctx["err"] = _build(ctx), None
    except plan.PlanError as exc:
        ctx["err"] = str(exc)


def _scene(ctx, sid):
    return next(s for s in ctx["tl"]["scenes"] if s["id"] == sid)


@then("each scene starts on the frame where the previous scene ends")
def contiguous(ctx):
    sc = ctx["tl"]["scenes"]
    for a, b in zip(sc, sc[1:]):
        assert a["start_frame"] + a["duration_frames"] == b["start_frame"]


@then("the total frame count equals the sum of all scene frame counts")
def total(ctx):
    assert ctx["tl"]["total_frames"] == sum(s["duration_frames"] for s in ctx["tl"]["scenes"])


@then("each scene start frame equals the rounded running total of scene seconds")
def no_drift(ctx):
    narr = {k: v["duration_s"] for k, v in ctx["manifest"]["scenes"].items()}
    cum, fps = 0.0, ctx["tl"]["fps"]
    for s, (_, length) in zip(ctx["tl"]["scenes"], plan.scene_lengths(ctx["script"], narr)):
        assert s["start_frame"] == round(cum * fps)
        cum += length


@then("every scene lasts longer than its narration")
def longer(ctx):
    for s in ctx["tl"]["scenes"]:
        assert s["duration_frames"] > s["narration_start_frame"] + s["narration_frames"]


@then("the narration audio of every scene starts inside that scene")
def audio_inside(ctx):
    for a, s in zip(ctx["tl"]["audio"], ctx["tl"]["scenes"]):
        assert s["start_frame"] <= a["start_frame"] < s["start_frame"] + s["duration_frames"]


@then(parsers.parse('the internal clips of scene "{sid}" cover the scene with no gap and no overlap'))
def cover(ctx, sid):
    s = _scene(ctx, sid)
    clips = s["visuals"]["internal"]["clips"]
    pos = 0
    for c in clips:
        assert c["start_frame"] == pos
        pos += c["duration_frames"]
    assert pos == s["duration_frames"]


@then(parsers.parse('clip {k:d} of scene "{sid}" starts on the frame of the word "{word}"'))
def clip_on_word(ctx, k, sid, word):
    s = _scene(ctx, sid)
    w = next(x for x in ctx["aligned"]["scenes"][sid]["words"] if x["word"].strip(".,") == word)
    assert s["visuals"]["internal"]["clips"][k]["start_frame"] == s["narration_start_frame"] + round(w["start"] * 30)


@then(parsers.parse("no clip plays faster than {x:g} times normal speed"))
def speed_cap(ctx, x):
    for s in ctx["tl"]["scenes"]:
        for c in s["visuals"]["internal"].get("clips", []):
            assert c["speed"] <= x


@then(parsers.parse('the timeline is rejected with a message that contains "{text}"'))
def rejected(ctx, text):
    assert ctx["err"] and text in ctx["err"]


@then(parsers.parse('the callout for "{word}" in scene "{sid}" appears on the frame of that word'))
def callout_frame(ctx, word, sid):
    s = _scene(ctx, sid)
    co = next(c for c in s["visuals"]["internal"]["callouts"] if c["at_word"] == word)
    w = next(x for x in ctx["aligned"]["scenes"][sid]["words"] if x["word"].strip(".,") == word)
    assert co["frame"] == s["narration_start_frame"] + round(w["start"] * 30)


@then("the last caption ends before the last frame of the video")
def cues_inside(ctx):
    assert ctx["tl"]["cues"][-1]["end_frame"] <= ctx["tl"]["total_frames"]


# ---------- fit ----------

@given(parsers.parse("a {sec:d}-second test recording at {fps:d} fps"))
def make_recording(ctx, sec, fps):
    path = ctx["tmp"] / "rec.mp4"
    ffmpeg_run(["-f", "lavfi", "-i", f"testsrc=size=320x180:rate={fps}:duration={sec}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)])
    ctx["rec"] = path


def _fit(ctx, s0, s1, frames, crop=None):
    src = s1 - s0
    speed = src / (frames / 30)
    play = max(speed, 1.0)
    clip = {"source_file": str(ctx["rec"]), "source": [s0, s1], "crop": crop, "speed": play,
            "duration_frames": frames, "freeze_frames": frames - min(frames, round(src / play * 30))}
    out = ctx["tmp"] / "clip.mp4"
    fit.render_clip(clip, 30, out)
    ctx["clip"] = out


@when(parsers.parse("I fit a clip of {s0:g} to {s1:g} seconds into {n:d} frames"))
def fit_clip(ctx, s0, s1, n):
    _fit(ctx, s0, s1, n)


@when(parsers.parse("I fit a clip of {s0:g} to {s1:g} seconds into {n:d} frames with crop {crop}"))
def fit_crop(ctx, s0, s1, n, crop):
    _fit(ctx, s0, s1, n, [int(v) for v in crop.split(",")])


@then(parsers.parse("the clip file has {n:d} frames at {fps:d} fps"))
def clip_frames(ctx, n, fps):
    assert fit.count_frames(ctx["clip"]) == n
    assert abs(probe(ctx["clip"])["fps"] - fps) < 0.01


@then(parsers.parse("the last {n:d} frames of the clip are identical"))
def frozen(ctx, n):
    # H.264 是有損壓縮：停格的重複影格解碼後仍可能差 1–2 個灰階，所以不能比雜湊值。
    # 改比相鄰影格的平均像素差：停格段要接近 0，前面有動的段落要明顯大於 0，確認這個檢查分得出差別。
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(str(ctx["clip"]))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f.astype(np.int16))
    cap.release()
    diffs = [float(np.mean(np.abs(a - b))) for a, b in zip(frames, frames[1:])]
    still = diffs[-(n - 1):]
    moving = diffs[: len(diffs) - n]
    # 實測：重複影格差約 0.003–0.01，testsrc 換格時差約 1.2
    assert max(still) < 0.1, still
    assert max(moving) > 0.5, moving


@then(parsers.parse("the clip file is {w:d}x{h:d} pixels"))
def clip_size(ctx, w, h):
    p = probe(ctx["clip"])
    assert (p["width"], p["height"]) == (w, h)
