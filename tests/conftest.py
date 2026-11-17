"""Video Creator 4-Tier 黑盒 E2E 驗證套件 conftest.py

提供全域測試 fixture、路徑探測、臨時專案沙盒、管線產物專案與 CLI 執行輔助函式。
落實隔離沙盒與同磁碟防護，杜絕 Windows 跨磁碟相對路徑崩潰與目錄殘留污染。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Generator

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_VALIDATOR_PATH = Path(r"D:\Ikaros\skill-creator\scripts\quick_validate.py")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """傳回專案根目錄路徑。"""
    return REPO_ROOT


@pytest.fixture(scope="session", autouse=True)
def sanitize_test_workspace(repo_root: Path) -> Generator[None, None, None]:
    """會話級 autouse fixture：在測試套件執行前後自動掃描並清理任何暫存產物或殘留資料夾。"""
    def _cleanup():
        for parent_name in ("projects", "06_projects"):
            parent = repo_root / parent_name
            if not parent.is_dir():
                continue
            for item in parent.iterdir():
                if item.is_dir() and (
                    item.name.startswith(("test_", "case_P-", "case_", "sandbox_", "temp_"))
                    or item.name in ("sandbox_project", "tmp_proj")
                ):
                    shutil.rmtree(item, ignore_errors=True)

    _cleanup()
    try:
        yield
    finally:
        _cleanup()


@pytest.fixture(scope="session")
def python_bin() -> str:
    """傳回當前 Python 解譯器路徑（.venv）。"""
    return sys.executable


@pytest.fixture(scope="session")
def quick_validate_script() -> Path:
    """傳回 skill-creator 的 quick_validate.py 腳本路徑。"""
    return SKILL_VALIDATOR_PATH


@pytest.fixture(scope="session")
def sample_project_path(repo_root: Path) -> Path:
    """動態定位示範專案目錄（優先 projects/_sample，次選 06_projects/_sample）。"""
    cand = repo_root / "projects" / "_sample"
    if cand.is_dir():
        return cand
    legacy = repo_root / "06_projects" / "_sample"
    if legacy.is_dir():
        return legacy
    pytest.skip("找不到示範專案 _sample（projects/_sample 或 06_projects/_sample 不存在）")


@pytest.fixture(scope="session")
def pipeline_project_path(repo_root: Path, sample_project_path: Path) -> Path:
    """動態定位具備完整真實前處理產物的管線專案（優先 projects/midsurface）。"""
    midsurface = repo_root / "projects" / "midsurface"
    if midsurface.is_dir() and (midsurface / "work" / "timeline.json").is_file():
        return midsurface
    return sample_project_path


@pytest.fixture
def run_vc_cli(repo_root: Path, python_bin: str) -> Callable[..., subprocess.CompletedProcess]:
    """輔助函式：執行 python -m vc <subcommand> [args] 並傳回 CompletedProcess。"""
    def _run(*args: str, check: bool = False, timeout: float = 60.0, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        current_env = os.environ.copy()
        current_env.setdefault("PYTHONIOENCODING", "utf-8")  # 子行程輸出固定為 UTF-8，避免 cp950 亂碼
        if env:
            current_env.update(env)
        cmd = [python_bin, "-m", "vc", *args]
        return subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=check,
            env=current_env,
        )
    return _run


@pytest.fixture
def validate_skill(python_bin: str, quick_validate_script: Path) -> Callable[[Path], subprocess.CompletedProcess]:
    """輔助函式：調用 quick_validate.py 驗證指定 skill 目錄。"""
    def _validate(skill_dir: Path) -> subprocess.CompletedProcess:
        if not quick_validate_script.is_file():
            pytest.skip(f"skill-creator 驗證腳本不存在：{quick_validate_script}")
        return subprocess.run(
            [python_bin, str(quick_validate_script), str(skill_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30.0,
        )
    return _validate


@pytest.fixture
def project_sandbox(tmp_path: Path, sample_project_path: Path) -> Generator[Path, None, None]:
    """建立自包含的隔離測試專案目錄，具有標準輸入與結構，並在測試後自動清理。"""
    sandbox_dir = tmp_path / "sandbox_project"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    input_dir = sandbox_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "slides").mkdir(parents=True, exist_ok=True)
    (input_dir / "recordings").mkdir(parents=True, exist_ok=True)

    # 建立最小合法 project.yaml
    cfg = {
        "name": "sandbox_project",
        "title": "Sandbox Test Project",
        "style": "executive_navy",
        "camera_mode": "fixed",
        "fps": 30,
        "resolution": [1920, 1080],
        "voice": {
            "engine": "kokoro",
            "name": "am_michael",
            "rate": 1.05,
        },
    }
    (sandbox_dir / "project.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    # 複製或建立 facts.yaml
    src_facts = sample_project_path / "facts.yaml"
    if src_facts.is_file():
        shutil.copy(src_facts, sandbox_dir / "facts.yaml")
    else:
        facts = {
            "test_metric": {
                "value": "6 seconds",
                "spoken": ["six seconds", "6 seconds", "6 s"],
                "sources": ["benchmark"],
                "confirmed": True,
            }
        }
        (sandbox_dir / "facts.yaml").write_text(yaml.safe_dump(facts, sort_keys=False), encoding="utf-8")

    # 複製或建立 script.json
    src_script = sample_project_path / "script.json"
    if src_script.is_file():
        shutil.copy(src_script, sandbox_dir / "script.json")

    yield sandbox_dir
    # 自動清除沙盒
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir, ignore_errors=True)
