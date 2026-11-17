"""features/voice.feature 的步驟實作。假後端產生正弦波，長度依字數決定，不需要網路或 GPU。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from pytest_bdd import given, parsers, scenarios, then, when

from vc import voice
from vc.project import resolve_project_dir
from vc.script import load_script
from vc.tools import ROOT

scenarios("voice.feature")


@dataclass
class FakeBackend:
    voice: str = "fake"
    rate: str = "+0%"
    engine: str = "fake"
    calls: list[str] = field(default_factory=list)

    def synth(self, text: str, out_wav: Path) -> None:
        self.calls.append(text)
        dur = 0.3 * len(text.split())
        t = np.arange(int(24000 * dur)) / 24000
        tmp = out_wav.with_name(out_wav.stem + "_src.wav")
        sf.write(str(tmp), 0.2 * np.sin(2 * np.pi * 220 * t), 24000)
        voice._to_wav48(tmp, out_wav)   # 走真實的轉檔流程，確認輸出格式
        tmp.unlink()


@pytest.fixture
def ctx(tmp_path) -> dict:
    return {"work": tmp_path / "work"}


@given("the sample script")
def script(ctx):
    ctx["script"] = load_script(resolve_project_dir("_sample") / "script.json")


@given("a fake TTS backend")
def fake(ctx):
    ctx["backend"] = FakeBackend()


@given("the narration audio was generated once")
def generated_once(ctx):
    voice.generate(ctx["script"], ctx["backend"], ctx["work"])


@when(parsers.parse('scene "{sid}" narration is "{text}"'))
def set_narration(ctx, sid, text):
    next(s for s in ctx["script"].scenes if s.id == sid).narration = text


@when(parsers.parse('the fake backend voice is "{name}"'))
def set_voice(ctx, name):
    ctx["backend"].voice = name


@when("I generate the narration audio")
def gen(ctx):
    ctx["manifest"] = voice.generate(ctx["script"], ctx["backend"], ctx["work"])


@when(parsers.parse("I make the preview with a {gap:g} second gap"))
def make_preview(ctx, gap):
    ctx["gap"] = gap
    ctx["preview"] = voice.preview(ctx["manifest"], voice.voice_dir(ctx["work"], ctx["backend"]), gap)


@given(parsers.parse("a WAV file with {a:g} seconds of silence, {b:g} second of tone, and {c:g} seconds of silence"))
def padded_wav(ctx, a, b, c):
    sr = 48000
    t = np.arange(int(sr * b)) / sr
    tone = 0.3 * np.sin(2 * np.pi * 220 * t)
    data = np.concatenate([np.zeros(int(sr * a)), tone, np.zeros(int(sr * c))])
    ctx["wav"] = ctx["work"].parent / "padded.wav"
    sf.write(str(ctx["wav"]), data, sr, subtype="PCM_16")


@when("I trim the silence")
def do_trim(ctx):
    voice.trim_silence(ctx["wav"])


@then(parsers.parse("the WAV file lasts {d:g} seconds within {tol:g}"))
def wav_len(ctx, d, tol):
    assert abs(voice.wav_duration(ctx["wav"]) - d) <= tol


@then(parsers.parse('the spoken text of scene "{sid}" contains "{text}"'))
def spoken_contains(ctx, sid, text):
    assert text in ctx["manifest"]["scenes"][sid]["spoken"]


@then(parsers.parse('the narration of scene "{sid}" still contains "{text}"'))
def narration_contains(ctx, sid, text):
    assert text in ctx["manifest"]["scenes"][sid]["narration"]


@then(parsers.parse("every scene has a WAV file at {sr:d} Hz with {ch:d} channel"))
def wav_format(ctx, sr, ch):
    d = voice.voice_dir(ctx["work"], ctx["backend"])
    for sc in ctx["manifest"]["scenes"].values():
        info = sf.info(str(d / sc["file"]))
        assert (info.samplerate, info.channels) == (sr, ch)


@then("every scene duration in the manifest matches its WAV file")
def durations_match(ctx):
    d = voice.voice_dir(ctx["work"], ctx["backend"])
    for sc in ctx["manifest"]["scenes"].values():
        assert abs(voice.wav_duration(d / sc["file"]) - sc["duration_s"]) < 0.002


@then(parsers.parse('only scene "{sid}" is generated again'))
def only_one(ctx, sid):
    assert ctx["manifest"]["generated"] == [sid]


@then(parsers.parse("all {n:d} scenes are generated"))
def all_generated(ctx, n):
    assert len(ctx["manifest"]["generated"]) == n


@then(parsers.parse("the preview length equals the total scene length plus {n:d} gaps, within {tol:g} seconds"))
def preview_len(ctx, n, tol):
    expected = ctx["manifest"]["total_s"] + n * ctx["gap"]
    assert abs(voice.wav_duration(ctx["preview"]) - expected) <= tol
