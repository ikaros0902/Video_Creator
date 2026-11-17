"""自定義風格、運鏡與技能輔助腳本的行為檢查。"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from vc.camera import scene_camera, validate_camera_plan
from vc.hf_scenes import render_all, render_scene_html
from vc.style_config import PRESETS, contrast_ratio, load_style, project_visual_settings, validate_style
from vc.tools import ROOT

scenarios("custom_styles.feature")


def title_context():
    return {"scene_id": "s01", "comp_id": "s01-public", "duration": 4.5, "fps": 30,
            "data": {"title": "A clear result", "subtitle": "Trace each claim", "at_word": "claim"},
            "at_frames": {"claim": 45}, "images": {"list": []}}


def dolly_plan():
    return {"shots": [{"scene_ref": "s01", "shot_id": "a", "start_time_s": 0,
                       "end_time_s": 4.5, "camera_motion": {"type": "dolly_in", "end_scale": 1.1}}]}


@pytest.fixture
def ctx():
    return {}


@given("a title scene with a fixed camera")
def title(ctx):
    ctx["scene"] = title_context()


@when("I render the scene with two valid style presets")
def themes(ctx):
    ctx["navy"] = render_scene_html("title", ctx["scene"], load_style("executive_navy"))
    ctx["swiss"] = render_scene_html("title", ctx["scene"], load_style("swiss_kinetic"))


@then("the palette and surface tokens differ")
def different(ctx):
    assert "background-color: #0B1220" in ctx["navy"]
    assert "background-color: #F8F7F4" in ctx["swiss"]
    assert "border-radius: 18px" in ctx["navy"]
    assert "border-radius: 0px" in ctx["swiss"]


@then("the narration timing stays unchanged")
def timing(ctx):
    for html in (ctx["navy"], ctx["swiss"]):
        assert 'show("#sub", 1.5);' in html
        assert 'data-duration="4.5"' in html


@given("a style with low text contrast or invalid CSS values")
def invalid_style(ctx):
    ctx["style"] = load_style()
    ctx["style"]["tokens"]["colors"]["text_primary"] = "#0B1220"


@when("I validate the style")
def validate(ctx):
    with pytest.raises(ValueError) as error:
        validate_style(ctx["style"])
    ctx["error"] = str(error.value)


@then("validation fails with an actionable error")
def error(ctx):
    assert "contrast to at least 4.5:1" in ctx["error"]


@given("a scene with a valid dolly shot")
def dolly(ctx):
    ctx["plan"] = dolly_plan()


@when("I generate its HyperFrames composition")
def camera_render(ctx):
    ctx["html"] = render_scene_html("title", title_context(), camera_config=ctx["plan"])


@then("its paused timeline contains the requested camera transform")
def transform(ctx):
    assert 'gsap.timeline({ paused: true })' in ctx["html"]
    assert '"end_scale": 1.1' in ctx["html"]
    assert 'tl.fromTo("#camera", from, to, shot.start_time_s)' in ctx["html"]


@then("invalid shot timing fails before generation")
def invalid_timing(ctx):
    ctx["plan"]["shots"][0]["end_time_s"] = 5.0
    with pytest.raises(ValueError, match="inside scene"):
        render_scene_html("title", title_context(), camera_config=ctx["plan"])


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_text_contrast(preset):
    colors = load_style(preset)["tokens"]["colors"]
    for front in ("text_primary", "text_secondary", "accent", "positive", "negative"):
        for back in ("background", "surface"):
            assert contrast_ratio(colors[front], colors[back]) >= 4.5


@pytest.mark.parametrize("section,key,value", [
    ("colors", "accent", "red;}</style><script>bad()</script>"),
    ("typography", "body_font", "Arial; background:url(https://bad.invalid)"),
    ("surface", "card_corner_radius", float("nan")),
    ("surface", "border_width", True),
    ("spacing", "safe_margin_px", -1),
])
def test_invalid_tokens_fail(section, key, value):
    style = load_style()
    style["tokens"][section][key] = value
    with pytest.raises(ValueError):
        validate_style(style)


def test_project_settings_resolve_local_style_and_plan(tmp_path):
    (tmp_path / "style.json").write_text(json.dumps(load_style("swiss_kinetic")), encoding="utf-8")
    (tmp_path / "camera.json").write_text(json.dumps(dolly_plan()), encoding="utf-8")
    (tmp_path / "project.yaml").write_text("style: style.json\ncamera_mode: cinematic\ncamera_plan: camera.json\n", encoding="utf-8")
    style, camera = project_visual_settings(tmp_path)
    assert style["theme_id"] == "swiss_kinetic"
    assert scene_camera(camera, "s01", 4.5)[0]["camera_motion"]["end_scale"] == 1.1


@pytest.mark.parametrize("settings", ["style: missing\n", "style: ../outside.json\n", "camera_mode: teleport\n", "camera_plan: ../outside.json\n"])
def test_invalid_project_settings_fail(tmp_path, settings):
    (tmp_path / "project.yaml").write_text(settings, encoding="utf-8")
    with pytest.raises(ValueError):
        project_visual_settings(tmp_path)


def test_text_is_escaped():
    ctx = title_context()
    ctx["data"]["title"] = '<script>alert("bad")</script>'
    html = render_scene_html("title", ctx)
    assert '<script>alert("bad")</script>' not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize("duration", [0, -1, True, float("nan")])
def test_invalid_duration_fails(duration):
    ctx = title_context()
    ctx["duration"] = duration
    with pytest.raises(ValueError):
        render_scene_html("title", ctx)


def test_camera_overlap_and_missing_target_fail():
    plan = dolly_plan()
    plan["shots"].append(copy.deepcopy(plan["shots"][0]))
    plan["shots"][1]["shot_id"] = "b"
    with pytest.raises(ValueError, match="overlap"):
        validate_camera_plan(plan)
    plan = dolly_plan()
    plan["shots"][0]["camera_motion"] = {"type": "focus_target", "target_selector": "#missing"}
    with pytest.raises(ValueError, match="target does not exist"):
        render_scene_html("title", title_context(), camera_config=plan)


def test_auto_camera_modes_preserve_duration():
    assert scene_camera({"shots": [], "mode": "fixed"}, "s01", 8) == []
    for mode, motion in (("dynamic", "pan_horizontal"), ("cinematic", "dolly_in")):
        shot = scene_camera({"shots": [], "mode": mode}, "s01", 8)[0]
        assert shot["camera_motion"]["type"] == motion
        assert shot["end_time_s"] == 8


def test_skill_copywriting_cli_rejects_bad_text(tmp_path):
    path = tmp_path / "script.json"
    path.write_text(json.dumps({"scenes": [{"narration": "使用GPU,提供顛覆性體驗。"}]}), encoding="utf-8")
    for name in ("lint_copywriting", "scan_ai_slop"):
        result = subprocess.run([sys.executable, str(ROOT / "skills/script-copywriter/scripts" / f"{name}.py"), str(path)], capture_output=True, text=True)
        assert result.returncode == 1
        assert json.loads(result.stdout)["valid"] is False


def test_skill_copywriting_cli_accepts_concrete_text(tmp_path):
    path = tmp_path / "script.json"
    path.write_text(json.dumps({"scenes": [{"narration": "使用 GPU 渲染影片。"}]}), encoding="utf-8")
    for name in ("lint_copywriting", "scan_ai_slop"):
        result = subprocess.run([sys.executable, str(ROOT / "skills/script-copywriter/scripts" / f"{name}.py"), str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_camera_audit_cli_rejects_short_shot(tmp_path):
    path = tmp_path / "camera.json"
    plan = dolly_plan()
    plan["shots"][0]["end_time_s"] = 0.8
    path.write_text(json.dumps(plan), encoding="utf-8")
    result = subprocess.run([sys.executable, str(ROOT / "skills/camera-pacing-director/scripts/audit_shot_pacing.py"), str(path)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "1.5 to 5.5" in result.stdout


def test_beat_alignment_preserves_valid_spacing():
    path = ROOT / "skills/camera-pacing-director/scripts/beat_sync_aligner.py"
    spec = importlib.util.spec_from_file_location("beat_aligner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    aligned = module.align(dolly_plan(), [4.55])
    assert aligned["shots"][0]["end_time_s"] == 4.55
    assert dolly_plan()["shots"][0]["end_time_s"] == 4.5


@pytest.mark.parametrize("anchors,expected_time", [
    ({"claim": None, "recording_only": None}, 0.6),
    ({"claim": 45, "recording_only": None}, 1.5),
    ({"claim": 0, "recording_only": None}, 0.0),
])
def test_unaligned_anchors_keep_fallback_and_valid_timing(anchors, expected_time):
    context = title_context()
    context["at_frames"] = anchors
    html = render_scene_html("title", context)
    assert f'show("#sub", {expected_time});' in html
    assert 'data-duration="4.5"' in html


@pytest.mark.parametrize("internal,public", [
    ("recording", "recording"), ("manim", "manim"),
    ("recording", "anim"), ("anim", "manim"),
])
def test_camera_plan_rejects_unsupported_variants_before_render(tmp_path, internal, public):
    (tmp_path / "project.yaml").write_text("camera_plan: camera.json\n", encoding="utf-8")
    (tmp_path / "camera.json").write_text(json.dumps(dolly_plan()), encoding="utf-8")
    timeline = {"fps": 30, "scenes": [{"id": "s01", "visuals": {
        "internal": {"kind": internal}, "public": {"kind": public},
    }}]}
    with pytest.raises(ValueError, match="Camera plans support only anim scenes") as error:
        render_all(timeline, tmp_path / "work", use_gpu=False)
    assert "s01/" in str(error.value)
    assert not (tmp_path / "work" / "hf").exists()


@pytest.mark.parametrize("margin", [60, 160])
@pytest.mark.parametrize("template", ["title", "cards3"])
def test_safe_margin_changes_actual_title_and_content_positions(margin, template):
    style = load_style()
    style["tokens"]["spacing"]["safe_margin_px"] = margin
    context = title_context()
    if template == "cards3":
        context["data"] = {"heading": "Evidence", "cards": [{"title": "Claim", "label": "Source"}],
                           "inset": {"drawing": "hole_in_plate"}}
        expected = {"head": margin, "card0": margin}
    else:
        expected = {"title": margin + 40, "bar": margin + 40, "sub": margin + 44}
    html = render_scene_html(template, context, style)
    for element_id, left in expected.items():
        match = re.search(rf'<div id="{element_id}"[^>]+style="([^"]+)"', html)
        assert match, element_id
        assert f"left:{left}px;" in match.group(1)


@pytest.mark.parametrize("margin", [120, 160])
@pytest.mark.parametrize("template", ["cards3", "steps4", "result", "vs_intro_mock", "chassis_mock", "demo_mock", "concept", "title"])
def test_primary_content_stays_inside_both_safe_margins(margin, template):
    style = load_style()
    style["tokens"]["spacing"]["safe_margin_px"] = margin
    context = title_context()
    common_inset = {"drawing": "hole_in_plate", "caption": "Illustration"}
    inputs = {
        "cards3": ({"heading": "Evidence", "cards": [{"title": "Claim", "label": "Source"}] * 3,
                    "inset": common_inset}, ["card0", "card1", "card2", "inset", "icap"]),
        "steps4": ({"heading": "Process", "steps": [{"title": "Step", "label": "Action"}] * 4,
                    "inset": common_inset}, ["step0", "step1", "step2", "step3", "inset", "icap"]),
        "result": ({"after": {"value": "3", "label": "After"}, "before": {"value": "4", "label": "Before"},
                    "footnote": "Source"}, ["after", "before", "outro"]),
        "vs_intro_mock": ({"title": "Compare", "subtitle": "Two methods"}, ["panel_left", "panel_right"]),
        "chassis_mock": ({"title": "Assembly", "result_line": "Complete"}, ["chassis", "info_card"]),
        "demo_mock": ({"steps": [{"title": "Step"}] * 3, "result_line": "Complete"},
                      ["win", "art", "chip0", "chip1", "chip2", "bar", "fill", "res"]),
        "concept": ({"labels": ["Solid", "Shell"]}, ["art"]),
        "title": (context["data"], ["bar"]),
    }
    context["data"], block_ids = inputs[template]
    html = render_scene_html(template, context, style)
    for block_id in block_ids:
        match = re.search(rf'<div id="{block_id}"[^>]+style="([^"]+)"', html)
        assert match, block_id
        left_match = re.search(r"(?:^|;)left:([0-9.]+)px;", match.group(1))
        width_match = re.search(r"(?:^|;)width:([0-9.]+)px;", match.group(1))
        assert left_match and width_match, block_id
        left, width = float(left_match.group(1)), float(width_match.group(1))
        assert left >= margin, (template, block_id, left, margin)
        assert left + width <= 1920 - margin + 1e-7, (template, block_id, left + width, 1920 - margin)
