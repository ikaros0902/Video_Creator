"""一次性檢查：錄影的聲音是不是人聲。用 Whisper 轉寫並列出有文字的片段。

用法：.venv\\Scripts\\python.exe 09_scripts\\check_rec_audio.py <影片> <輸出 json>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vc.tools import WHISPER_DIR, configure_model_cache, detect_torch_device, find_tool  # noqa: E402

configure_model_cache()
os.environ["PATH"] = str(Path(find_tool("ffmpeg")).parent) + os.pathsep + os.environ["PATH"]

import whisper  # noqa: E402

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dst.unlink(missing_ok=True)
device = detect_torch_device()
model = whisper.load_model("small.en", device=device, download_root=str(WHISPER_DIR))
res = model.transcribe(str(src), language="en", fp16=(device == "cuda"), condition_on_previous_text=False)
segs = [{"start": round(s["start"], 1), "end": round(s["end"], 1), "text": s["text"].strip(),
         "no_speech_prob": round(s["no_speech_prob"], 2)} for s in res["segments"]]
dst.write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"segments={len(segs)}")
for s in segs[:20]:
    print(f"{s['start']:6.1f}-{s['end']:6.1f}  p_nospeech={s['no_speech_prob']}  {s['text'][:70]}")
