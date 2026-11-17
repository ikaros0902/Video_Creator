"""tests/test_verify_tools.py

針對 scripts/verify_tools.py 進行完整功能驗證與邊界測試。
涵蓋 JSON Schema 測試、Exit Code 邊界測試、Mock 測試以及本機 Rust 工具整合測試。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 將專案根目錄加入模組搜尋路徑
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_tools import ToolResult, ToolVerifier, main


def test_tool_result_dataclass():
    """驗證 ToolResult 結構化資料之正確性與欄位型別。"""
    res = ToolResult(
        name="test_tool",
        category="Core",
        status="PASS",
        version="1.0.0",
        required=True,
        latency_ms=12.5,
        detail="OK",
        fix_hint="",
    )
    d = res.__dict__
    assert d["name"] == "test_tool"
    assert d["category"] == "Core"
    assert d["status"] == "PASS"
    assert d["version"] == "1.0.0"
    assert d["required"] is True
    assert d["latency_ms"] == 12.5
    assert d["detail"] == "OK"
    assert d["fix_hint"] == ""


def test_verify_tools_cli_json(capsys):
    """驗證 --json 輸出符合標準 JSON Schema 且結構完整。"""
    ret = main(["--json"])
    assert ret == 0  # 目前環境下所有 required 通過，應返回 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert "summary" in data
    assert "tools" in data

    summary = data["summary"]
    assert "total" in summary
    assert "passed" in summary
    assert "warnings" in summary
    assert "failed" in summary
    assert "ok" in summary
    assert summary["ok"] is True
    assert summary["failed"] == 0
    assert len(data["tools"]) >= 10

    # 檢查工具條目必備欄位
    tool_names = [t["name"] for t in data["tools"]]
    assert "python" in tool_names
    assert "node" in tool_names
    assert "ffmpeg" in tool_names
    assert "DeckCraft" in tool_names
    assert "EffectCraft" in tool_names
    assert "PhotoCraft" in tool_names
    assert "VectorCraft" in tool_names
    assert "pyJianYingDraft" in tool_names
    assert "craft_tools.py" in tool_names


def test_verify_tools_exit_code_zero_on_required_pass():
    """當所有 required=True 工具正常時，即使有 WARN 亦必須傳回 Exit Code 0。"""
    verifier = ToolVerifier()
    with patch.object(verifier, "check_python", return_value=ToolResult("python", "Core", "PASS", "3.11", True, 1.0, "OK")), \
         patch.object(verifier, "check_node", return_value=ToolResult("node", "Core", "PASS", "v26", True, 1.0, "OK")), \
         patch.object(verifier, "check_ffmpeg", return_value=ToolResult("ffmpeg", "Core", "PASS", "9.0", True, 1.0, "OK")):
        results = verifier.run_all()
        failed_required = [r for r in results if r.required and r.status == "FAIL"]
        assert len(failed_required) == 0


def test_verify_tools_exit_code_one_on_required_fail(capsys):
    """當任一 required=True 工具缺失時，必須傳回 Exit Code 1。"""
    verifier = ToolVerifier()
    mock_fail = ToolResult("ffmpeg", "Core", "FAIL", "N/A", True, 1.0, "Missing")
    with patch.object(verifier, "check_ffmpeg", return_value=mock_fail):
        with patch("scripts.verify_tools.ToolVerifier", return_value=verifier):
            ret = main([])
            assert ret == 1
            captured = capsys.readouterr()
            assert "[錯誤]" in captured.out or "[錯誤]" in captured.err or "ffmpeg" in captured.out


def test_craft_tools_module_integration():
    """驗證 vc.craft_tools 與 tools.craft_tools 模組可正確載入並診斷本機四大工具。"""
    import vc.craft_tools as vct
    import tools.craft_tools as tct

    report = vct.diagnose_craft_tools()
    assert "DeckCraft" in report
    assert "EffectCraft" in report
    assert "PhotoCraft" in report
    assert "VectorCraft" in report

    # 本機環境已具備這 4 大工具
    for name in ("DeckCraft", "EffectCraft", "PhotoCraft", "VectorCraft"):
        assert report[name]["available"] is True, f"{name} 應為可用狀態"
        assert report[name]["path"] is not None

    # tools.craft_tools 應導出相同 API
    assert hasattr(tct, "deck_render_slides")
    assert hasattr(tct, "effect_render_frame")
    assert hasattr(tct, "photo_convert")
    assert hasattr(tct, "vector_convert")
