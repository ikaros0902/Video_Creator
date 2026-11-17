"""features/ingest.feature 的步驟實作。測試素材在暫存資料夾即時產生。"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from pptx import Presentation
from pptx.util import Inches
from pytest_bdd import given, parsers, scenarios, then, when

from vc import ingest_ppt, ingest_rec
from vc.media import ffmpeg_run

scenarios("ingest.feature")


@pytest.fixture
def ctx(tmp_path) -> dict:
    return {"tmp": tmp_path}


# ---------- PPT ----------

@given("a 3-slide test deck")
def deck(ctx):
    tmp: Path = ctx["tmp"]
    prs = Presentation()
    s1 = prs.slides.add_slide(prs.slide_layouts[0])
    s1.shapes.title.text = "Old Tool Problems"

    s2 = prs.slides.add_slide(prs.slide_layouts[1])
    s2.shapes.title.text = "Bottlenecks"
    tf = s2.placeholders[1].text_frame
    tf.text = "Three problems"
    for t in ("Crash", "Holes"):
        p = tf.add_paragraph()
        p.text, p.level = t, 1
    s2.notes_slide.notes_text_frame.text = "Explain the three bottlenecks."

    s3 = prs.slides.add_slide(prs.slide_layouts[5])
    s3.shapes.title.text = "Settings"
    png = tmp / "pic.png"
    cv2.imwrite(str(png), np.full((32, 64, 3), 200, np.uint8))
    s3.shapes.add_picture(str(png), Inches(1), Inches(2))
    tbl = s3.shapes.add_table(2, 2, Inches(4), Inches(2), Inches(4), Inches(1)).table
    for (r, c), v in {(0, 0): "Setting", (0, 1): "Value", (1, 0): "Max thickness", (1, 1): "3.0"}.items():
        tbl.cell(r, c).text = v

    path = tmp / "deck.pptx"
    prs.save(str(path))
    ctx["pptx"] = path


@when("I extract the deck")
def extract_deck(ctx):
    ctx["out"] = ctx["tmp"] / "work"
    ctx["deck"] = ingest_ppt.extract(ctx["pptx"], ctx["out"])


@then(parsers.parse("the result has {n:d} slides"))
def n_slides(ctx, n):
    assert len(ctx["deck"]["slides"]) == n


@then(parsers.parse('slide {i:d} has the title "{title}"'))
def slide_title(ctx, i, title):
    assert ctx["deck"]["slides"][i - 1]["title"] == title


@then(parsers.parse('slide {i:d} has paragraph levels "{levels}"'))
def slide_levels(ctx, i, levels):
    body = [t for t in ctx["deck"]["slides"][i - 1]["texts"] if not t["is_title"]]
    got = [p["level"] for p in body[0]["paragraphs"]]
    assert got == [int(x) for x in levels.split(",")]


@then(parsers.parse('slide {i:d} has the notes "{notes}"'))
def slide_notes(ctx, i, notes):
    assert ctx["deck"]["slides"][i - 1]["notes"] == notes


@then(parsers.parse("slide {i:d} has {n:d} picture that exists on disk with size {w:d}x{h:d}"))
def slide_picture(ctx, i, n, w, h):
    pics = ctx["deck"]["slides"][i - 1]["pictures"]
    assert len(pics) == n
    assert (ctx["out"] / pics[0]["file"]).is_file()
    assert pics[0]["px"] == [w, h]


@then(parsers.parse('slide {i:d} has a table with first row "{row}"'))
def slide_table(ctx, i, row):
    assert ctx["deck"]["slides"][i - 1]["tables"][0]["rows"][0] == row.split(",")


# ---------- 錄影 ----------

@given("a 6-second test video with 3 solid-color parts and no audio")
def color_video(ctx):
    path = ctx["tmp"] / "colors.mp4"
    srcs = []
    for c in ("red", "green", "blue"):
        srcs += ["-f", "lavfi", "-i", f"color=c={c}:s=320x180:d=2:r=30"]
    ffmpeg_run([*srcs, "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]", "-map", "[v]",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)])
    ctx["video"] = path


@given("a 2-second test video with a sine tone")
def tone_video(ctx):
    path = ctx["tmp"] / "tone.mp4"
    ffmpeg_run(["-f", "lavfi", "-i", "color=c=gray:s=320x180:d=2:r=30",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)])
    ctx["video"] = path


@when(parsers.parse("I analyze the recording with a thumbnail every {every:g} second"))
def analyze_rec(ctx, every):
    out = ctx["tmp"] / "work" / "recordings" / "rec01"
    r = ingest_rec.analyze(ctx["video"], out, "rec01", every=every)
    r["active_ranges"] = ingest_rec.active_ranges(r["activity"], r["activity_step_s"])
    ctx["rec"], ctx["rec_dir"] = r, out


@then(parsers.parse("the duration is {d:g} seconds within {tol:g}"))
def duration_is(ctx, d, tol):
    assert abs(ctx["rec"]["probe"]["duration"] - d) <= tol


@then(parsers.parse("{n:d} scenes are found"))
def scenes_found(ctx, n):
    assert len(ctx["rec"]["scenes"]) == n


@then(parsers.parse("{n:d} thumbnails and {m:d} contact sheet are written"))
def thumbs_written(ctx, n, m):
    assert len(ctx["rec"]["thumbs"]) == n
    assert len(ctx["rec"]["sheets"]) == m
    for t in ctx["rec"]["thumbs"]:
        assert (ctx["rec_dir"] / t["file"]).is_file()


@then(parsers.parse("activity is found only near {a:d} and {b:d} seconds"))
def activity_near(ctx, a, b):
    ranges = ctx["rec"]["active_ranges"]
    assert len(ranges) == 2, ranges
    for (lo, hi), t in zip(ranges, (a, b)):
        assert lo - 0.5 <= t <= hi + 0.5, ranges


@then("the recording has no audio")
def no_audio(ctx):
    assert ctx["rec"]["probe"]["has_audio"] is False
    assert ctx["rec"]["mean_volume_db"] is None


@then(parsers.parse("the recording has audio with a mean volume above {db:g} dB"))
def has_audio(ctx, db):
    assert ctx["rec"]["probe"]["has_audio"] is True
    assert ctx["rec"]["mean_volume_db"] > db
