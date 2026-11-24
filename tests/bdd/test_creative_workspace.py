"""驗證本機設計資料的來源、預覽及可還原儲存。"""
import json

import yaml
from pytest_bdd import given, parsers, scenarios, then, when

from vc.creative import apply_style, import_reference, preview, save_brief
from vc.style_config import load_style

scenarios("creative_workspace.feature")


@given("a creative project", target_fixture="creative")
def creative_project(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "project.yaml").write_text("name: example\nstyle: executive_navy\n", encoding="utf-8")
    (root / "script.json").write_text(json.dumps({"meta": {"title": "Demo"}, "scenes": [
        {"id": "s01", "narration": "A useful explanation.", "visual": {"data": {"title": "Demo"}}}
    ]}), encoding="utf-8")
    return {"root": root, "result": None}


def operation(ctx, action):
    try:
        ctx["value"] = action()
        ctx["result"] = "saved"
    except (ValueError, FileNotFoundError):
        ctx["result"] = "rejected"


@when(parsers.re(r'I save a brief with audience "(?P<audience>[^"]*)" and purpose "(?P<purpose>[^"]*)"'))
def brief(creative, audience, purpose):
    operation(creative, lambda: save_brief(creative["root"], {
        "audience": audience, "purpose": purpose, "message": "Explain the result", "avoid": []}))


@when(parsers.parse('I import a reference of type "{kind}"'))
def reference(creative, kind):
    source = creative["root"].parent / ("image.png" if kind == "image" else "program.exe")
    if kind != "missing":
        source.write_bytes(b"reference bytes")
    operation(creative, lambda: import_reference(creative["root"], source, "Original", "https://example.com", "Human note", ["layout"]))


@when("I import the same reference twice")
def import_twice(creative):
    source = creative["root"].parent / "image.png"
    source.write_bytes(b"reference bytes")
    creative["records"] = [import_reference(creative["root"], source, "Original", "local", note, [])
                           for note in ("first note", "second note")]


@then("both source records preserve their notes and asset bytes")
def distinct_records(creative):
    first, second = creative["records"]
    assert first["id"] != second["id"]
    assert [r["notes"] for r in (first, second)] == ["first note", "second note"]
    for record in (first, second):
        assert (creative["root"] / "design" / "library" / record["id"] / record["asset"]).read_bytes() == b"reference bytes"
        assert record["provenance"] == "user"


@when(parsers.parse('I apply a style with condition "{condition}"'))
def style_choice(creative, condition):
    style = load_style()
    if condition == "low contrast":
        style["tokens"]["colors"]["text_primary"] = style["tokens"]["colors"]["background"]
    elif condition == "small text":
        style["tokens"]["typography"]["base_size_px"] = 2
    operation(creative, lambda: apply_style(creative["root"], style, "Clear hierarchy"))


@when("I apply two valid style choices")
def two_styles(creative):
    apply_style(creative["root"], load_style(), "First")
    creative["old_style"] = (creative["root"] / "design/style.json").read_bytes()
    apply_style(creative["root"], load_style("swiss_kinetic"), "Second")


@then("the previous style and project settings have backups")
def style_backups(creative):
    backups = list((creative["root"] / "design/backups").glob("*/style.json"))
    assert any(path.read_bytes() == creative["old_style"] for path in backups)
    assert list((creative["root"] / "design/backups").glob("*/project.yaml"))
    assert yaml.safe_load((creative["root"] / "project.yaml").read_text())["style"] == "design/style.json"


@when(parsers.parse('I preview the scene with condition "{condition}"'))
def scene_preview(creative, condition):
    operation(creative, lambda: preview(creative["root"], "missing" if condition == "unknown scene" else "s01",
                                       ["invalid" if condition == "invalid style" else "executive_navy"]))


@when("I preview a scene that contains HTML markup")
def html_preview(creative):
    script_path = creative["root"] / "script.json"
    data = json.loads(script_path.read_text())
    data["scenes"][0]["narration"] = "<script>alert(1)</script>"
    script_path.write_text(json.dumps(data), encoding="utf-8")
    creative["before"] = {p.name: p.read_bytes() for p in (script_path, creative["root"] / "project.yaml")}
    creative["preview"] = preview(creative["root"], "s01", ["executive_navy", "swiss_kinetic", "blueprint"])


@then("the preview preserves the input files and escapes the markup")
def safe_preview(creative):
    for name, content in creative["before"].items():
        assert (creative["root"] / name).read_bytes() == content
    content = creative["preview"].read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in content
    assert "\\u003cscript>" in content
    assert '"blueprint"' in content


@then(parsers.parse('the creative operation is "{result}"'))
def result(creative, result):
    assert creative["result"] == result
