"""features/align.feature 的步驟實作。用合成的 Whisper 逐字結果測試，不需要 GPU。"""
from __future__ import annotations

import re

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc import align

scenarios("align.feature")


@pytest.fixture
def ctx() -> dict:
    return {}


@when(parsers.parse('I compare the reference "{ref}" with the transcript "{hyp}"'))
def compare(ctx, ref, hyp):
    ctx["wer"] = align.wer(ref, hyp)
    ctx["diff"] = align.diff_words(ref, hyp)


@then(parsers.parse("the word error rate is {value:g}"))
def wer_is(ctx, value):
    assert ctx["wer"] == pytest.approx(value)


@then(parsers.parse("the word error rate is above {value:g}"))
def wer_above(ctx, value):
    assert ctx["wer"] > value


@then(parsers.parse('the difference list contains "{word}"'))
def diff_contains(ctx, word):
    assert any(word in d for d in ctx["diff"]), ctx["diff"]


@given(parsers.parse('the narration "{text}" with lexicon "{src}" as "{dst}"'))
def narration_lex(ctx, text, src, dst):
    ctx["narration"], ctx["lexicon"] = text, {src: dst}


@given(parsers.parse('the narration "{text}" with no lexicon'))
def narration_plain(ctx, text):
    ctx["narration"], ctx["lexicon"] = text, {}


def _timed(words: list[str], per: float) -> list[dict]:
    return [{"word": w, "start": round(i * per, 3), "end": round((i + 1) * per, 3)} for i, w in enumerate(words)]


@given(parsers.parse('Whisper heard "{words}" with {per:g} seconds per word'))
def heard(ctx, words, per):
    ctx["whisper"] = _timed(words.split("|"), per)


@given(parsers.parse("Whisper heard each narration word with {per:g} seconds per word"))
def heard_all(ctx, per):
    ctx["whisper"] = _timed(ctx["narration"].split(), per)


@when("I align the words")
def do_align(ctx):
    ctx["words"] = align.align_words(ctx["narration"], ctx["lexicon"], ctx["whisper"])


@when("I make captions")
def do_cues(ctx):
    ctx["cues"] = align.make_cues(ctx["words"])


@when(parsers.parse("I format {t:g} seconds as an SRT time"))
def fmt(ctx, t):
    ctx["srt"] = align.srt_time(t)


@then("every narration word has a start time and an end time")
def all_timed(ctx):
    assert len(ctx["words"]) == len(ctx["narration"].split())
    assert all(w["start"] is not None and w["end"] >= w["start"] for w in ctx["words"])


@then("the start times never go backward")
def monotonic(ctx):
    starts = [w["start"] for w in ctx["words"]]
    assert starts == sorted(starts), starts


@then(parsers.parse('the word "{word}" starts at {t:g} seconds within {tol:g}'))
def word_start(ctx, word, t, tol):
    w = next(x for x in ctx["words"] if x["word"].strip(".,") == word)
    assert abs(w["start"] - t) <= tol, w


@then(parsers.parse('the callout word "{word}" starts at {t:g} seconds within {tol:g}'))
def callout_start(ctx, word, t, tol):
    assert abs(align.find_word_time(ctx["words"], word) - t) <= tol


@then(parsers.parse("no caption is longer than {n:d} characters"))
def cue_len(ctx, n):
    assert all(len(c["text"]) <= n for c in ctx["cues"]), [c["text"] for c in ctx["cues"]]


@then("no caption crosses a sentence end")
def cue_sentence(ctx):
    for c in ctx["cues"]:
        assert not re.search(r"[.!?]\s", c["text"]), c["text"]


@then(parsers.parse("every caption lasts at least {s:g} second"))
def cue_min(ctx, s):
    assert all(c["end"] - c["start"] >= s for c in ctx["cues"]), ctx["cues"]


@then(parsers.parse("every caption has at least {n:d} words"))
def cue_words(ctx, n):
    assert all(len(c["text"].split()) >= n for c in ctx["cues"]), [c["text"] for c in ctx["cues"]]


@then('no caption ends with "a", "the", "of", or "and" unless the sentence ends there')
def cue_weak_end(ctx):
    for c in ctx["cues"]:
        assert c["text"].split()[-1].lower() not in {"a", "the", "of", "and"}, c["text"]


@then(parsers.parse('the SRT time is "{text}"'))
def srt_is(ctx, text):
    assert ctx["srt"] == text
