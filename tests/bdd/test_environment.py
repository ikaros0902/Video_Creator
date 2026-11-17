"""features/environment.feature 的步驟實作。"""
from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from vc import doctor
from vc.doctor import Check

scenarios("environment.feature")


@pytest.fixture
def ctx() -> dict:
    return {}


@given(parsers.parse('the tool "{name}" cannot be found'))
def tool_missing(monkeypatch, name):
    # 只讓指定工具找不到，其他工具維持真實查找
    real = doctor.find_tool
    monkeypatch.setattr(doctor, "find_tool", lambda n: None if n == name else real(n))


@when(parsers.parse('I check the tool "{name}"'))
def check_tool(ctx, name):
    ctx["result"] = doctor.check_version_tool(name, ["-version"], doctor.SETUP_HINT)


@given("the check results contain a required item that failed")
def results_required_failed(monkeypatch):
    fake = [Check("a", True, ""), Check("b", False, "", "fix", required=True)]
    monkeypatch.setattr(doctor, "collect", lambda deep=False: fake)


@given("the check results contain only an optional item that failed")
def results_optional_failed(monkeypatch):
    fake = [Check("a", True, ""), Check("b", False, "", "fix", required=False)]
    monkeypatch.setattr(doctor, "collect", lambda deep=False: fake)


@when('I run "vc doctor"')
def run_doctor(ctx):
    ctx["exit"] = doctor.main([])


@when(parsers.parse("I check Python version {major:d}.{minor:d}"))
def check_python_version(ctx, major, minor):
    ctx["result"] = doctor.check_python((major, minor))


@when(parsers.parse('I parse the version text "{text}"'))
def parse_version(ctx, text):
    ctx["major"] = doctor.parse_major(text)


@then(parsers.parse('the status is "{status}"'))
def status_is(ctx, status):
    assert ctx["result"].status == status


@then("the result shows a fix")
def shows_fix(ctx):
    assert ctx["result"].fix


@then(parsers.parse("the exit code is {code:d}"))
def exit_code_is(ctx, code):
    assert ctx["exit"] == code


@then(parsers.parse("the major version is {major:d}"))
def major_is(ctx, major):
    assert ctx["major"] == major


@when("I inspect detected FFmpeg GPU encoders")
def inspect_gpu_encoders(ctx):
    from vc import media
    ctx["gpu_encoders"] = media.gpu_encoders()
    ctx["hw_candidates"] = set(media.HW_ENCODERS)


@then("every detected encoder is a known hardware H264 codec")
def check_hw_encoders(ctx):
    assert set(ctx["gpu_encoders"]) <= ctx["hw_candidates"]
