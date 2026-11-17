"""vc/craft_tools.py: 本機 Rust 創意工具鏈 (Office_adobe_CAD) 封裝模組。

封裝四大高效能無頭工具：
- DeckCraft: PPTX/Deckcraft 投影片無頭 1080p 繪製與格式轉換
- EffectCraft: After Effects 相容無頭合成、特效影格與影片渲染
- PhotoCraft: Photoshop PSD/圖片無頭圖層剖析、轉換與批次處理
- VectorCraft: 向量 (SVG, AI, PDF) 幾何無頭渲染與點陣化
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

# 預設本機路徑與備用路徑
DEFAULT_CRAFT_BASE = Path(r"D:\Ikaros\Office_adobe_CAD")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class CraftToolError(RuntimeError):
    """Craft 工具執行失敗異常。"""
    def __init__(self, tool: str, returncode: int, stderr: str, cmd: Sequence[str]):
        super().__init__(f"[{tool}] 執行失敗 (code {returncode}):\n{stderr[-1000:]}\n指令: {' '.join(cmd)}")
        self.tool = tool
        self.returncode = returncode
        self.stderr = stderr
        self.cmd = cmd


class CraftToolNotFoundError(FileNotFoundError):
    """找不到指定的 Craft 工具二進位檔案。"""


def resolve_craft_binary(tool_name: str) -> Path:
    """尋找指定工具的 CLI 二進位檔路徑。

    搜尋順序：
    1. 環境變數 CRAFT_TOOLS_DIR / OFFICE_ADOBE_CAD_DIR
    2. D:\\Ikaros\\Office_adobe_CAD\\<ToolName>\\<toolname>-cli.exe
    3. <PROJECT_ROOT>\\tools\\craft\\<toolname>-cli.exe
    4. 系統 PATH
    """
    env_dir = os.environ.get("CRAFT_TOOLS_DIR") or os.environ.get("OFFICE_ADOBE_CAD_DIR")
    candidates: list[Path] = []

    cli_name = f"{tool_name.lower()}-cli.exe"

    if env_dir:
        candidates.append(Path(env_dir) / tool_name / cli_name)
        candidates.append(Path(env_dir) / cli_name)

    candidates.append(DEFAULT_CRAFT_BASE / tool_name / cli_name)
    candidates.append(PROJECT_ROOT / "tools" / "craft" / cli_name)

    for p in candidates:
        if p.is_file():
            return p

    # 查系統 PATH
    which_p = shutil.which(cli_name) or shutil.which(f"{tool_name.lower()}-cli")
    if which_p:
        return Path(which_p)

    raise CraftToolNotFoundError(
        f"找不到 {tool_name} CLI 執行檔（預期為 {cli_name}）。"
        f"請確認 {DEFAULT_CRAFT_BASE}\\{tool_name} 存在或設定 CRAFT_TOOLS_DIR 環境變數。"
    )


def _run_craft(tool_name: str, args: list[str], timeout: float = 120) -> subprocess.CompletedProcess[str]:
    bin_path = resolve_craft_binary(tool_name)
    cmd = [str(bin_path), *args]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if res.returncode != 0:
        raise CraftToolError(tool_name, res.returncode, res.stderr or res.stdout, cmd)
    return res


# ==========================================
# 1. DeckCraft 封裝
# ==========================================
@dataclass
class DeckInfo:
    slides_count: int
    raw: dict[str, Any]


def deck_render_slides(
    pptx_path: Path,
    out_dir: Path,
    scale: int = 2,
    slide_index: int | None = None,
) -> list[Path]:
    """將 PPTX 或 .deckcraft 投影片渲染為 1920x1080 (scale=2) PNG 圖片序列。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    args = ["render", str(pptx_path)]
    if slide_index is not None:
        args.extend(["--slide", str(slide_index)])
    else:
        args.append("--all")
    args.extend(["--scale", str(scale), str(out_dir)])

    _run_craft("DeckCraft", args, timeout=180)
    # 收集產出的 PNG
    return sorted(out_dir.glob("slide-*.png"))


