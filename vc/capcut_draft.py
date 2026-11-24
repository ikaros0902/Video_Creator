"""Story 12：把算好的最終影片匯出成可編輯的剪映（CapCut）草稿。

用 capcut-cli 的 quickstart 指令，把 output/<variant>/<name>.mp4 與同目錄的 final.srt
（由 Story 8 `vc plan` 寫出，跟目前 timeline.json 的旁白逐句對齊）一次匯入成一份新草稿，
寫進本機 CapCut 的草稿庫（`vc doctor` 的 capcut-app 檢查會找到的那個資料夾），可直接在
CapCut 開啟續編、加轉場或調整。

輸出：CapCut 草稿庫 /<draft-name>（預設 <project>-<variant>）
"""
from __future__ import annotations

import json
import os
import subprocess

from vc.project import Project, load_project
from vc.tools import ROOT, find_tool


def capcut_cli() -> str:
    exe = find_tool("capcut")
    if not exe:
        raise FileNotFoundError("找不到 capcut-cli，在根目錄執行 npm install")
    return exe


def ffprobe_cmd() -> str | None:
    """capcut-cli 預設在 PATH 找 ffprobe；專案內的 ffprobe 沒掛在 PATH 上，明確指路徑。"""
    p = ROOT / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"
    return str(p) if p.is_file() else None


def build_draft(proj: Project, variant: str, name: str, draft_name: str) -> dict:
    """呼叫 `capcut quickstart` 建立草稿，回傳 capcut-cli 的 JSON 結果。"""
    video = proj.output / f"{name}.mp4"
    srt = proj.output / "final.srt"
    if not video.is_file():
        raise FileNotFoundError(f"找不到影片：{video}")
    if not srt.is_file():
        raise FileNotFoundError(f"找不到字幕：{srt}")
    cmd = [capcut_cli(), "quickstart", draft_name, "--video", str(video), "--srt", str(srt)]
    probe = ffprobe_cmd()
    if probe:
        cmd += ["--ffprobe-cmd", probe]
    env = dict(os.environ, NODE_USE_SYSTEM_CA="1")
    res = subprocess.run(cmd, capture_output=True, check=False, text=True, encoding="utf-8", errors="replace",
                          timeout=120, env=env)
    if res.returncode != 0:
        raise RuntimeError(f"capcut quickstart 失敗：{(res.stdout + res.stderr).strip()[-2000:]}")
    return json.loads(res.stdout)


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc capcut-draft <project> [--name draft] [--draft-name <name>]")
        return 2
    proj = load_project(argv[0])
    if "--variant" in argv:
        print("已取消版本選項，請使用單一影片。")
        return 2
    variant = "main"
    name = argv[argv.index("--name") + 1] if "--name" in argv else "draft"
    draft_name = argv[argv.index("--draft-name") + 1] if "--draft-name" in argv else proj.name
    result = build_draft(proj, variant, name, draft_name)
    lint = result.get("lint", {})
    added = result.get("added", {})
    print(f"{draft_name}: {result['draft_path']}  影片={added.get('video')}  字幕段數={added.get('captions')}  "
          f"lint 錯誤={lint.get('errors')} 警告={lint.get('warnings')}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
