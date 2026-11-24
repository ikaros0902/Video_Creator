"""tests/test_milestone4_showcase.py

Milestone 4 驗收測試套件：
涵蓋 F16 (自包含範例輸入資料建置)、F17 (多風格與運鏡參數切換實測)、
以及 F18 (端到端管線走通與標準化產物結構稽核)。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from vc.hf_scenes import render_scene_html
from vc.media import probe
from vc.project import load_project
from vc.script import load_facts, load_script
from vc.style_config import load_style

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = Path(os.environ.get("VC_SHOWCASE_PROJECT", str(REPO_ROOT / "projects" / "demo_showcase"))).resolve()


class TestMilestone4Showcase:
    """Milestone 4 驗收測試集合。"""

    # --- Feature 16: 自包含範例輸入資料建置 ---

    @pytest.mark.integration
    def test_f16_input_directory_structure_and_files(self):
        """驗證 demo_showcase 輸入目錄結構完整性且檔案皆為非 0-byte 真實素材。"""
        assert DEMO_DIR.is_dir(), f"專案目錄不存在：{DEMO_DIR}"

        pptx_file = DEMO_DIR / "input" / "slides" / "showcase.pptx"
        rec_file = DEMO_DIR / "input" / "recordings" / "rec01.mp4"
        bgm_file = DEMO_DIR / "input" / "audio" / "bgm.mp3"
        logo_file = DEMO_DIR / "input" / "assets" / "logo.png"

        assert pptx_file.is_file(), f"缺少簡報檔案：{pptx_file}"
        assert pptx_file.stat().st_size > 1000, "簡報檔案大小異常"
        assert pptx_file.read_bytes()[:4] == b"PK\x03\x04", "簡報缺少 PK ZIP 標頭"

        assert rec_file.is_file(), f"缺少錄影檔案：{rec_file}"
        assert rec_file.stat().st_size > 10000, "錄影檔案大小異常"
        assert rec_file.read_bytes()[4:8] == b"ftyp", "錄影缺少 MP4 ftyp 標頭"

        assert bgm_file.is_file(), f"缺少背景音訊：{bgm_file}"
        assert bgm_file.stat().st_size > 10000, "音訊檔案大小異常"

        assert logo_file.is_file(), f"缺少標誌圖片：{logo_file}"
        assert logo_file.stat().st_size > 500, "標誌檔案大小異常"
        assert logo_file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "標誌缺少 PNG 標頭"

    @pytest.mark.integration
    def test_f16_project_configs_contracts(self):
        """驗證 project.yaml, facts.yaml, script.json 符合介面合約。"""
        proj = load_project(str(DEMO_DIR))
        assert proj.name == "demo_showcase"
        assert proj.pptx is not None and proj.pptx.is_file()
        assert len(proj.recordings) == 1 and proj.recordings[0].is_file()

        facts = load_facts(DEMO_DIR / "facts.yaml")
        assert "frame_rate" in facts and "render_speed" in facts
        assert facts["frame_rate"].confirmed is True

        script = load_script(DEMO_DIR / "script.json")
        assert script.meta.title == "Video Creator Showcase"
        assert script.meta.fps == 30
        assert script.meta.size == (1920, 1080)
        assert len(script.scenes) == 3

    @pytest.mark.integration
    def test_f16_vc_validate_clean_pass(self, run_vc_cli):
        """驗證 python -m vc validate demo_showcase 100% 通過無錯誤。"""
        res = run_vc_cli("validate", str(DEMO_DIR))
        assert res.returncode == 0, f"vc validate 執行失敗：\n{res.stdout}\n{res.stderr}"
        assert "全部檢查通過" in res.stdout

    # --- Feature 17: 多風格與運鏡參數切換實測 ---

    @pytest.mark.integration
    def test_f17_style_variants_files_exist(self):
        """驗證包含至少 2 套風格與運鏡配置檔案。"""
        v_navy = DEMO_DIR / "variants" / "executive_navy_cinematic.yaml"
        v_swiss = DEMO_DIR / "variants" / "swiss_kinetic_dynamic.yaml"
        assert v_navy.is_file(), "缺少 executive_navy_cinematic.yaml"
        assert v_swiss.is_file(), "缺少 swiss_kinetic_dynamic.yaml"

        c_navy = yaml.safe_load(v_navy.read_text(encoding="utf-8"))
        c_swiss = yaml.safe_load(v_swiss.read_text(encoding="utf-8"))

        assert c_navy["style"] == "executive_navy"
        assert c_navy["camera_mode"] == "cinematic"
        assert c_swiss["style"] == "swiss_kinetic"
        assert c_swiss["camera_mode"] == "dynamic"

    def test_f17_style_tokens_and_html_rendering_difference(self):
        """驗證 Executive Navy 與 Swiss Kinetic 樣板渲染時產生實質視覺與色彩差異。"""
        navy_style = load_style("executive_navy")
        swiss_style = load_style("swiss_kinetic")

        assert navy_style["tokens"]["colors"]["accent"] == "#3FA9F5"
        assert swiss_style["tokens"]["colors"]["accent"] == "#A71D2A"
        assert navy_style["tokens"]["colors"]["background"] == "#0B1220"
        assert swiss_style["tokens"]["colors"]["background"] == "#F8F7F4"

        ctx = {
            "comp_id": "test_diff",
            "scene_id": "s01",
            "duration": 5.0,
            "fps": 30,
            "data": {"title": "Showcase", "subtitle": "Visual Style Switching", "badge": "Test"},
            "at_frames": {},
            "images": {"list": []},
        }

        html_navy = render_scene_html("title", ctx, style_config=navy_style, camera_config={"mode": "cinematic", "shots": []})
        html_swiss = render_scene_html("title", ctx, style_config=swiss_style, camera_config={"mode": "dynamic", "shots": []})

        assert html_navy != html_swiss, "兩套風格產出的 HTML 內容必須不相等"
        assert "#3FA9F5" in html_navy
        assert "#A71D2A" in html_swiss

    @pytest.mark.integration
    def test_f17_comparison_report_audit(self):
        """驗證風格切換比對報告實體存在且記錄實質差異。"""
        rep_json = DEMO_DIR / "reports" / "style_comparison_report.json"
        rep_md = DEMO_DIR / "reports" / "style_comparison_report.md"
        assert rep_json.is_file(), "缺少 style_comparison_report.json"
        assert rep_md.is_file(), "缺少 style_comparison_report.md"

        data = json.loads(rep_json.read_text(encoding="utf-8"))
        assert "token_differences" in data
        assert "scene_differences" in data
        for sc_id, var_dict in data["scene_differences"].items():
            for v_name, diff in var_dict.items():
                assert diff["distinct_html"] is True, f"場景 {sc_id}/{v_name} 風格 HTML 未產生實質差異"

    # --- Feature 18: 端到端管線走通與產物稽核 ---

    @pytest.mark.integration
    def test_f18_output_directory_structure_and_naming(self):
        """單一影片與字幕直接保存於 output，報告保存於 reports。"""
        output = DEMO_DIR / "output"
        assert list(output.glob("*.mp4")), "缺少單一影片成品"
        assert (output / "final.srt").stat().st_size > 0
        assert (output / "reports").is_dir()

    @pytest.mark.integration
    def test_f18_binary_magic_bytes_authenticity(self):
        """成品必須包含可讀取的影像與音訊串流。"""
        videos = list((DEMO_DIR / "output").glob("*.mp4"))
        assert videos, "缺少 MP4 成品"
        for video in videos:
            assert video.read_bytes()[4:8] == b"ftyp"
            info = probe(video)
            assert info["video_codec"] is not None
            assert info["has_audio"] is True
            assert (info["width"], info["height"]) == (1920, 1080)

    @pytest.mark.integration
    def test_f18_metadata_report_schema_and_values(self):
        """報告的單一影片資訊必須符合實際成品。"""
        from vc.fit import count_frames
        output = DEMO_DIR / "output"
        metadata = json.loads((output / "reports" / "metadata.json").read_text(encoding="utf-8"))
        video = output / metadata["file"]
        info = probe(video)
        assert metadata["total_frames"] == count_frames(video)
        assert metadata["fps"] == info["fps"]
        assert metadata["width"] == info["width"]
        assert metadata["height"] == info["height"]
        assert metadata["file_size_bytes"] == video.stat().st_size

    @pytest.mark.integration
    def test_f18_loudness_report_ebu_r128_compliance(self):
        """報告中的響度需符合設定目標與實際成品量測。"""
        from vc.render import get_loudness_targets, measure_loudness
        output = DEMO_DIR / "output"
        metadata = json.loads((output / "reports" / "metadata.json").read_text(encoding="utf-8"))
        report = json.loads((output / "reports" / "loudness_report.json").read_text(encoding="utf-8"))
        target, peak = get_loudness_targets(DEMO_DIR)
        measured = measure_loudness(output / metadata["file"])
        assert report["compliant"] is True
        assert report["target_lufs"] == target
        assert abs(measured["I"] - target) <= 1.0
        assert measured["TP"] <= peak + 0.1
        assert report["integrated_lufs"] == measured["I"]
        assert report["true_peak_dbtp"] == measured["TP"]
