"""環境檢查：列出管線需要的每個工具是否可用，缺少時附上修復方式。"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from vc.tools import ROOT, find_tool, run, use_system_certs

SETUP_HINT = "執行 09_scripts\\setup.ps1"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fix: str = ""
    required: bool = True

    @property
    def status(self) -> str:
        if self.ok:
            return "OK"
        return "MISSING" if self.required else "WARN"


# ---------- 個別檢查 ----------

def check_python(version: tuple[int, int] | None = None) -> Check:
    major, minor = version or sys.version_info[:2]
    ok = (major, minor) >= (3, 10) and (major, minor) <= (3, 12)
    return Check("python", ok, f"{major}.{minor}", "用 py -3.11 建立 .venv" if not ok else "")


# (模組名, 說明, 是否必要)
PY_MODULES = (
    ("torch", "PyTorch", True),
    ("whisper", "OpenAI Whisper", True),
    ("edge_tts", "Edge TTS", True),
    ("kokoro", "Kokoro TTS", True),
    ("soundfile", "音檔讀寫", True),
    ("scenedetect", "PySceneDetect", True),
    ("cv2", "OpenCV", True),
    ("pptx", "python-pptx", True),
    ("jiwer", "WER 計算", True),
    ("pydantic", "腳本格式驗證", True),
    ("pytest_bdd", "BDD 測試", True),
    ("textstat", "易讀度計算", True),
    ("yaml", "PyYAML", True),
    ("truststore", "Windows 憑證（公司網路 HTTPS）", True),
    ("espeakng_loader", "Kokoro 生字發音（espeak-ng）", False),
)


def check_py_module(module: str, label: str, required: bool) -> Check:
    found = importlib.util.find_spec(module) is not None
    return Check(f"py:{module}", found, label, "" if found else SETUP_HINT, required)


def check_cuda() -> Check:
    try:
        import torch  # 延遲匯入：torch 載入約需數秒
    except ImportError:
        return Check("cuda", False, "torch 未安裝", SETUP_HINT)
    if not torch.cuda.is_available():
        return Check("cuda", False, f"torch {torch.__version__} 無法使用 GPU", "安裝 CUDA 版 torch（見 09_scripts\\setup.ps1）")
    return Check("cuda", True, f"torch {torch.__version__} / {torch.cuda.get_device_name(0)}")


def check_ffmpeg_gpu_encoders() -> Check:
    from vc.media import gpu_encoders
    encs = gpu_encoders()
    if not encs:
        return Check("ffmpeg:gpu", False, "未偵測到硬體 H.264 編碼器（將自動回退 libx264）", "更新 GPU 驅動或確認 ffmpeg 含 nvenc/qsv/amf")
    return Check("ffmpeg:gpu", True, ", ".join(encs))


def parse_major(version_text: str) -> int | None:
    m = re.search(r"(\d+)\.\d+", version_text)
    return int(m.group(1)) if m else None


def check_node(min_major: int = 22) -> Check:
    exe = find_tool("node")
    if not exe:
        return Check("node", False, "找不到 node", "安裝 Node.js 22 以上")
    out = run([exe, "--version"]).stdout.strip()
    major = parse_major(out)
    ok = major is not None and major >= min_major
    return Check("node", ok, out, "" if ok else f"需要 Node {min_major} 以上（HyperFrames 要求）")


def check_version_tool(name: str, args: list[str], fix: str, required: bool = True) -> Check:
    exe = find_tool(name)
    if not exe:
        return Check(name, False, "找不到", fix, required)
    try:
        res = run([exe, *args], timeout=120)
    except Exception as exc:  # 逾時或無法執行都視為不可用，並保留原因
        return Check(name, False, f"執行失敗：{exc}", fix, required)
    text = (res.stdout or res.stderr).strip().splitlines()
    first = text[0] if text else ""
    return Check(name, res.returncode == 0, first[:80], "" if res.returncode == 0 else fix, required)


FFMPEG_ENCODERS = ("libx264", "libvpx-vp9", "prores_ks", "aac")


def check_ffmpeg_encoders() -> Check:
    exe = find_tool("ffmpeg")
    if not exe:
        return Check("ffmpeg:encoders", False, "ffmpeg 未安裝", SETUP_HINT)
    out = run([exe, "-hide_banner", "-encoders"]).stdout
    missing = [e for e in FFMPEG_ENCODERS if not re.search(rf"\s{re.escape(e)}\s", out)]
    if missing:
        return Check("ffmpeg:encoders", False, "缺少 " + ", ".join(missing), "改用 gyan.dev full build")
    return Check("ffmpeg:encoders", True, ", ".join(FFMPEG_ENCODERS))


def check_remotion() -> Check:
    pkg = ROOT / "remotion" / "node_modules" / "remotion" / "package.json"
    if not pkg.is_file() or not find_tool("remotion"):
        return Check("remotion", False, "remotion/node_modules 未安裝", "在 remotion\\ 執行 npm install")
    version = json.loads(pkg.read_text(encoding="utf-8")).get("version", "?")
    return Check("remotion", True, version)


def check_powerpoint() -> Check:
    try:
        import winreg
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application").Close()
        return Check("powerpoint", True, "COM 可用", required=False)
    except (ImportError, OSError):
        return Check("powerpoint", False, "找不到 COM", "只影響投影片預覽圖匯出", required=False)


def capcut_draft_dirs() -> list[Path]:
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    return [
        local / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
        local / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
    ]


def check_capcut_app() -> Check:
    found = [str(p) for p in capcut_draft_dirs() if p.is_dir()]
    if found:
        return Check("capcut-app", True, found[0], required=False)
    return Check("capcut-app", False, "找不到草稿資料夾", "開啟 CapCut 一次並建立任一專案", required=False)


def check_edge_tts_network() -> Check:
    """實際合成一句話，確認能連到微軟語音服務（公司 proxy 可能擋住）。"""
    try:
        import asyncio
        import edge_tts

        use_system_certs()

        async def _synth() -> int:
            size = 0
            async for chunk in edge_tts.Communicate("Test.", "en-US-AndrewNeural").stream():
                if chunk["type"] == "audio":
                    size += len(chunk["data"])
            return size

        size = asyncio.run(asyncio.wait_for(_synth(), timeout=30))
        return Check("edge-tts:network", size > 0, f"收到 {size} bytes 音訊", required=False)
    except Exception as exc:
        return Check("edge-tts:network", False, f"{type(exc).__name__}: {exc}"[:80], "改用 Kokoro 後端", required=False)


# ---------- 組合 ----------

def collect(deep: bool = False) -> list[Check]:
    checks: list[Callable[[], Check]] = [
        check_python,
        *[lambda m=m, l=l, r=r: check_py_module(m, l, r) for m, l, r in PY_MODULES],
        check_cuda,
        check_node,
        lambda: check_version_tool("ffmpeg", ["-version"], SETUP_HINT),
        lambda: check_version_tool("ffprobe", ["-version"], SETUP_HINT),
        check_ffmpeg_encoders,
        check_ffmpeg_gpu_encoders,
        lambda: check_version_tool("auto-editor", ["--version"], SETUP_HINT),
        lambda: check_version_tool("hyperframes", ["--version"], "在專案根目錄執行 npm install"),
        lambda: check_version_tool("capcut", ["--version"], "在專案根目錄執行 npm install"),
        check_remotion,
        check_powerpoint,
        check_capcut_app,
    ]
    if deep:
        checks.append(check_edge_tts_network)
    return [c() for c in checks]


def format_table(results: list[Check]) -> str:
    lines = [f"{'項目':<22}{'狀態':<9}說明"]
    for c in results:
        line = f"{c.name:<24}{c.status:<9}{c.detail}"
        if c.fix:
            line += f"  -> {c.fix}"
        lines.append(line)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    deep = "--deep" in argv
    results = collect(deep=deep)
    if "--json" in argv:
        print(json.dumps([asdict(c) | {"status": c.status} for c in results], ensure_ascii=False, indent=2))
    else:
        print(format_table(results))
    failed = [c.name for c in results if c.required and not c.ok]
    if failed:
        print(f"\n必要項目缺少 {len(failed)} 項：{', '.join(failed)}")
        return 1
    print("\n必要項目全部通過。")
    return 0
