"""scripts/verify_tools.py

Milestone 2 F09 外部工具可用性與相依性自檢腳本。
支援文字表格 (Rich / Plain text) 與 --json 結構化輸出。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

# 本機工具搜尋路徑優先序
LOCAL_BIN_DIRS = (
    REPO_ROOT / "tools" / "ffmpeg" / "bin",
    REPO_ROOT / "node_modules" / ".bin",
    REPO_ROOT / "packages" / "remotion" / "node_modules" / ".bin",
    REPO_ROOT / ".venv" / "Scripts",
)

OFFICE_ADOBE_CAD_DEFAULT = Path(r"D:\Ikaros\Office_adobe_CAD")


@dataclass
class ToolResult:
    name: str
    category: str  # Core / Pipeline / External / OfficeCraft
    status: str    # PASS / WARN / FAIL
    version: str
    required: bool
    latency_ms: float
    detail: str
    fix_hint: str = ""


def find_local_or_path(name: str) -> Optional[str]:
    exts = (".exe", ".cmd", ".bat", "")
    for d in LOCAL_BIN_DIRS:
        for ext in exts:
            p = d / f"{name}{ext}"
            if p.is_file():
                return str(p)
    # 查找系統 PATH
    for ext in exts:
        found = shutil.which(f"{name}{ext}")
        if found:
            return found
    return shutil.which(name)


def run_cmd(cmd: List[str], timeout: float = 15.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


class ToolVerifier:
    def __init__(self, deep: bool = False):
        self.deep = deep
        self.results: List[ToolResult] = []

    def check_python(self) -> ToolResult:
        t0 = time.perf_counter()
        v = sys.version_info
        ver_str = f"{v.major}.{v.minor}.{v.micro}"
        ok = (3, 10) <= (v.major, v.minor) <= (3, 12)
        latency = (time.perf_counter() - t0) * 1000
        return ToolResult(
            name="python",
            category="Core",
            status="PASS" if ok else "FAIL",
            version=ver_str,
            required=True,
            latency_ms=round(latency, 2),
            detail=f"解譯器路徑: {sys.executable}",
            fix_hint="建議建立 Python 3.11 虛擬環境: py -3.11 -m venv .venv" if not ok else "",
        )

    def check_node(self) -> ToolResult:
        t0 = time.perf_counter()
        exe = find_local_or_path("node")
        if not exe:
            return ToolResult("node", "Core", "FAIL", "N/A", True, 0.0, "找不到 node 可執行檔", "安裝 Node.js >= 22")
        res = run_cmd([exe, "--version"])
        ver = res.stdout.strip()
        m = re.search(r"v?(\d+)\.", ver)
        major = int(m.group(1)) if m else 0
        ok = major >= 22
        latency = (time.perf_counter() - t0) * 1000
        return ToolResult(
            name="node",
            category="Core",
            status="PASS" if ok else "FAIL",
            version=ver,
            required=True,
            latency_ms=round(latency, 2),
            detail=f"Node 執行期路徑: {exe}",
            fix_hint="HyperFrames 要求 Node.js >= 22" if not ok else "",
        )

    def check_ffmpeg(self) -> ToolResult:
        t0 = time.perf_counter()
        exe = find_local_or_path("ffmpeg")
        if not exe:
            return ToolResult(
                name="ffmpeg",
                category="Core",
                status="FAIL",
                version="N/A",
                required=True,
                latency_ms=0.0,
                detail="找不到 ffmpeg 可執行檔",
                fix_hint="請下載 FFmpeg 並置於 tools/ffmpeg/bin/ffmpeg.exe 或執行 09_scripts/setup.ps1",
            )
        res = run_cmd([exe, "-version"])
        first_line = res.stdout.splitlines()[0] if res.stdout else "Unknown"
        m = re.search(r"ffmpeg version\s+([^\s]+)", first_line)
        ver_str = m.group(1) if m else first_line[:30]

        enc_res = run_cmd([exe, "-hide_banner", "-encoders"])
        encoders = enc_res.stdout
        has_x264 = "libx264" in encoders
        has_aac = "aac" in encoders

        if not (has_x264 and has_aac):
            return ToolResult(
                name="ffmpeg",
                category="Core",
                status="FAIL",
                version=ver_str,
                required=True,
                latency_ms=(time.perf_counter() - t0) * 1000,
                detail=f"缺少必要編碼器 (libx264: {has_x264}, aac: {has_aac})",
                fix_hint="請更換為 gyan.dev full build 版本的 FFmpeg",
            )

        detail_msg = f"路徑: {exe} | 必要編碼器 (libx264, aac) 就緒"
        latency = (time.perf_counter() - t0) * 1000
        return ToolResult("ffmpeg", "Core", "PASS", ver_str, True, round(latency, 2), detail_msg)

    def check_ffmpeg_nvenc(self) -> ToolResult:
        t0 = time.perf_counter()
        exe = find_local_or_path("ffmpeg")
        if not exe:
            return ToolResult("ffmpeg:nvenc", "External", "WARN", "N/A", False, 0.0, "FFmpeg 未安裝", "")
        res = run_cmd([
            exe, "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.04",
            "-frames:v", "1", "-c:v", "h264_nvenc", "-f", "null", "-",
        ])
        ok = res.returncode == 0
        latency = (time.perf_counter() - t0) * 1000
        return ToolResult(
            name="ffmpeg:nvenc",
            category="External",
            status="PASS" if ok else "WARN",
            version="Hardware NVENC",
            required=False,
            latency_ms=round(latency, 2),
            detail="NVIDIA GPU 硬體編碼測試成功" if ok else "未偵測到 NVENC 硬體加速（自動回退 CPU libx264）",
            fix_hint="若具備 NVIDIA 顯卡請更新驅動程式" if not ok else "",
        )

    def check_pyjianyingdraft(self) -> ToolResult:
        t0 = time.perf_counter()
        spec = importlib.util.find_spec("pyjianyingdraft") or importlib.util.find_spec("pyJianYingDraft")
        tool_dir = REPO_ROOT / "tools" / "pyJianYingDraft"
        if spec is not None or tool_dir.is_dir():
            ver = "Installed"
            try:
                mod_name = spec.name if spec else "pyjianyingdraft"
                mod = importlib.import_module(mod_name)
                ver = getattr(mod, "__version__", "Available")
            except Exception:
                pass
            latency = (time.perf_counter() - t0) * 1000
            return ToolResult(
                name="pyJianYingDraft",
                category="Pipeline",
                status="PASS",
                version=str(ver),
                required=False,
                latency_ms=round(latency, 2),
                detail=f"剪映草稿生成庫就緒 ({'模組導入' if spec else '本地目錄'})",
            )
        latency = (time.perf_counter() - t0) * 1000
        return ToolResult(
            name="pyJianYingDraft",
            category="Pipeline",
            status="WARN",
            version="N/A",
            required=False,
            latency_ms=round(latency, 2),
            detail="未安裝 pyJianYingDraft（剪映草稿匯出將降級為純 MP4/SRT）",
            fix_hint="執行 pip install pyjianyingdraft 或 git clone 至 tools/pyJianYingDraft",
        )

    def check_recordly(self) -> ToolResult:
        t0 = time.perf_counter()
        cand_dirs = [REPO_ROOT / "tools" / "Recordly", REPO_ROOT / "external" / "Recordly"]
        found = next((d for d in cand_dirs if d.is_dir()), None)
        latency = (time.perf_counter() - t0) * 1000
        if found:
            has_pkg = (found / "package.json").is_file()
            return ToolResult(
                name="Recordly",
                category="External",
                status="PASS",
                version="Found",
                required=False,
                latency_ms=round(latency, 2),
                detail=f"錄影追焦工具目錄存在: {found} (package.json: {has_pkg})",
            )
        return ToolResult(
            name="Recordly",
            category="External",
            status="WARN",
            version="N/A",
            required=False,
            latency_ms=round(latency, 2),
            detail="未整合 Recordly（螢幕錄影將降級為靜態等比縮放，無自動追焦）",
            fix_hint="git clone https://github.com/webadderallorg/Recordly external/Recordly",
        )

    def check_ppt_master(self) -> ToolResult:
        t0 = time.perf_counter()
        cand_dirs = [REPO_ROOT / "tools" / "ppt-master", REPO_ROOT / "external" / "ppt-master"]
        found = next((d for d in cand_dirs if d.is_dir()), None)
        has_pptx = importlib.util.find_spec("pptx") is not None
        latency = (time.perf_counter() - t0) * 1000
        if found:
            return ToolResult(
                name="ppt-master",
                category="External",
                status="PASS",
                version="Found",
                required=False,
                latency_ms=round(latency, 2),
                detail=f"PPT Master 目錄存在: {found} (python-pptx: {has_pptx})",
            )
        return ToolResult(
            name="ppt-master",
            category="External",
            status="WARN",
            version="N/A",
            required=False,
            latency_ms=round(latency, 2),
            detail="未整合 ppt-master（DrawingML 向量簡報生成降級為純文字 Markdown）",
            fix_hint="git clone https://github.com/hugohe3/ppt-master tools/ppt-master",
        )

    def check_marp_cli(self) -> ToolResult:
        t0 = time.perf_counter()
        local_marp = find_local_or_path("marp")
        npx_exe = find_local_or_path("npx")
        
        cmd: Optional[List[str]] = None
        if local_marp:
            cmd = [local_marp, "--no-stdin", "--version"]
        elif npx_exe:
            cmd = [npx_exe, "@marp-team/marp-cli", "--no-stdin", "--version"]
        else:
            cmd = ["npx", "@marp-team/marp-cli", "--no-stdin", "--version"]

        try:
            res = run_cmd(cmd, timeout=30.0)
            if res.returncode == 0:
                ver = res.stdout.strip().splitlines()[-1]
                latency = (time.perf_counter() - t0) * 1000
                return ToolResult(
                    name="marp-cli",
                    category="Pipeline",
                    status="PASS",
                    version=ver,
                    required=False,
                    latency_ms=round(latency, 2),
                    detail=f"Markdown 投影片抽幀工具就緒 ({'本地 CLI' if local_marp else 'NPX 呼叫'})",
                )
        except Exception:
            pass

        latency = (time.perf_counter() - t0) * 1000
        return ToolResult(
            name="marp-cli",
            category="Pipeline",
            status="WARN",
            version="N/A",
            required=False,
            latency_ms=round(latency, 2),
            detail="無法調用 marp-cli（投影片批次抽幀將降級）",
            fix_hint="npm install -D @marp-team/marp-cli 或確保網路支援 npx 呼叫",
        )

    def check_rust_craft_tool(self, tool_name: str, cli_name: str) -> ToolResult:
        t0 = time.perf_counter()
        base_dir = Path(os.environ.get("OFFICE_ADOBE_CAD_DIR", str(OFFICE_ADOBE_CAD_DEFAULT)))
        exe_path = base_dir / tool_name / cli_name
        if not exe_path.is_file():
            # 也查系統 PATH 與專案內 tools/craft/
            alt_path = REPO_ROOT / "tools" / "craft" / cli_name
            which_p = shutil.which(cli_name)
            if alt_path.is_file():
                exe_path = alt_path
            elif which_p:
                exe_path = Path(which_p)
            else:
                latency = (time.perf_counter() - t0) * 1000
                return ToolResult(
                    name=tool_name,
                    category="OfficeCraft",
                    status="WARN",
                    version="N/A",
                    required=False,
                    latency_ms=round(latency, 2),
                    detail=f"找不到二進制檔: {exe_path}",
                    fix_hint=f"請確認 {base_dir} 包含 {tool_name}/{cli_name} 或設定環境變數 OFFICE_ADOBE_CAD_DIR",
                )
        try:
            res = run_cmd([str(exe_path), "--version"])
            out = (res.stdout or res.stderr).strip().splitlines()[0] if res.returncode == 0 else "Execution failed"
            ok = res.returncode == 0
            latency = (time.perf_counter() - t0) * 1000
            return ToolResult(
                name=tool_name,
                category="OfficeCraft",
                status="PASS" if ok else "WARN",
                version=out if ok else "Error",
                required=False,
                latency_ms=round(latency, 2),
                detail=f"二進制可用: {exe_path}",
                fix_hint="" if ok else "執行回傳非零退出碼，請檢查依賴 DLL",
            )
        except Exception as exc:
            latency = (time.perf_counter() - t0) * 1000
            return ToolResult(tool_name, "OfficeCraft", "WARN", "N/A", False, round(latency, 2), f"調用例外: {exc}", "")

    def check_craft_tools_wrapper(self) -> ToolResult:
        t0 = time.perf_counter()
        wrapper_paths = [REPO_ROOT / "tools" / "craft_tools.py", REPO_ROOT / "vc" / "craft_tools.py"]
        found = next((p for p in wrapper_paths if p.is_file()), None)
        latency = (time.perf_counter() - t0) * 1000
        if found:
            return ToolResult(
                name="craft_tools.py",
                category="Pipeline",
                status="PASS",
                version="Available",
                required=False,
                latency_ms=round(latency, 2),
                detail=f"Rust 工具 Python 封裝介面存在: {found}",
            )
        return ToolResult(
            name="craft_tools.py",
            category="Pipeline",
            status="WARN",
            version="N/A",
            required=False,
            latency_ms=round(latency, 2),
            detail="未找到 tools/craft_tools.py 封裝介面",
            fix_hint="待 Milestone 2 Worker 實作 tools/craft_tools.py 介面",
        )

    def run_all(self) -> List[ToolResult]:
        self.results = [
            self.check_python(),
            self.check_node(),
            self.check_ffmpeg(),
            self.check_ffmpeg_nvenc(),
            self.check_marp_cli(),
            self.check_pyjianyingdraft(),
            self.check_recordly(),
            self.check_ppt_master(),
            self.check_rust_craft_tool("EffectCraft", "effectcraft-cli.exe"),
            self.check_rust_craft_tool("PhotoCraft", "photocraft-cli.exe"),
            self.check_rust_craft_tool("VectorCraft", "vectorcraft-cli.exe"),
            self.check_rust_craft_tool("DeckCraft", "deckcraft-cli.exe"),
            self.check_craft_tools_wrapper(),
        ]
        return self.results


def print_rich_table(results: List[ToolResult]):
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Video Creator 外部工具與相依性自檢報告 (Milestone 2 F09)")
        table.add_column("分類", style="cyan", width=12)
        table.add_column("工具名稱", style="bold white", width=18)
        table.add_column("狀態", width=8)
        table.add_column("版本 / 資訊", style="magenta", width=24)
        table.add_column("耗時 (ms)", justify="right", width=10)
        table.add_column("詳細說明 / 修復建議", style="dim")

        for r in results:
            if r.status == "PASS":
                status_str = "[bold green]PASS[/bold green]"
            elif r.status == "WARN":
                status_str = "[bold yellow]WARN[/bold yellow]"
            else:
                status_str = "[bold red]FAIL[/bold red]"

            desc = r.detail
            if r.fix_hint:
                desc += f" -> [yellow]{r.fix_hint}[/yellow]"
            table.add_row(r.category, r.name, status_str, r.version, f"{r.latency_ms:.1f}", desc)

        console.print(table)
    except ImportError:
        print_plain_table(results)


def print_plain_table(results: List[ToolResult]):
    header = f"{'分類':<12}{'項目':<18}{'狀態':<8}{'版本':<24}{'耗時(ms)':<10}說明"
    print("=" * 100)
    print("Video Creator 外部工具與相依性自檢報告 (Milestone 2 F09)")
    print("=" * 100)
    print(header)
    print("-" * 100)
    for r in results:
        line = f"{r.category:<12}{r.name:<18}{r.status:<8}{r.version:<24}{r.latency_ms:<10.1f}{r.detail}"
        if r.fix_hint:
            line += f" -> 修復: {r.fix_hint}"
        print(line)
    print("=" * 100)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="驗證外部工具與相依性環境")
    parser.add_argument("--all", action="store_true", help="執行全部檢查項目")
    parser.add_argument("--json", action="store_true", help="輸出 JSON 格式報告")
    parser.add_argument("--deep", action="store_true", help="執行深度音視頻編碼測試")
    args = parser.parse_args(argv)

    verifier = ToolVerifier(deep=args.deep)
    results = verifier.run_all()

    failed_required = [r for r in results if r.required and r.status == "FAIL"]
    warns = [r for r in results if r.status == "WARN"]

    if args.json:
        report = {
            "summary": {
                "total": len(results),
                "passed": len([r for r in results if r.status == "PASS"]),
                "warnings": len(warns),
                "failed": len(failed_required),
                "ok": len(failed_required) == 0,
            },
            "tools": [asdict(r) for r in results],
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if failed_required else 0
    else:
        print_rich_table(results)
        print()
        if failed_required:
            print(f"[錯誤] 共有 {len(failed_required)} 個必要工具未通過檢測：{', '.join(r.name for r in failed_required)}")
            return 1
        elif warns:
            print(f"[提示] 所有必要工具通過。另有 {len(warns)} 項可選工具未安裝或處於降級狀態（不影響主流程運行）。")
            return 0
        else:
            print("[成功] 所有外部工具與相依性檢查全數通過！")
            return 0


if __name__ == "__main__":
    sys.exit(main())