def deck_convert(in_path: Path, out_path: Path) -> Path:
    """轉換簡報格式（支援 .pptx, .deckcraft, .pdf, .md, .png, .gif）。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run_craft("DeckCraft", ["convert", str(in_path), str(out_path)], timeout=120)
    return out_path


def deck_info(in_path: Path) -> dict[str, Any]:
    """提取簡報 JSON 資訊（主題、版型與頁數）。"""
    res = _run_craft("DeckCraft", ["info", str(in_path)], timeout=30)
    return json.loads(res.stdout)


# ==========================================
# 2. EffectCraft 封裝
# ==========================================
def effect_render_frame(
    proj_path: Path | None,
    out_png: Path,
    comp: str = "-",
    frame: int | None = None,
    time_sec: float | None = None,
    demo: bool = False,
) -> Path:
    """渲染單一特效合成影格為高品質 PNG。"""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    args = ["render-frame"]
    if demo:
        args.append("--demo")
    elif proj_path:
        args.extend(["--project", str(proj_path)])

    if comp != "-":
        args.extend(["--comp", comp])
    if frame is not None:
        args.extend(["--frame", str(frame)])
    elif time_sec is not None:
        args.extend(["--time", str(time_sec)])

    args.extend(["--out", str(out_png)])
    _run_craft("EffectCraft", args, timeout=60)
    return out_png


def effect_render_video(
    proj_path: Path,
    out_video: Path,
    comp: str = "-",
    fmt: str = "h264",
    fps: int = 30,
    quality: str = "best",
) -> Path:
    """無頭批次導出合成影片（支援 h264, hevc, av1, prores, webm）。"""
    out_video.parent.mkdir(parents=True, exist_ok=True)
    args = [
        "render",
        "--project", str(proj_path),
        "--comp", comp,
        "--out", str(out_video),
        "--format", fmt,
        "--fps", str(fps),
        "--quality", quality,
    ]
    _run_craft("EffectCraft", args, timeout=600)
    return out_video


def effect_eval_script(script_code: str, proj_path: Path | None = None) -> str:
    """執行 After Effects 風格 JavaScript 物件模型腳本。"""
    args = ["script", "--eval", script_code]
    if proj_path:
        args.append(str(proj_path))
    res = _run_craft("EffectCraft", args, timeout=60)
    return res.stdout


# ==========================================
# 3. PhotoCraft 封裝
# ==========================================
def photo_convert(in_path: Path, out_path: Path, quality: int = 90) -> Path:
    """轉換圖片/PSD 檔案格式（支援 .psd, .pcraft, .png, .jpg, .webp 等）。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = ["convert", str(in_path), str(out_path), "--quality", str(quality)]
    _run_craft("PhotoCraft", args, timeout=60)
    return out_path


def photo_info(in_path: Path) -> dict[str, Any]:
    """讀取 PSD/圖片的 JSON 圖層結構樹、色版與尺寸。"""
    res = _run_craft("PhotoCraft", ["info", str(in_path)], timeout=30)
    return json.loads(res.stdout)


# ==========================================
# 4. VectorCraft 封裝
# ==========================================
def vector_convert(in_path: Path, out_path: Path, scale: float = 2.0) -> Path:
    """將向量圖檔 (SVG, AI, PDF) 轉換為高畫質點陣圖或向量格式。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = ["convert", str(in_path), str(out_path), "--scale", str(scale)]
    _run_craft("VectorCraft", args, timeout=60)
    return out_path


def vector_info(in_path: Path) -> dict[str, Any]:
    """獲取向量文檔結構與圖板 JSON 資訊。"""
    res = _run_craft("VectorCraft", ["info", str(in_path)], timeout=30)
    return json.loads(res.stdout)


# ==========================================
# 5. 健康診斷介面 (Health Diagnostic)
# ==========================================
def diagnose_craft_tools() -> dict[str, dict[str, Any]]:
    """診斷本機 4 大 Rust 創意工具之可用性與版本。"""
    tools = {
        "DeckCraft": "deckcraft-cli.exe",
        "EffectCraft": "effectcraft-cli.exe",
        "PhotoCraft": "photocraft-cli.exe",
        "VectorCraft": "vectorcraft-cli.exe",
    }
    report: dict[str, dict[str, Any]] = {}
    for name, _exe in tools.items():
        try:
            bin_p = resolve_craft_binary(name)
            res = subprocess.run(
                [str(bin_p), "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            report[name] = {
                "available": res.returncode == 0,
                "path": str(bin_p),
                "version": (res.stdout or res.stderr).strip().splitlines()[0] if res.returncode == 0 else "Error",
            }
        except Exception as e:
            report[name] = {
                "available": False,
                "path": None,
                "error": str(e),
            }
    return report
