"""本機參考影片分析的驗收測試，不下載模型。"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc import reference

scenarios("reference.feature")


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    video = tmp_path / "source.mp4"
    video.write_bytes(b"original video")
    tool = tmp_path / "isolated" / "Scripts" / "rea-video.exe"
    tool.parent.mkdir(parents=True)
    tool.write_bytes(b"tool")
    state = {"project": project, "video": video, "tool": tool, "complete": True}
    monkeypatch.setattr(reference, "probe", lambda path: {"duration": 2.0, "width": 1920, "height": 1080})
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-pass")
    monkeypatch.setenv("REA_VLM_API_KEY", "must-not-pass")

    def run(command, **kwargs):
        state["command"], state["env"] = command, kwargs["env"]
        if state.get("problem") == "timeout":
            raise subprocess.TimeoutExpired(command, 1)
        if state.get("problem") == "failure":
            return SimpleNamespace(returncode=3, stdout="", stderr="decode failure")
        out = Path(command[command.index("-o") + 1])
        if state["complete"]:
            (out / "VIDEO.md").write_text("# Reference")
            (out / "report.html").write_text("<p>Review required</p>")
            (out / "breakdown.json").write_text(json.dumps({"summary": {"shots": 2}}))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(reference.subprocess, "run", run)
    return state


@given("a local reference video and an isolated analysis tool")
def local_video(ctx):
    pass


@given(parsers.parse('the analysis input has "{problem}"'))
def problem(ctx, problem, monkeypatch):
    if problem == "missing video":
        ctx["video"].unlink()
    elif problem == "missing tool":
        ctx["tool"].unlink()
    else:
        monkeypatch.setattr(reference, "probe", lambda path: (_ for _ in ()).throw(RuntimeError("bad media")))


@given("an analysis with the same name already exists")
def existing(ctx):
    out = ctx["project"] / "work" / "references" / "ref"
    out.mkdir(parents=True)
    (out / "keep.txt").write_text("keep")


@given("the analysis tool returns incomplete output")
def incomplete(ctx):
    ctx["complete"] = False


@given(parsers.parse('the analysis tool has "{problem}"'))
def tool_problem(ctx, problem):
    ctx["problem"] = problem


@when("I analyze the reference video")
def analyze(ctx):
    try:
        ctx["result"] = reference.analyze(ctx["project"], ctx["video"], "ref", executable=ctx["tool"])
    except reference.ReferenceError as exc:
        ctx["error"] = str(exc)


@then("the analysis contains reports and the source video is unchanged")
def output(ctx):
    assert ctx["video"].read_bytes() == b"original video"
    assert (ctx["result"] / "VIDEO.md").is_file()
    manifest = json.loads((ctx["result"] / "analysis.json").read_text())
    assert manifest["review_required"] is True
    assert manifest["cloud_models"] is False


@then("cloud analysis is disabled")
def offline(ctx):
    assert "--no-vlm" in ctx["command"]
    assert "--vlm" not in ctx["command"]
    assert "GEMINI_API_KEY" not in ctx["env"]
    assert "REA_VLM_API_KEY" not in ctx["env"]


@then(parsers.parse('analysis fails with "{message}"'))
def failed(ctx, message):
    assert message in ctx["error"]
    assert "result" not in ctx
    keep = ctx["project"] / "work" / "references" / "ref" / "keep.txt"
    if keep.exists():
        assert keep.read_text() == "keep"
