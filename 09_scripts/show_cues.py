"""列出指定段落的長度、觸發字影格（換成秒）與逐字時間，寫 Manim 動畫時用來對照。

用法：.venv\\Scripts\\python.exe 09_scripts\\show_cues.py <project> <scene> [<scene> ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "06_projects" / sys.argv[1] / "work"
tl = json.loads((root / "timeline.json").read_text(encoding="utf-8"))
words = json.loads((root / "align" / "words.json").read_text(encoding="utf-8"))["scenes"]
for sid in sys.argv[2:]:
    s = next(x for x in tl["scenes"] if x["id"] == sid)
    fps = tl["fps"]
    print(f"{sid} 長度 {s['duration_frames'] / fps:.2f}s  旁白起點 {s['narration_start_frame'] / fps:.2f}s  "
          f"旁白長 {s['narration_frames'] / fps:.2f}s")
    print("  觸發字：", {k: round(v / fps, 2) for k, v in s["at_frames"].items()})
    print("  逐字：", " ".join(f"{w['word']}@{w['start']:.1f}" for w in words[sid]["words"]))
