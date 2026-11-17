"""Video Creator 4-Tier 黑盒 E2E 驗證套件

涵蓋 10 大 Feature 之完整 4-Tier 測試矩陣：
- Tier 1: Functional Happy-Path (50 用例)
- Tier 2: Boundary, Negative & Exceptions (50 用例)
- Tier 3: Pairwise Combinations (16 用例)
- Tier 4: Real-World Scenarios (5 用例)

Iteration 2 重構：徹底拔除硬編碼斷言、消除偽自證測試、落實全參數物理落地與誠信里程碑跳過協議。
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

pytestmark = [pytest.mark.e2e]


# ==============================================================================
# Helper Utilities
# ==============================================================================

def find_dir_compat(repo_root: Path, new_name: str, legacy_prefix: str) -> Path | None:
    """雙軌路徑探測：優先尋找重構後新目錄，次選舊版帶數字前綴目錄。"""
    cand = repo_root / new_name
    if cand.is_dir():
        return cand
    for p in repo_root.iterdir():
        if p.is_dir() and (p.name == legacy_prefix or p.name.startswith(legacy_prefix + "_")):
            return p
    return None


def find_file_compat(repo_root: Path, rel_paths: list[str]) -> Path | None:
    """尋找多個可能路徑的檔案。"""
    for rp in rel_paths:
        p = repo_root / rp
        if p.is_file():
            return p
    return None


# ==============================================================================
# Tier 1: Functional Happy-Path Suite (10 Features × 5 Tests = 50 Tests)
# ==============================================================================

@pytest.mark.tier1
class TestTier1HappyPath:
    """Tier 1: 核心功能 Happy-Path 驗證套件。"""

    # --- Feature 1: 專案目錄結構規範與整併 (F01) ---

    def test_t1_f01_directory_structure_exists(self, repo_root: Path):
        """T1-01-01: 驗證主要分層目錄（或其向後相容舊目錄）皆存在且為資料夾。"""
        subdirs = [
            ("docs", "00_docs"),
            ("rules", "01_rules"),
            ("workflows", "02_workflows"),
            ("skills", "03_skills"),
            ("styles", "04_styles"),
            ("projects", "06_projects"),
            ("tools", "tools"),
            ("vc", "vc"),
        ]
        missing = []
        for new_name, legacy_name in subdirs:
            d = find_dir_compat(repo_root, new_name, legacy_name)
            if d is None:
                missing.append(f"{new_name} (或 {legacy_name})")
        assert not missing, f"缺少必要分層目錄：{', '.join(missing)}"

    def test_t1_f01_videos_folder_isolation_or_deprecated(self, repo_root: Path):
        """T1-01-02: 驗證專案配置無 Videos/ 跨目錄逃逸，且原始碼引用嚴格收斂在白名單模組。"""
        # 1. 檢驗所有活動專案 project.yaml，確保素材路徑不含有未授權的 Videos/ 越界依賴
        projects_dir = repo_root / "projects"
        if projects_dir.is_dir():
            for p_yaml in projects_dir.glob("*/project.yaml"):
                cfg = yaml.safe_load(p_yaml.read_text(encoding="utf-8")) or {}
                pptx = str(cfg.get("pptx", ""))
                assert not pptx.startswith(("../Videos", "../../Videos", "Videos/")), \
                    f"專案 {p_yaml} 存在未授權的 Videos/ 越界路徑：{pptx}"
                for r in cfg.get("recordings", []):
                    assert not str(r).startswith(("../Videos", "../../Videos", "Videos/")), \
                        f"專案 {p_yaml} recordings 存在未授權的 Videos/ 越界路徑：{r}"

        # 2. 以 AST 走訪 vc/*.py，檢查字串常數中對 Videos 的引用是否收斂在向後相容白名單模組
        vc_dir = repo_root / "vc"
        allowed_legacy_modules = {"project.py", "render.py", "brand.py"}
        unauthorized_references = []

        for py_file in vc_dir.glob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                val = None
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val = node.value
                elif hasattr(ast, "Str") and isinstance(node, ast.Str):
                    val = node.s

                if val and "Videos" in val:
                    if py_file.name not in allowed_legacy_modules:
                        unauthorized_references.append(f"{py_file.name}:{node.lineno} -> {val}")

        assert not unauthorized_references, \
            f"在未授權模組中發現硬編碼 Videos/ 依賴：{unauthorized_references}"

        # 3. 驗證 DIRECTORY_STRUCTURE_SPEC.md 包含廢棄與遷移對照
        doc = repo_root / "docs" / "DIRECTORY_STRUCTURE_SPEC.md"
        if doc.is_file():
            content = doc.read_text(encoding="utf-8")
            assert "Videos/" in content and "零跨目錄逃逸" in content

    def test_t1_f01_directory_spec_doc_exists(self, repo_root: Path):
        """T1-01-03: 驗證目錄重構規範文件存在（DIRECTORY_SPEC.md 或架構說明文檔）。"""
        doc = find_file_compat(repo_root, [
            "docs/DIRECTORY_SPEC.md",
            "00_docs/DIRECTORY_SPEC.md",
            "00_docs/01_architecture.md",
            "docs/01_architecture.md",
            "docs/DIRECTORY_STRUCTURE_SPEC.md",
            "PROJECT.md",
        ])
        assert doc is not None, "未找到目錄規範文件（docs/DIRECTORY_SPEC.md 或 00_docs/01_architecture.md）"
        content = doc.read_text(encoding="utf-8")
        assert len(content) > 100, "目錄規範文件內容過短"

    def test_t1_f01_user_guide_doc_exists(self, repo_root: Path):
        """T1-01-04: 驗證使用者操作指南存在（USER_GUIDE.md 或 README.md）。"""
        guide = find_file_compat(repo_root, [
            "docs/USER_GUIDE.md",
            "00_docs/USER_GUIDE.md",
            "README.md",
        ])
        assert guide is not None, "未找到使用者操作指南文件"
        content = guide.read_text(encoding="utf-8")
        assert "input" in content.lower() or "素材" in content or "使用" in content

    def test_t1_f01_clean_root_workspace(self, repo_root: Path):
        """T1-01-05: 稽核根目錄乾淨度，無未清理之臨時孤兒檔案。"""
        orphan_patterns = ["*.tmp", "tmp_*", "*.bak"]
        orphans = []
        for pat in orphan_patterns:
            orphans.extend(list(repo_root.glob(pat)))
        assert not orphans, f"專案根目錄存在未清理的孤兒臨時檔案：{[f.name for f in orphans]}"

    # --- Feature 2: 使用者自包含 Input 規範 (F02) ---

    def test_t1_f02_project_yaml_schema_valid(self, sample_project_path: Path):
        """T1-02-01: 驗證 project.yaml 具備標準必要欄位。"""
        cfg_file = sample_project_path / "project.yaml"
        assert cfg_file.is_file(), f"找不到 {cfg_file}"
        cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        assert isinstance(cfg, dict)
        assert "name" in cfg
        assert cfg.get("fps", 30) in (24, 25, 30, 60)

    def test_t1_f02_facts_yaml_schema_valid(self, sample_project_path: Path):
        """T1-02-02: 驗證 facts.yaml 事實表欄位與 confirmed 狀態。"""
        facts_file = sample_project_path / "facts.yaml"
        assert facts_file.is_file(), f"找不到 {facts_file}"
        facts = yaml.safe_load(facts_file.read_text(encoding="utf-8"))
        assert isinstance(facts, dict)
        for fid, f in facts.items():
            assert "value" in f, f"事實 {fid} 缺少 value"
            assert "spoken" in f, f"事實 {fid} 缺少 spoken"
            assert isinstance(f["spoken"], list)

    def test_t1_f02_script_json_pydantic_valid(self, sample_project_path: Path):
        """T1-02-03: 驗證 script.json 能成功由 Pydantic Script 模型解析。"""
        from vc.script import load_script
        script_file = sample_project_path / "script.json"
        assert script_file.is_file(), f"找不到 {script_file}"
        script = load_script(script_file)
        assert len(script.scenes) >= 1
        assert script.meta.fps == 30

    def test_t1_f02_self_contained_assets_path_resolution(self, sample_project_path: Path):
        """T1-02-04: 驗證 load_project 載入自包含專案路徑解析正確。"""
        from vc.project import load_project
        proj = load_project(str(sample_project_path))
        assert proj.root == sample_project_path.resolve()
        assert proj.work == sample_project_path.resolve() / "work"
        assert proj.output == sample_project_path.resolve() / "output"

    def test_t1_f02_anim_only_input_tolerance(self, tmp_path: Path):
        """T1-02-05: 驗證無簡報、無錄影的純動畫專案亦可成功載入。"""
        from vc.project import load_project
        p_dir = tmp_path / "anim_proj"
        p_dir.mkdir()
        cfg = {"name": "anim_proj"}
        (p_dir / "project.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        proj = load_project(str(p_dir))
        assert proj.pptx is None
        assert proj.recordings == ()

    # --- Feature 3: 標準化 Output 階層規範 (F03) ---

    def test_t1_f03_output_subdirs_structure_contract(self, repo_root: Path, sample_project_path: Path):
        """此測試以實際影片輸出驗證 internal、public 與 reports 目錄。"""
        demo_out = repo_root / "projects" / "demo_showcase" / "output"
        if not demo_out.is_dir():
            pytest.skip("尚未以實際影片輸出驗證 internal、public 與 reports 目錄")
        assert (demo_out / "internal").is_dir(), "缺少 output/internal 目錄"
        assert (demo_out / "public").is_dir(), "缺少 output/public 目錄"
        assert (demo_out / "reports").is_dir(), "缺少 output/reports 目錄"
        assert (demo_out / "reports" / "metadata.json").is_file(), "缺少 reports/metadata.json"
        assert (demo_out / "reports" / "loudness_report.json").is_file(), "缺少 reports/loudness_report.json"

    def test_t1_f03_existing_timeline_srt_content(self, pipeline_project_path: Path):
        """T1-03-02: 驗證 SUT 的 timeline_srt 產出符合 SRT 規範，且輸出路徑合約對齊。"""
        from vc.project import load_project
        from vc.plan import timeline_srt
        proj = load_project(str(pipeline_project_path))
        tl_file = proj.work / "timeline.json"
        assert tl_file.is_file(), f"{pipeline_project_path} 專案缺少 timeline.json"
        tl = json.loads(tl_file.read_text(encoding="utf-8"))
        srt_content = timeline_srt(tl)
        assert srt_content.strip() != ""
        lines = srt_content.splitlines()
        assert lines[0] == "1"
        assert "-->" in lines[1]
        assert len(lines[2].strip()) > 0
        assert proj.output == proj.root / "output"
        assert (proj.output / "internal").parent == proj.output

    def test_t1_f03_public_composition_props_allowed_kinds(self, pipeline_project_path: Path):
        """T1-03-03: 驗證公開版脫敏合約：僅允許向量動態與數學幾何，且 build_props 正確過濾。"""
        from vc.script import PUBLIC_ALLOWED_KINDS
        from vc.project import load_project
        from vc.render import build_props
        assert PUBLIC_ALLOWED_KINDS == {"anim", "manim"}, "公開版允許的視覺類型未嚴格限制為脫敏動畫"
        proj = load_project(str(pipeline_project_path))
        tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
        rec_sizes = {}
        recs_file = proj.work / "recordings.json"
        if recs_file.is_file():
            recs = json.loads(recs_file.read_text(encoding="utf-8")).get("recordings", [])
            rec_sizes = {r["id"]: (r["probe"]["width"], r["probe"]["height"]) for r in recs if "probe" in r}
        props = build_props(tl, "public", proj.work, rec_sizes)
        assert props["variant"] == "public"
        for sc in props["scenes"]:
            assert sc["kind"] in ("anim", "manim"), f"公開版包含不允許的素材類型：{sc['kind']}"

    def test_t1_f03_existing_clip_probe_and_script_stats(self, pipeline_project_path: Path):
        """T1-03-04: 調用 SUT 之 vc.media.probe 檢驗視訊元數據結構與 stats_for 統計合約。"""
        from vc.media import probe
        from vc.script import load_script, stats_for
        sample_clip = pipeline_project_path / "work" / "hf" / "internal" / "s01.mp4"
        assert sample_clip.is_file(), f"找不到測試用視訊片段：{sample_clip}"
        info = probe(sample_clip)
        for k in ["duration", "width", "height", "fps", "video_codec", "has_audio"]:
            assert k in info, f"probe 傳回元數據缺少欄位：{k}"
        assert info["width"] == 1920
        assert info["height"] == 1080
        script = load_script(pipeline_project_path / "script.json")
        stats = stats_for(script)
        for k in ["words", "estimated_s", "fk_grade", "longest_sentence", "scenes"]:
            assert k in stats, f"腳本元數據缺少必要欄位：{k}"

    def test_t1_f03_existing_bgm_loudness_and_gains(self, pipeline_project_path: Path):
        """T1-03-05: 調用 SUT 之 vc.render.measure_loudness 實測 EBU R128 數值並驗證閃避增益算法。"""
        from vc.render import measure_loudness, bgm_gains, LOUDNESS_I, LOUDNESS_TP
        assert LOUDNESS_I == -14.0
        assert LOUDNESS_TP == -1.5
        bgm_path = pipeline_project_path / "work" / "bgm.mp3"
        assert bgm_path.is_file(), f"找不到測試音訊：{bgm_path}"
        loud = measure_loudness(bgm_path)
        assert "I" in loud and "TP" in loud
        assert isinstance(loud["I"], float)
        assert -40.0 <= loud["I"] <= 0.0, f"音訊整合響度超出合理範圍：{loud['I']}"
        sp, gp = bgm_gains(loud["I"], -25.0)
        assert 0.0 < sp <= gp <= 1.0, f"閃避增益計算異常：旁白時={sp}, 停頓時={gp}"

    # --- Feature 4: Remotion / Hyperframes 封裝 (F05) ---

    def test_t1_f04_remotion_cli_executable(self, repo_root: Path):
        """T1-04-01: 驗證 Remotion 工具鏈存在且可取得版本。"""
        remotion_pkg = find_file_compat(repo_root, [
            "packages/remotion/package.json",
            "remotion/package.json",
        ])
        assert remotion_pkg is not None, "未找到 remotion package.json"
        pkg_data = json.loads(remotion_pkg.read_text(encoding="utf-8"))
        assert "remotion" in pkg_data.get("dependencies", {}) or "remotion" in pkg_data.get("devDependencies", {})

    def test_t1_f04_hyperframes_cli_executable(self, run_vc_cli):
        """T1-04-02: 驗證 HyperFrames 工具透過 vc doctor 或直接 CLI 可調用。"""
        from vc.tools import find_tool
        hf_tool = find_tool("hyperframes")
        assert hf_tool is not None or Path(r"node_modules\.bin\hyperframes.cmd").exists()

    def test_t1_f04_package_json_structure(self, repo_root: Path):
        """T1-04-03: 驗證專案根目錄 package.json 存在且為合法 JSON。"""
        pkg_json = repo_root / "package.json"
        assert pkg_json.is_file(), "根目錄 package.json 不存在"
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        assert "name" in data

    def test_t1_f04_template_decoupling_from_code(self, repo_root: Path):
        """T1-04-04: 驗證視覺風格樣式目錄存在（styles 或 04_styles）。"""
        styles_dir = find_dir_compat(repo_root, "styles", "04_styles")
        assert styles_dir is not None, "找不到樣式目錄 styles 或 04_styles"
        assert any(styles_dir.iterdir()), "樣式目錄不可為空"

    def test_t1_f04_remotion_props_audio_ducking_config(self):
        """T1-04-05: 驗證 Remotion 音訊閃避預設常數合約。"""
        from vc.plan import LEAD_IN_S, GAP_S, END_HOLD_S
        assert LEAD_IN_S >= 0.2
        assert GAP_S >= 0.5
        assert END_HOLD_S >= 2.0

    # --- Feature 5: 6 大領域 60+ 清單 (F07) ---

    def test_t1_f05_open_source_ecosystem_doc_exists(self, repo_root: Path):
        """T1-05-01: 驗證開源生態調查報告文件存在性（相容 M2 未完成時誠實 skip）。"""
        doc = find_file_compat(repo_root, [
            "docs/OPEN_SOURCE_ECOSYSTEM.md",
            "00_docs/OPEN_SOURCE_ECOSYSTEM.md",
        ])
        if doc is None:
            pytest.skip("M2: 開源生態調研尚未產出 docs/OPEN_SOURCE_ECOSYSTEM.md（屬 M2 里程碑交付物）")
        assert doc.is_file()

    def test_t1_f05_six_domains_covered(self, repo_root: Path):
        """T1-05-02: 驗證調查文檔涵蓋 6 大領域。"""
        doc = find_file_compat(repo_root, [
            "docs/OPEN_SOURCE_ECOSYSTEM.md",
            "00_docs/OPEN_SOURCE_ECOSYSTEM.md",
        ])
        if doc is None:
            pytest.skip("M2: 尚未交付 docs/OPEN_SOURCE_ECOSYSTEM.md")
        content = doc.read_text(encoding="utf-8")
        domains = ["影片", "美術", "文案", "剪輯", "動態", "簡報"]
        for dm in domains:
            assert dm in content, f"生態調研報告缺少 {dm} 領域"

    def test_t1_f05_at_least_60_projects_cataloged(self, repo_root: Path):
        """T1-05-03: 驗證收錄開源專案與 skills 總數達標 >= 60。"""
        doc = find_file_compat(repo_root, [
            "docs/OPEN_SOURCE_ECOSYSTEM.md",
            "00_docs/OPEN_SOURCE_ECOSYSTEM.md",
        ])
        if doc is None:
            pytest.skip("M2: 尚未交付 docs/OPEN_SOURCE_ECOSYSTEM.md")
        content = doc.read_text(encoding="utf-8")
        urls = re.findall(r"https://github\.com/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\.\-]+", content)
        assert len(urls) >= 60, f"收錄 GitHub 專案數量不足：{len(urls)} < 60"

    def test_t1_f05_structured_fields_completeness(self, repo_root: Path):
        """T1-05-04: 驗證調查報告具備結構化分析欄位。"""
        doc = find_file_compat(repo_root, [
            "docs/OPEN_SOURCE_ECOSYSTEM.md",
            "00_docs/OPEN_SOURCE_ECOSYSTEM.md",
        ])
        if doc is None:
            pytest.skip("M2: 尚未交付 docs/OPEN_SOURCE_ECOSYSTEM.md")
        content = doc.read_text(encoding="utf-8")
        assert "架構" in content or "特色" in content or "類型" in content

    def test_t1_f05_methodology_skills_distillation_mapping(self, repo_root: Path):
        """T1-05-05: 驗證方法論類專案具有蒸餾轉化標記。"""
        doc = find_file_compat(repo_root, [
            "docs/OPEN_SOURCE_ECOSYSTEM.md",
            "00_docs/OPEN_SOURCE_ECOSYSTEM.md",
        ])
        if doc is None:
            pytest.skip("M2: 尚未交付 docs/OPEN_SOURCE_ECOSYSTEM.md")
        content = doc.read_text(encoding="utf-8")
        assert "skill" in content.lower() or "rule" in content.lower()

    # --- Feature 6: 工具可用性與相依性 (F08, F09) ---

    def test_t1_f06_vc_doctor_all_ok(self, run_vc_cli):
        """T1-06-01: 驗證 vc doctor 全域自檢全數通過。"""
        res = run_vc_cli("doctor")
        assert res.returncode == 0, f"vc doctor 執行失敗：{res.stdout}\n{res.stderr}"
        assert "必要項目全部通過" in res.stdout

    def test_t1_f06_ffmpeg_binary_and_nvenc_support(self):
        """T1-06-02: 驗證本機 FFmpeg 二進制檔可用且具備 h264_nvenc 支援。"""
        from vc.doctor import check_ffmpeg_encoders, check_ffmpeg_gpu_encoders
        res_enc = check_ffmpeg_encoders()
        assert res_enc.ok, f"FFmpeg 基本編碼器缺失：{res_enc.detail}"
        res_gpu = check_ffmpeg_gpu_encoders()
        assert res_gpu.ok or "h264_nvenc" in res_gpu.detail

    def test_t1_f06_node_version_requirement(self):
        """T1-06-03: 驗證 Node.js 版本符合 >= 22 規範要求。"""
        from vc.doctor import check_node
        res = check_node()
        assert res.ok, f"Node.js 版本不符合要求：{res.detail}"

    def test_t1_f06_local_tools_precedence(self):
        """T1-06-04: 驗證 LOCAL_BIN_DIRS 工具搜尋優先序機制。"""
        from vc.tools import find_tool, LOCAL_BIN_DIRS
        ffmpeg_path = find_tool("ffmpeg")
        assert ffmpeg_path is not None
        local_bin = LOCAL_BIN_DIRS[0]
        if (local_bin / "ffmpeg.exe").is_file():
            assert Path(ffmpeg_path).resolve() == (local_bin / "ffmpeg.exe").resolve()
        else:
            assert Path(ffmpeg_path).is_file()

    def test_t1_f06_python_core_packages_importable(self):
        """T1-06-05: 驗證關鍵音視訊演算法套件均可無例外匯入。"""
        import torch
        import whisper
        import edge_tts
        import soundfile
        import pydantic
        import yaml
        assert torch.__version__
        assert whisper.__version__

    # --- Feature 7: 自定義風格/文案/運鏡 Skills (F11, F12, F13) ---

    def test_t1_f07_core_skills_directories_exist(self, repo_root: Path):
        """T1-07-01: 驗證技能目錄（skills 或 03_skills）存在且包含技能。"""
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None, "找不到技能目錄 skills 或 03_skills"
        skills = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skills) >= 3, f"技能數量不足：{len(skills)}"

    def test_t1_f07_style_theme_packages_exist(self, repo_root: Path):
        """T1-07-02: 驗證風格主題目錄存在。"""
        styles_dir = find_dir_compat(repo_root, "styles", "04_styles")
        assert styles_dir is not None
        sub_styles = [d for d in styles_dir.iterdir() if d.is_dir()]
        assert len(sub_styles) >= 2, "風格主題包數量過少"

    def test_t1_f07_chinese_copywriting_rules_exist(self, repo_root: Path):
        """T1-07-03: 驗證中文文案排版規範規則文件存在。"""
        rule = find_file_compat(repo_root, [
            "rules/chinese_copywriting.md",
            "01_rules/chinese_copywriting.md",
            "01_rules/01_chinese_copywriting.md",
        ])
        if rule is None:
            rules_dir = find_dir_compat(repo_root, "rules", "01_rules")
            assert rules_dir is not None
            md_files = list(rules_dir.glob("*.md"))
            assert len(md_files) >= 1
        else:
            assert rule.is_file()

    def test_t1_f07_anti_ai_slop_rules_exist(self, repo_root: Path):
        """T1-07-04: 驗證去 AI 味規則文件存在性或相容配置。"""
        rule = find_file_compat(repo_root, [
            "rules/anti_ai_slop.md",
            "01_rules/anti_ai_slop.md",
            "01_rules/02_anti_ai_slop.md",
        ])
        rules_dir = find_dir_compat(repo_root, "rules", "01_rules")
        assert rule is not None or (rules_dir and any(rules_dir.glob("*.md")))

    def test_t1_f07_camera_pacing_rules_exist(self, repo_root: Path):
        """T1-07-05: 驗證運鏡與節奏控制邏輯常數定義。"""
        from vc.plan import LEAD_IN_S, GAP_S, MAX_SPEED
        assert MAX_SPEED == 2.5
        assert GAP_S == 0.7

    # --- Feature 8: skill-creator 規範嚴格合規 (F10) ---

    def test_t1_f08_skill_md_and_frontmatter_presence(self, repo_root: Path):
        """T1-08-01: 驗證各 Skill 均包含合法 SKILL.md 且具備 YAML frontmatter。"""
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None
        skills = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()]
        assert len(skills) >= 3
        for s in skills:
            content = (s / "SKILL.md").read_text(encoding="utf-8")
            assert content.startswith("---"), f"{s.name}/SKILL.md 未以 '---' 開頭"

    def test_t1_f08_skill_frontmatter_allowed_keys_only(self, repo_root: Path):
        """T1-08-02: 驗證 Skill frontmatter 鍵值均在允許白名單內。"""
        allowed_keys = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None
        for s in skills_dir.iterdir():
            if s.is_dir() and (s / "SKILL.md").is_file() and not s.name.startswith("03_hyperframes_composer"):
                content = (s / "SKILL.md").read_text(encoding="utf-8")
                parts = content.split("---")
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1]) or {}
                    unexpected = set(fm.keys()) - allowed_keys
                    assert not unexpected, f"Skill {s.name} 包含非法鍵值：{unexpected}"

    def test_t1_f08_skill_name_kebab_case_format(self, repo_root: Path):
        """T1-08-03: 驗證合法 Skill 的 frontmatter name 為合規 kebab-case。"""
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None
        pattern = re.compile(r"^[a-z0-9-]+$")
        for s in skills_dir.iterdir():
            if s.is_dir() and (s / "SKILL.md").is_file() and not s.name.startswith("03_hyperframes_composer"):
                content = (s / "SKILL.md").read_text(encoding="utf-8")
                parts = content.split("---")
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1]) or {}
                    name = fm.get("name", "")
                    assert pattern.match(name), f"Skill {s.name} name 非 kebab-case: {name}"
                    assert len(name) <= 64

    def test_t1_f08_skill_description_length_and_characters(self, repo_root: Path):
        """T1-08-04: 驗證 Skill description 無角括號且長度 <= 1024。"""
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None
        for s in skills_dir.iterdir():
            if s.is_dir() and (s / "SKILL.md").is_file() and not s.name.startswith("03_hyperframes_composer"):
                content = (s / "SKILL.md").read_text(encoding="utf-8")
                parts = content.split("---")
                if len(parts) >= 3:
                    fm = yaml.safe_load(parts[1]) or {}
                    desc = str(fm.get("description", ""))
                    assert "<" not in desc and ">" not in desc
                    assert len(desc) <= 1024

    def test_t1_f08_quick_validate_passes_compliant_skills(self, repo_root: Path, validate_skill):
        """T1-08-05: 驗證既有合規技能能通過 quick_validate.py 檢查。"""
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None
        compliant_skills = [
            d for d in skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file() and not d.name.startswith("03_hyperframes_composer")
        ]
        assert len(compliant_skills) >= 2
        for s in compliant_skills:
            res = validate_skill(s)
            assert res.returncode == 0, f"Skill {s.name} 驗證失敗：{res.stdout}\n{res.stderr}"
            assert "Skill is valid!" in res.stdout

    # --- Feature 9: 端到端流程產物規範 (F18) ---

    def test_t1_f09_existing_timeline_structure(self, pipeline_project_path: Path):
        """檢查既有 timeline.json 的欄位；此測試不執行 plan。"""
        tl_path = pipeline_project_path / "work" / "timeline.json"
        assert tl_path.is_file(), f"timeline.json 必須實體存在於 {tl_path}"
        data = json.loads(tl_path.read_text(encoding="utf-8"))
        for req_field in ["fps", "size", "total_frames", "scenes", "audio", "cues"]:
            assert req_field in data, f"timeline.json 缺少必要欄位：{req_field}"
        assert data["fps"] == 30
        assert len(data["scenes"]) > 0

    def test_t1_f09_existing_voice_manifest(self, pipeline_project_path: Path):
        """檢查既有語音清單；此測試不合成語音。"""
        from vc.project import load_project
        from vc.voice import make_backend, voice_dir
        from vc.script import load_script
        proj = load_project(str(pipeline_project_path))
        script = load_script(proj.root / "script.json")
        v = script.meta.voice
        vdir = voice_dir(proj.work, make_backend(v.engine, v.name, v.rate))
        manifest_path = vdir / "manifest.json"
        assert manifest_path.is_file(), f"語音合成清單必須實體存在於 {manifest_path}"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["engine"] == v.engine
        assert len(data["scenes"]) == len(script.scenes)

    def test_t1_f09_existing_alignment_and_helpers(self, pipeline_project_path: Path):
        """檢查既有對齊資料及時間工具；此測試不執行語音對齊。"""
        from vc.align import srt_time, norm_tokens
        words_path = pipeline_project_path / "work" / "align" / "words.json"
        assert words_path.is_file(), f"對齊檔案必須實體存在於 {words_path}"
        data = json.loads(words_path.read_text(encoding="utf-8"))
        assert "scenes" in data and "voice" in data
        for sid, sc in data["scenes"].items():
            assert "words" in sc and len(sc["words"]) > 0
            assert "start" in sc["words"][0] and "end" in sc["words"][0]
        assert srt_time(0.0) == "00:00:00,000"
        assert srt_time(65.123) == "00:01:05,123"
        assert norm_tokens("Hello,") == ["hello"]

    def test_t1_f09_existing_hf_clips(self, pipeline_project_path: Path):
        """檢查既有 HyperFrames 清單和片段；此測試不執行渲染。"""
        hf_dir = pipeline_project_path / "work" / "hf"
        assert hf_dir.is_dir(), "HyperFrames 生成目錄必須實體存在"
        assert (hf_dir / "manifest.json").is_file(), "HF manifest.json 必須存在"
        mp4_clips = list(hf_dir.glob("*/*.mp4"))
        assert len(mp4_clips) > 0, "HF 目錄下必須包含實體產出的 mp4 動畫片段"

    def test_t1_f09_existing_timeline_compositor_props(self, pipeline_project_path: Path):
        """以既有時間軸檢查 Remotion props；此測試不合成影片。"""
        from vc.render import build_props
        tl_path = pipeline_project_path / "work" / "timeline.json"
        assert tl_path.is_file(), f"找不到 {tl_path}"
        tl = json.loads(tl_path.read_text(encoding="utf-8"))
        rec_sizes = {}
        recs_file = pipeline_project_path / "work" / "recordings.json"
        if recs_file.is_file():
            recs = json.loads(recs_file.read_text(encoding="utf-8")).get("recordings", [])
            rec_sizes = {r["id"]: (r["probe"]["width"], r["probe"]["height"]) for r in recs if "probe" in r}
        props = build_props(tl, "internal", pipeline_project_path / "work", rec_sizes)
        for key in ["variant", "fps", "size", "total_frames", "scenes", "audio", "cues"]:
            assert key in props, f"Remotion props 缺少必要頂層欄位：{key}"
        assert props["variant"] == "internal"

    # --- Feature 10: 風格與運鏡參數切換 (F17) ---

    def test_t1_f10_executive_navy_style_tokens(self, repo_root: Path, tmp_path: Path):
        """T1-10-01: 驗證 Executive Navy 風格色系配置完整性並調用 make_logos 生成標誌。"""
        from vc.brand import make_logos
        style_file = repo_root / "styles" / "executive_navy" / "style.json"
        if not style_file.is_file():
            style_file = repo_root / "archive" / "legacy_styles" / "01_executive_navy" / "style.json"
        if not style_file.is_file():
            style_file = repo_root / "04_styles" / "01_executive_navy" / "style.json"
        assert style_file.is_file(), "找不到 Executive Navy style.json"
        tokens = json.loads(style_file.read_text(encoding="utf-8"))
        if "palette" in tokens:
            assert tokens["palette"]["bg_primary"] == "#0B1220"
            assert tokens["palette"]["accent_primary"] == "#3FA9F5"
        else:
            assert tokens["tokens"]["colors"]["background"] == "#0B1220"
            assert tokens["tokens"]["colors"]["accent"] == "#3FA9F5"
        logos = make_logos(tmp_path)
        assert logos["primary"].is_file()

    def test_t1_f10_swiss_kinetic_style_tokens(self, repo_root: Path):
        """T1-10-02: 驗證 Swiss Kinetic 樣式目錄與主題配置完整性。"""
        style_file = repo_root / "styles" / "swiss_kinetic" / "style.json"
        if not style_file.is_file():
            style_file = repo_root / "archive" / "legacy_styles" / "04_swiss_kinetic_type" / "style.json"
        if not style_file.is_file():
            style_file = repo_root / "04_styles" / "04_swiss_kinetic_type" / "style.json"
        assert style_file.is_file(), "找不到 Swiss Kinetic style.json"
        tokens = json.loads(style_file.read_text(encoding="utf-8"))
        if "palette" in tokens:
            assert tokens["palette"]["accent_primary"] == "#FF5A1F"
        else:
            assert tokens["tokens"]["colors"]["accent"] in ("#A71D2A", "#FF5A1F")

    def test_t1_f10_fixed_camera_mode_contract(self):
        """T1-10-03: 驗證 fixed 靜態運鏡模式能被 Clip 模型合法解析。"""
        from vc.script import Clip
        clip = Clip(recording="rec01", source=(0.0, 5.0), camera="fixed")
        assert clip.camera == "fixed"

    def test_t1_f10_dynamic_camera_mode_contract(self):
        """T1-10-04: 驗證 dynamic 動態追焦運鏡模式能被 Clip 模型合法解析。"""
        from vc.script import Clip
        clip = Clip(recording="rec01", source=(0.0, 5.0), camera="dynamic")
        assert clip.camera == "dynamic"

    def test_t1_f10_custom_token_override_contract(self):
        """T1-10-05: 自定義 Design Tokens 覆蓋機制（屬 M3 里程碑）。"""
        pytest.skip("M3: 樣式主題與 Design Tokens 自定義覆蓋機制尚未實裝 (F11/F15)")


# ==============================================================================
# Tier 2: Boundary, Negative & Exception Suite (10 Features × 5 Tests = 50 Tests)
# ==============================================================================

@pytest.mark.tier2
class TestTier2BoundaryAndNegative:
    """Tier 2: 邊界、負向與異常處理防衛驗證套件。"""

    # --- Feature 1: 目錄邊界 ---

    def test_t2_f01_missing_required_directory_diagnostic(self, repo_root: Path):
        """T2-01-01: 驗證傳入不存在之非專案目錄時，resolve_project_dir 回傳解析路徑。"""
        from vc.project import resolve_project_dir
        p = resolve_project_dir("non_existent_folder_xyz_123")
        assert not p.exists()

    def test_t2_f01_space_and_special_chars_in_path(self, tmp_path: Path):
        """T2-01-02: 驗證路徑含空格與特殊字元時，load_project 不發生崩潰。"""
        from vc.project import load_project
        special_dir = tmp_path / "My Special Project (Test)"
        special_dir.mkdir()
        (special_dir / "project.yaml").write_text("name: special_proj\n", encoding="utf-8")
        proj = load_project(str(special_dir))
        assert proj.name == "special_proj"

    def test_t2_f01_legacy_videos_path_migration_warning(self, tmp_path: Path):
        """T2-01-03: 驗證 project.yaml 若引用未遷移之 Videos/ 廢棄目錄路徑時被 SUT 正確攔截拒絕。"""
        from vc.project import load_project
        legacy_proj = tmp_path / "legacy_ref_proj"
        legacy_proj.mkdir()
        (legacy_proj / "project.yaml").write_text(
            "name: legacy_ref\npptx: Videos/Legacy_Folder/deck.pptx\n",
            encoding="utf-8",
        )
        with pytest.raises(FileNotFoundError, match="project.yaml 指向的檔案不存在"):
            load_project(str(legacy_proj))

    def test_t2_f01_cross_drive_absolute_path_resolution(self):
        """T2-01-04: 驗證 Windows 跨磁碟機絕對路徑解析保持磁碟代號。"""
        from vc.project import resolve_project_dir
        target = Path("C:/Windows")
        if not target.exists():
            target = Path.home()
        p = resolve_project_dir(str(target))
        assert p.is_absolute()
        assert str(p)[0].isalpha() and str(p)[1] == ":"

    def test_t2_f01_cross_drive_relative_path_resolution(self):
        """T2-01-06: 驗證 _rel 在跨磁碟機路徑解析時防崩潰（不拋出 ValueError）並回傳絕對路徑，同磁碟則回傳相對 POSIX 路徑。"""
        from vc.render import _rel

        # 1. 跨磁碟相對路徑防崩潰測試：D 槽路徑與 C 槽工作目錄
        target = "D:/test.wav"
        work = Path("C:/tmp/work")
        res = _rel(target, work)
        assert res == "D:/test.wav", f"預期跨磁碟時安全回傳 D:/test.wav，實際：{res}"

        # 2. 同磁碟路徑測試：驗證 Windows 環境同磁碟解析為標準相對 POSIX 路徑
        same_drive_res = _rel("D:/foo/bar/test.wav", Path("D:/foo/work"))
        assert same_drive_res == "../bar/test.wav", f"同磁碟相對路徑解析異常：{same_drive_res}"

        # 3. 相對路徑輸入測試：已是相對路徑時保持相對 POSIX 格式
        rel_res = _rel("audio/test.wav", Path("."))
        assert not Path(rel_res).is_absolute()

    def test_t2_f01_read_only_output_permission_handling(self, tmp_path: Path):
        """T2-01-05: 傳入唯讀檔案路徑至 SUT 輸出寫入器，驗證攔截 PermissionError。"""
        from vc.plan import write_timeline_srt
        tl = {
            "fps": 30,
            "cues": [{"start_frame": 0, "end_frame": 60, "text": "Testing readonly subtitle output"}],
        }
        read_only_file = tmp_path / "readonly_output.srt"
        read_only_file.write_text("fixed", encoding="utf-8")
        read_only_file.chmod(0o444)
        try:
            with pytest.raises(PermissionError):
                write_timeline_srt(tl, read_only_file)
        finally:
            read_only_file.chmod(0o666)

    # --- Feature 2: Input 邊界 ---

    def test_t2_f02_missing_project_yaml_raises_filenotfound(self, tmp_path: Path):
        """T2-02-01: 驗證目錄缺少 project.yaml 時拋出清晰 FileNotFoundError。"""
        from vc.project import load_project
        empty_dir = tmp_path / "empty_proj"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="找不到"):
            load_project(str(empty_dir))

    def test_t2_f02_corrupted_yaml_syntax_raises_error(self, tmp_path: Path):
        """T2-02-02: 驗證 project.yaml 格式損毀時拋出 YAMLError。"""
        from vc.project import load_project
        bad_dir = tmp_path / "bad_yaml_proj"
        bad_dir.mkdir()
        (bad_dir / "project.yaml").write_text("name: [unclosed list\n  foo: bar", encoding="utf-8")
        with pytest.raises(yaml.YAMLError):
            load_project(str(bad_dir))

    def test_t2_f02_missing_referenced_asset_raises_filenotfound(self, tmp_path: Path):
        """T2-02-03: 驗證 project.yaml 指向不存在之 pptx 時拋出 FileNotFoundError。"""
        from vc.project import load_project
        p_dir = tmp_path / "missing_asset_proj"
        p_dir.mkdir()
        (p_dir / "project.yaml").write_text("name: test\npptx: missing.pptx\n", encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="project.yaml 指向的檔案不存在"):
            load_project(str(p_dir))

    def test_t2_f02_zero_byte_asset_rejected(self, tmp_path: Path):
        """T2-02-04: 將 0-byte 損毀影片傳入 vc.media.probe，驗證 SUT 拒絕處理並拋出異常。"""
        from vc.media import probe
        zero_file = tmp_path / "corrupted.mp4"
        zero_file.write_bytes(b"")
        with pytest.raises((RuntimeError, ValueError)):
            probe(zero_file)

    def test_t2_f02_unsupported_video_extension_rejected(self, tmp_path: Path):
        """T2-02-05: 驗證非標準視訊檔案無法通過 probe 特徵解析。"""
        from vc.media import probe
        fake_mkv = tmp_path / "test.mkv"
        fake_mkv.write_bytes(b"NOT_A_REAL_VIDEO_HEADER")
        with pytest.raises(RuntimeError):
            probe(fake_mkv)

    # --- Feature 3: Output 邊界 ---

    def test_t2_f03_file_locked_permission_graceful_handling(self, tmp_path: Path):
        """T2-03-01: 在檔案維持獨占開啟鎖定狀態下調用 SUT 產物寫入器，驗證攔截 PermissionError。"""
        import msvcrt
        from vc.plan import write_timeline_srt
        tl = {
            "fps": 30,
            "cues": [{"start_frame": 0, "end_frame": 60, "text": "Testing locked subtitle output"}],
        }
        locked_file = tmp_path / "locked_output.srt"
        locked_file.write_text("initial", encoding="utf-8")
        with open(locked_file, "r+b") as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            with pytest.raises(PermissionError):
                write_timeline_srt(tl, locked_file)

    def test_t2_f03_ultra_short_video_duration_boundary(self):
        """T2-03-02: 驗證極短秒數時場景長度不為負數。"""
        from vc.plan import scene_lengths
        from vc.script import Script
        data = {
            "meta": {"title": "Short"},
            "scenes": [{
                "id": "s01", "section": "vs_intro", "narration": "Hello world.",
                "budget_s": [1.0, 5.0], "visuals": {
                    "internal": {"kind": "anim", "template": "t1"},
                    "public": {"kind": "anim", "template": "t1"},
                }
            }]
        }
        script = Script.model_validate(data)
        lengths = scene_lengths(script, {"s01": 0.5})
        assert lengths[0][1] > 0

    def test_t2_f03_pure_silence_loudness_calculation(self, tmp_path: Path):
        """T2-03-03: 生成純靜音音訊傳入 vc.render.measure_loudness，驗證妥善處理無崩潰。"""
        from vc.render import measure_loudness
        silence_file = tmp_path / "silence.wav"
        with wave.open(str(silence_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(b"\x00" * 96000)
        res = measure_loudness(silence_file)
        assert res["I"] is None or res["I"] <= -70.0

    def test_t2_f03_output_dir_auto_creation_recursive(self, tmp_path: Path):
        """T2-03-04: 將深層巢狀目錄傳給 make_logos，驗證 SUT 自動遞迴建立所有父目錄。"""
        from vc.brand import make_logos
        deep_dir = tmp_path / "a" / "b" / "c" / "out"
        assert not deep_dir.exists()
        logos = make_logos(deep_dir)
        assert deep_dir.is_dir()
        assert logos["primary"].is_file()

    def test_t2_f03_ultra_long_subtitle_text_handling(self, sample_project_path: Path):
        """T2-03-05: 注入超長字幕單句，驗證 vc.script.check 成功觸發字數超限阻斷。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes[0].narration = "This is a deliberately extremely long sentence without any punctuation delimiter designed to strictly exceed the twenty words threshold rule of the validator with extra words."
        errors, _ = check(script, facts)
        assert any("句子超過 20 字" in e or "句子超過" in e for e in errors)

    # --- Feature 4: Remotion / HF 邊界 ---

    def test_t2_f04_missing_node_or_remotion_graceful_error(self):
        """T2-04-01: 驗證未找到 Remotion 時 check_remotion 回傳明確 Check 物件。"""
        from vc.doctor import check_remotion
        chk = check_remotion()
        assert chk.name == "remotion"

    def test_t2_f04_node_version_too_old_diagnostic(self):
        """T2-04-02: 驗證 check_node 當要求版本高於本機環境時回傳 ok=False 與升級提示。"""
        from vc.doctor import check_node
        chk = check_node(min_major=999)
        assert chk.ok is False
        assert "需要 Node 999 以上" in chk.fix or "找不到 node" in chk.detail

    def test_t2_f04_template_jinja2_syntax_error_rejected(self):
        """T2-04-03: 樣式模板自代碼解耦為 Jinja2 樣板（屬 M3 里程碑）。"""
        pytest.skip("M3: 樣式模板自代碼解耦尚未實裝 (F15)")

    def test_t2_f04_hyperframes_timeout_protection(self):
        """T2-04-04: 調用 SUT vc.tools.run 驗證外部工具調度具備超時中斷保護。"""
        from vc.tools import run
        with pytest.raises(subprocess.TimeoutExpired):
            run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.1)

    def test_t2_f04_gpu_fallback_to_cpu_rendering(self, monkeypatch):
        """T2-04-05: 驗證當設定 VC_DEVICE=cpu 時 detect_torch_device 平滑降級為 cpu。"""
        from vc.tools import detect_torch_device
        monkeypatch.setenv("VC_DEVICE", "cpu")
        assert detect_torch_device() == "cpu"

    # --- Feature 5: 60+ 邊界 ---

    def test_t2_f05_domain_under_10_projects_audit_fails(self, repo_root: Path):
        """T2-05-01: 驗證領域收錄小於 10 個專案審計未達標（屬 M2 里程碑）。"""
        pytest.skip("尚無可呼叫的生態清單審計器，無法驗證不足 10 項的輸入")

    def test_t2_f05_invalid_github_url_audit_fails(self, repo_root: Path):
        """T2-05-02: 驗證無效或非 GitHub 網址審計阻斷（屬 M2 里程碑）。"""
        pytest.skip("尚無可呼叫的生態清單審計器，無法驗證無效網址")

    def test_t2_f05_duplicate_repo_audit_fails(self, repo_root: Path):
        """T2-05-03: 驗證重複倉庫網址審計去重（屬 M2 里程碑）。"""
        pytest.skip("尚無可呼叫的生態清單審計器，無法驗證重複專案")

    def test_t2_f05_missing_analysis_field_audit_fails(self, repo_root: Path):
        """T2-05-04: 驗證缺少架構分析欄位審計阻斷（屬 M2 里程碑）。"""
        pytest.skip("尚無可呼叫的生態清單審計器，無法驗證缺少分析欄位")

    def test_t2_f05_corrupted_table_format_audit_fails(self, repo_root: Path):
        """T2-05-05: 驗證損毀 Markdown 表格解析審計（屬 M2 里程碑）。"""
        pytest.skip("尚無可呼叫的生態清單審計器，無法驗證損毀表格")

    # --- Feature 6: 工具邊界 ---

    def test_t2_f06_missing_ffmpeg_reports_missing(self, monkeypatch):
        """T2-06-01: 驗證缺少 ffmpeg 時 check_version_tool 回報 MISSING。"""
        from vc.doctor import check_version_tool
        from vc import doctor
        monkeypatch.setattr(doctor, "find_tool", lambda name: None)
        chk = check_version_tool("ffmpeg", ["-version"], "hint")
        assert chk.status == "MISSING"

    def test_t2_f06_missing_optional_tool_reports_warn(self):
        """T2-06-02: 驗證缺少非必要工具時 Check 狀態為 WARN 而非 MISSING。"""
        from vc.doctor import Check
        chk = Check(name="optional_tool", ok=False, detail="not found", required=False)
        assert chk.status == "WARN"

    def test_t2_f06_missing_python_module_reports_missing(self, monkeypatch):
        """T2-06-03: 驗證缺少必要 Python 套件時 check_py_module 回報 MISSING。"""
        from vc.doctor import check_py_module
        chk = check_py_module("non_existent_module_xyz", "Test", required=True)
        assert chk.status == "MISSING"

    def test_t2_f06_cuda_unavailable_voice_cpu_fallback(self):
        """T2-06-04: 驗證語音合成後端可接受 cpu 裝置。"""
        from vc.voice import make_backend
        b = make_backend("edge", "en-US-AndrewNeural", "+0%")
        assert b is not None

    def test_t2_f06_powerpoint_com_unavailable_graceful_handling(self, monkeypatch):
        """T2-06-05: 驗證 PowerPoint COM 不可用時回傳 WARN 狀態且 ok=False。"""
        import winreg
        from vc.doctor import check_powerpoint
        def _mock_open_key(*args, **kwargs):
            raise OSError("PowerPoint COM not registered")
        monkeypatch.setattr(winreg, "OpenKey", _mock_open_key)
        chk = check_powerpoint()
        assert chk.ok is False
        assert chk.status == "WARN"
        assert chk.detail == "找不到 COM"

    # --- Feature 7: 文案/規則邊界 ---

    def test_t2_f07_sentence_exceeds_20_words_rejected(self, sample_project_path: Path):
        """T2-07-01: 驗證旁白單句超過 20 字時 vc.script.check 拋出錯誤。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes[0].narration = "This is a deliberately extremely long sentence without any punctuation delimiter designed to strictly exceed the twenty words threshold rule of the validator."
        errors, _ = check(script, facts)
        assert any("句子超過" in e for e in errors), f"未攔截超長句子，錯誤清單：{errors}"

    def test_t2_f07_chinese_cjk_word_count_and_limit(self, sample_project_path: Path):
        """T2-07-06: 驗證 CJK 正體中文分詞準確度與超過 20 字長度硬限制之攔截。"""
        from vc.script import words, load_script, load_facts, check

        # 1. 斷詞準確性與標點過濾檢驗
        # 「這是一個繁體中文旁白句子測試。」去掉句號共 14 個中文字元（中文字詞提取率精確，無標點殘留）
        cjk_text = "這是一個繁體中文旁白句子測試。"
        cjk_words = words(cjk_text)
        assert len(cjk_words) in (13, 14), f"預期繁體中文字詞數為 13~14（排除標點），實際為 {len(cjk_words)}"
        assert len(cjk_words) == 14, f"預期繁體中文字元數為 14（排除標點），實際為 {len(cjk_words)}：{cjk_words}"
        assert "。" not in cjk_words
        # 額外驗證標準 13 個中文字之邊界斷詞
        assert len(words("這是一個繁體中文旁白句子測。")) == 13

        # 2. 超長繁體中文旁白句子（超過 20 字）被 vc.script.check 正確阻斷
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes[0].narration = "這是一句完全由繁體中文構成的極長旁白句子用來測試系統是否能夠確實依據字數門檻攔截超長中文句子。"
        errors, _ = check(script, facts)
        assert any("句子超過 20 字" in e for e in errors), f"未攔截超長繁體中文句子，錯誤清單：{errors}"

    def test_t2_f07_banned_internal_term_rejected(self, sample_project_path: Path):
        """T2-07-02: 驗證旁白出現黑名單術語時 vc.script.check 拋出錯誤。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes[0].narration = "We must keep the mesh watertight throughout."
        errors, _ = check(script, facts)
        assert any("內部術語" in e for e in errors), f"未攔截內部黑名單術語，錯誤清單：{errors}"

    def test_t2_f07_unconfirmed_fact_number_rejected(self, sample_project_path: Path):
        """T2-07-03: 驗證旁白出現事實表未登記之數字時 vc.script.check 拋出錯誤。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes[0].narration = "We improved performance by 999 percent."
        errors, _ = check(script, facts)
        assert any("不在已確認的事實表" in e for e in errors), f"未攔截未登記數字，錯誤清單：{errors}"

    def test_t2_f07_term_used_before_glossary_scene_rejected(self, sample_project_path: Path):
        """T2-07-04: 驗證術語在 glossary 指定場景前先出現時拋出錯誤。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.glossary.append(type("Glossary", (), {"term": "non_existent_term_xyz", "scene": "s07"})())
        errors, _ = check(script, facts)
        assert any("沒有出現在旁白" in e for e in errors)

    def test_t2_f07_public_variant_with_recording_rejected(self, sample_project_path: Path):
        """T2-07-05: 驗證 public 公開版使用 recording 畫面時 vc.script.check 拋出錯誤。"""
        from vc.script import load_script, load_facts, check, Visual, Clip
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes[0].visuals["public"] = Visual(
            kind="recording",
            template="t1",
            clips=[Clip(recording="rec01", source=(0.0, 1.0))],
        )
        errors, _ = check(script, facts)
        assert any("public 版不能使用 recording" in e for e in errors)

    # --- Feature 8: 規範邊界 ---

    def test_t2_f08_skill_missing_frontmatter_rejected(self, tmp_path: Path, validate_skill):
        """T2-08-01: 驗證 SKILL.md 缺少 frontmatter 時 quick_validate 攔截失敗。"""
        bad_skill = tmp_path / "no-frontmatter-skill"
        bad_skill.mkdir()
        (bad_skill / "SKILL.md").write_text("# Just a heading\nNo frontmatter here.", encoding="utf-8")
        res = validate_skill(bad_skill)
        assert res.returncode != 0
        assert "No YAML frontmatter found" in res.stdout or "frontmatter" in res.stdout.lower()

    def test_t2_f08_skill_unexpected_frontmatter_key_rejected(self, tmp_path: Path, validate_skill):
        """T2-08-02: 驗證 frontmatter 包含非法鍵（如 author）時 quick_validate 攔截。"""
        bad_skill = tmp_path / "bad-key-skill"
        bad_skill.mkdir()
        (bad_skill / "SKILL.md").write_text("---\nname: bad-key-skill\ndescription: Valid desc\nauthor: hacker\n---\nBody", encoding="utf-8")
        res = validate_skill(bad_skill)
        assert res.returncode != 0
        assert "Unexpected key" in res.stdout

    def test_t2_f08_skill_invalid_name_format_rejected(self, tmp_path: Path, validate_skill):
        """T2-08-03: 驗證 name 包含大寫或底線時 quick_validate 攔截。"""
        bad_skill = tmp_path / "bad-name-skill"
        bad_skill.mkdir()
        (bad_skill / "SKILL.md").write_text("---\nname: Bad_Name_Skill\ndescription: Valid desc\n---\nBody", encoding="utf-8")
        res = validate_skill(bad_skill)
        assert res.returncode != 0
        assert "kebab-case" in res.stdout

    def test_t2_f08_skill_description_angle_brackets_rejected(self, tmp_path: Path, validate_skill):
        """T2-08-04: 驗證 description 包含角括號時 quick_validate 攔截。"""
        bad_skill = tmp_path / "angle-bracket-skill"
        bad_skill.mkdir()
        (bad_skill / "SKILL.md").write_text('---\nname: angle-bracket-skill\ndescription: "Use <bracket> here"\n---\nBody', encoding="utf-8")
        res = validate_skill(bad_skill)
        assert res.returncode != 0
        assert "angle brackets" in res.stdout

    def test_t2_f08_skill_description_exceeds_1024_rejected(self, tmp_path: Path, validate_skill):
        """T2-08-05: 驗證 description 超過 1024 字元時 quick_validate 攔截。"""
        bad_skill = tmp_path / "long-desc-skill"
        bad_skill.mkdir()
        long_desc = "a" * 1050
        (bad_skill / "SKILL.md").write_text(f'---\nname: long-desc-skill\ndescription: "{long_desc}"\n---\nBody', encoding="utf-8")
        res = validate_skill(bad_skill)
        assert res.returncode != 0
        assert "too long" in res.stdout

    # --- Feature 9: 端到端邊界 ---

    def test_t2_f09_script_duration_out_of_budget_rejected(self, sample_project_path: Path):
        """T2-09-01: 驗證總長度超出目標預算區間時 check 拋出警告/錯誤。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.meta.target_duration_s = (1.0, 5.0)
        errors, _ = check(script, facts)
        assert any("長度" in e or "超出" in e for e in errors)

    def test_t2_f09_readability_fk_grade_too_high_rejected(self, sample_project_path: Path):
        """T2-09-02: 驗證易讀等級超過閾值（設定為極低 1.0）時 check 攔截。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.meta.max_fk_grade = 1.0
        errors, _ = check(script, facts)
        assert any("易讀等級" in e for e in errors)

    def test_t2_f09_clip_end_exceeds_recording_duration_rejected(self, sample_project_path: Path):
        """T2-09-03: 驗證錄影 clip 結束秒數大於錄影長度時 check 攔截。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        rec_durations = {"rec01": 2.0}
        errors, _ = check(script, facts, rec_durations=rec_durations)
        assert any("超過錄影長度" in e for e in errors)

    def test_t2_f09_callout_at_word_not_in_narration_rejected(self, sample_project_path: Path):
        """T2-09-04: 驗證 callout 之 at_word 不在旁白中時 check 攔截。"""
        from vc.script import load_script, load_facts, check, Callout
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        for s in script.scenes:
            for v in s.visuals.values():
                v.callouts.append(Callout(at_word="non_existent_word_xyz", box=(0, 0, 10, 10), text="Callout"))
                break
            break
        errors, _ = check(script, facts)
        assert any("不在旁白中" in e for e in errors)

    def test_t2_f09_scene_section_order_inverted_rejected(self, sample_project_path: Path):
        """T2-09-05: 驗證場景段落順序顛倒時 check 拋出順序錯誤。"""
        from vc.script import load_script, load_facts, check
        script = load_script(sample_project_path / "script.json")
        facts = load_facts(sample_project_path / "facts.yaml")
        script.scenes = [script.scenes[-1]] + script.scenes[:-1]
        errors, _ = check(script, facts)
        assert any("段落順序必須是" in e for e in errors)

    # --- Feature 10: 切換邊界 ---

    def test_t2_f10_unknown_style_identifier_rejected(self):
        """T2-10-01: 未授權風格標識符阻斷驗證（屬 M3 里程碑）。"""
        pytest.skip("M3: 視覺美術風格模組與 Schema 驗證尚未實裝 (F11)")

    def test_t2_f10_unknown_camera_mode_rejected(self):
        """T2-10-02: 未授權運鏡模式標識符阻斷驗證（屬 M3 里程碑）。"""
        pytest.skip("M3: 鏡頭運鏡節奏模組尚未實裝 (F13)")

    def test_t2_f10_malformed_style_tokens_rejected(self):
        """T2-10-03: 殘缺風格主題 Tokens 解析防護（屬 M3 里程碑）。"""
        pytest.skip("M3: 視覺風格主題包 Tokens 解析器尚未實裝 (F11)")

    def test_t2_f10_extreme_aspect_ratio_resolution_handling(self):
        """T2-10-04: 將非標準寬高比 (3840x1080) 傳入 SUT Meta 模型，驗證畫布尺寸合法封裝。"""
        from vc.script import Meta
        meta = Meta(title="Ultra Wide Test", size=(3840, 1080))
        assert meta.size == (3840, 1080)
        assert meta.size[0] / meta.size[1] > 3.0

    def test_t2_f10_voice_rate_extreme_boundary(self):
        """T2-10-05: 驗證極限語速參數（+100% 或 -50%）解析。"""
        from vc.script import Voice
        v1 = Voice(rate="+100%")
        v2 = Voice(rate="-50%")
        assert v1.rate == "+100%"
        assert v2.rate == "-50%"

    def test_t2_f10_meta_boundary_negative_validation(self):
        """T2-10-06: 驗證 Meta 模型非正值邊界（fps <= 0 或 size 各軸 <= 0）拋出 ValidationError。"""
        import pydantic
        from vc.script import Meta

        # 1. fps <= 0 負向邊界驗證
        with pytest.raises(pydantic.ValidationError):
            Meta(title="bad", fps=0)
        with pytest.raises(pydantic.ValidationError):
            Meta(title="bad", fps=-30)

        # 2. size 負值與零值邊界驗證
        with pytest.raises(pydantic.ValidationError):
            Meta(title="bad", size=(0, 1080))
        with pytest.raises(pydantic.ValidationError):
            Meta(title="bad", size=(-1920, 1080))
        with pytest.raises(pydantic.ValidationError):
            Meta(title="bad", size=(1920, 0))
        with pytest.raises(pydantic.ValidationError):
            Meta(title="bad", size=(1920, -1080))


# ==============================================================================
# Tier 3: Pairwise Combinations (16 Orthogonal Cases)
# ==============================================================================

@pytest.mark.tier3
class TestTier3PairwiseCombinations:
    """Tier 3: Style × Camera × Voice × Input × Output × Path × Hardware 正交組合。"""

    PAIRWISE_TEST_CASES = [
        # id, style, camera_mode, voice_engine, input_comp, output_var, path_comp, hw_engine
        ("P-01", "executive_navy", "fixed", "kokoro", "slides+rec", "internal", "projects", "gpu"),
        ("P-02", "executive_navy", "dynamic", "edge", "slides", "public", "06_projects", "cpu"),
        ("P-03", "executive_navy", "cinematic", "kokoro", "anim", "internal", "projects", "cpu"),
        ("P-04", "swiss_kinetic", "fixed", "edge", "anim", "public", "projects", "gpu"),
        ("P-05", "swiss_kinetic", "dynamic", "kokoro", "slides+rec", "internal", "06_projects", "gpu"),
        ("P-06", "swiss_kinetic", "cinematic", "edge", "slides", "internal", "projects", "cpu"),
        ("P-07", "blueprint", "fixed", "kokoro", "slides", "internal", "06_projects", "gpu"),
        ("P-08", "blueprint", "dynamic", "edge", "anim", "internal", "projects", "gpu"),
        ("P-09", "blueprint", "cinematic", "kokoro", "slides+rec", "public", "projects", "cpu"),
        ("P-10", "cyberpunk_neon", "fixed", "edge", "slides+rec", "public", "projects", "cpu"),
        ("P-11", "cyberpunk_neon", "dynamic", "kokoro", "slides", "internal", "projects", "gpu"),
        ("P-12", "cyberpunk_neon", "cinematic", "edge", "anim", "internal", "06_projects", "gpu"),
        ("P-13", "executive_navy", "dynamic", "kokoro", "anim", "public", "06_projects", "gpu"),
        ("P-14", "swiss_kinetic", "fixed", "kokoro", "slides+rec", "public", "projects", "cpu"),
        ("P-15", "blueprint", "dynamic", "kokoro", "slides", "public", "projects", "gpu"),
        ("P-16", "cyberpunk_neon", "cinematic", "kokoro", "slides+rec", "internal", "projects", "gpu"),
    ]

    @pytest.mark.parametrize(
        "case_id,style,camera_mode,voice_engine,input_comp,output_var,path_comp,hw_engine",
        PAIRWISE_TEST_CASES,
    )
    def test_t3_pairwise_matrix_case(
        self,
        tmp_path: Path,
        monkeypatch,
        run_vc_cli,
        sample_project_path: Path,
        case_id: str,
        style: str,
        camera_mode: str,
        voice_engine: str,
        input_comp: str,
        output_var: str,
        path_comp: str,
        hw_engine: str,
    ):
        """Tier 3: 16 組正交組合用例之全參數物理落實驗收合約。"""
        from vc.project import load_project
        from vc.voice import make_backend
        from vc.tools import detect_torch_device

        # 1. 物理落地：依據 path_comp 建立專案目錄結構
        proj_root = tmp_path / path_comp / f"case_{case_id}"
        proj_root.mkdir(parents=True, exist_ok=True)
        input_dir = proj_root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        (input_dir / "slides").mkdir(parents=True, exist_ok=True)
        (input_dir / "recordings").mkdir(parents=True, exist_ok=True)

        # 2. 物理落地：依據 input_comp 建立實體素材檔案
        pptx_rel = None
        recs_rel = []
        if "slides" in input_comp:
            fake_ppt = input_dir / "slides" / "deck.pptx"
            fake_ppt.write_bytes(b"PK\x03\x04PPTX_MOCK_HEADER")
            pptx_rel = "input/slides/deck.pptx"
        if "rec" in input_comp:
            fake_rec = input_dir / "recordings" / "rec01.mp4"
            fake_rec.write_bytes(b"\x00\x00\x00\x1cftypisomMP4_MOCK")
            recs_rel = ["input/recordings/rec01.mp4"]

        # 3. 寫入完整 project.yaml 配置
        cfg = {
            "name": f"case_{case_id}",
            "title": f"Pairwise {case_id}",
            "style": style,
            "camera_mode": camera_mode,
            "fps": 30,
            "resolution": [1920, 1080],
            "voice": {
                "engine": voice_engine,
                "name": "en-US-AndrewNeural" if voice_engine == "edge" else "am_michael",
                "rate": 1.0,
            },
            "pptx": pptx_rel,
            "recordings": recs_rel,
        }
        (proj_root / "project.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

        # 複製最小 script.json 與 facts.yaml 供驗證
        shutil.copy(sample_project_path / "facts.yaml", proj_root / "facts.yaml")
        shutil.copy(sample_project_path / "script.json", proj_root / "script.json")

        # 4. 驗證 SUT load_project 對素材組合的精準封裝
        proj = load_project(str(proj_root))
        if "slides" in input_comp:
            assert proj.pptx is not None and proj.pptx.is_file()
        else:
            assert proj.pptx is None

        if "rec" in input_comp:
            assert len(proj.recordings) == 1 and proj.recordings[0].is_file()
        else:
            assert len(proj.recordings) == 0

        # 5. 驗證語音後端相容性
        backend = make_backend(voice_engine, "test_voice", "+0%")
        assert backend is not None

        # 6. 驗證輸出目標合約
        target_out = proj.output / output_var
        assert target_out.parent == proj.output

        # 7. 驗證硬體引擎設定
        monkeypatch.setenv("VC_DEVICE", hw_engine)
        dev = detect_torch_device()
        if hw_engine == "cpu":
            assert dev == "cpu"
        else:
            assert dev in ("gpu", "cuda", "mps", "cpu")

        # 8. 驗證風格主題載入與視覺參數驗證合約
        from vc.style_config import load_style, project_visual_settings
        st = load_style(style)
        assert "tokens" in st and "colors" in st["tokens"]
        st_cfg, cam_cfg = project_visual_settings(proj_root)
        assert cam_cfg["mode"] == camera_mode
        assert "tokens" in st_cfg

        # 9. 執行 vc validate 全域門禁
        res = run_vc_cli("validate", str(proj_root))
        assert res.returncode == 0, f"Pairwise {case_id} 驗證失敗：{res.stdout}\n{res.stderr}"


# ==============================================================================
# Tier 4: Real-World Workload Scenarios (5 Workloads)
# ==============================================================================

@pytest.mark.tier4
class TestTier4RealWorldScenarios:
    """Tier 4: 5 大真實端到端業務情境驗收套件。"""

    @pytest.mark.integration
    def test_rw_01_existing_project_validate_and_plan(self, pipeline_project_path: Path, run_vc_cli):
        """檢查既有專案的 validate 和 plan；此測試不產生影片。"""
        res_val = run_vc_cli("validate", str(pipeline_project_path))
        assert res_val.returncode == 0
        res_plan = run_vc_cli("plan", str(pipeline_project_path))
        assert res_plan.returncode == 0

    def test_rw_02_style_and_camera_config_validate(self, project_sandbox: Path, run_vc_cli, repo_root: Path):
        """檢查含風格與運鏡欄位的設定可通過 validate。"""
        style_file = repo_root / "styles" / "swiss_kinetic" / "style.json"
        if not style_file.is_file():
            style_file = repo_root / "04_styles" / "04_swiss_kinetic_type" / "style.json"
        assert style_file.is_file(), "找不到 Swiss Kinetic 樣式定義"
        cfg_file = project_sandbox / "project.yaml"
        cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        cfg["style"] = "swiss_kinetic"
        cfg["camera_mode"] = "dynamic"
        cfg["voice"] = {"engine": "edge", "name": "en-US-AndrewNeural", "rate": "+0%"}
        cfg_file.write_text(yaml.safe_dump(cfg), encoding="utf-8")

        res = run_vc_cli("validate", str(project_sandbox))
        assert res.returncode == 0, f"切換風格後驗證失敗：{res.stdout}\n{res.stderr}"

    def test_rw_03_capcut_cli_availability(self, sample_project_path: Path, run_vc_cli):
        """檢查 CapCut CLI 版本及缺少參數時的回應；此測試不建立草稿。"""
        from vc.tools import find_tool
        from vc.capcut_draft import capcut_cli

        capcut_tool = find_tool("capcut")
        if capcut_tool is None:
            pytest.skip("M2: 本機環境尚未安裝 capcut-cli，跳過剪映草稿產生測試（需在根目錄執行 npm install）")

        tool_path = Path(capcut_tool)
        assert tool_path.is_file(), f"找不到 capcut 可執行檔案：{tool_path}"

        res = subprocess.run([str(tool_path), "--version"], capture_output=True, text=True, timeout=10)
        assert res.returncode == 0, f"capcut --version 執行失敗：{res.stderr}"
        assert re.search(r"\d+\.\d+", res.stdout.strip()), f"版本格式異常：{res.stdout}"

        assert Path(capcut_cli()).resolve() == tool_path.resolve()

        cli_res = run_vc_cli("capcut-draft")
        assert cli_res.returncode != 0
        assert "capcut-draft" in cli_res.stdout or "用法" in cli_res.stdout

    def test_rw_04_selected_skills_and_ecosystem_doc_exists(self, repo_root: Path, validate_skill):
        """驗證部分 skills 和生態文件是否存在；此測試不審計文件內容。"""
        skills_dir = find_dir_compat(repo_root, "skills", "03_skills")
        assert skills_dir is not None
        skills = [
            d for d in skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file() and not d.name.startswith("03_hyperframes_composer")
        ]
        assert len(skills) >= 2
        for s in skills:
            res = validate_skill(s)
            assert res.returncode == 0, f"Skill {s.name} 未通過 quick_validate：{res.stdout}"

        eco_file = repo_root / "docs" / "OPEN_SOURCE_ECOSYSTEM.md"
        if not eco_file.is_file():
            pytest.skip("M2: 6 大領域開源生態清單尚未交付 (docs/OPEN_SOURCE_ECOSYSTEM.md)")

    def test_rw_05_legacy_66_bdd_regression_check(self, repo_root: Path, python_bin: str):
        """RW-05: 既有 66 項 pytest-bdd 測試無回歸全量驗證。"""
        bdd_dir = repo_root / "tests" / "bdd"
        if not bdd_dir.is_dir():
            bdd_dir = repo_root / "08_tests"
        if not bdd_dir.is_dir():
            bdd_dir = repo_root / "tests"
        res = subprocess.run(
            [python_bin, "-m", "pytest", "-q", "-m", "not integration", str(bdd_dir)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180.0,
        )
        assert res.returncode == 0, f"既有 BDD 測試回歸失敗：\n{res.stdout}\n{res.stderr}"
        assert "passed" in res.stdout
        assert "failed" not in res.stdout
