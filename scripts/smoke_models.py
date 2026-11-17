"""下載模型並做一次端到端冒煙測試：Kokoro 與 Edge TTS 各念一句，再用 Whisper 轉回文字比對。

用法：.venv\\Scripts\\python.exe 09_scripts\\smoke_models.py
輸出：models\\_smoke\\ 底下的音檔與 smoke_report.json
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vc.tools import MODELS_DIR, WHISPER_DIR, configure_model_cache, detect_torch_device, find_tool, use_system_certs  # noqa: E402

configure_model_cache()
use_system_certs()

import os  # noqa: E402

# Whisper 讀音檔時會呼叫 ffmpeg，先把專案內的 ffmpeg 放到 PATH 最前面
os.environ["PATH"] = str(Path(find_tool("ffmpeg")).parent) + os.pathsep + os.environ["PATH"]

import jiwer  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
import whisper  # noqa: E402

TEXT = "To validate a wireframe mesh reliably, we batch check all closed components in parallel."
OUT = MODELS_DIR / "_smoke"
OUT.mkdir(parents=True, exist_ok=True)


def normalize(s: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() or ch == " " else " " for ch in s).split())


def kokoro_tts(path: Path, device: str) -> float:
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device=device)
    chunks = [audio for _, _, audio in pipe(TEXT, voice="am_michael", speed=1.0)]
    audio = np.concatenate([c.cpu().numpy() if hasattr(c, "cpu") else c for c in chunks])
    sf.write(path, audio, 24000)
    return len(audio) / 24000


async def edge_tts(path: Path) -> None:
    import edge_tts as et

    await et.Communicate(TEXT, "en-US-AndrewNeural").save(str(path))


def main() -> int:
    device = detect_torch_device()
    dev_name = torch.cuda.get_device_name(0) if device == "cuda" and torch.cuda.is_available() else device
    report: dict = {"text": TEXT, "device": dev_name}

    t = time.perf_counter()
    model = whisper.load_model("small.en", device=device, download_root=str(WHISPER_DIR))
    report["whisper_load_s"] = round(time.perf_counter() - t, 1)

    files = {"kokoro": OUT / "kokoro.wav", "edge": OUT / "edge.mp3"}
    for f in files.values():
        f.unlink(missing_ok=True)

    t = time.perf_counter()
    report["kokoro_duration_s"] = round(kokoro_tts(files["kokoro"], device), 2)
    report["kokoro_synth_s"] = round(time.perf_counter() - t, 1)

    t = time.perf_counter()
    asyncio.run(edge_tts(files["edge"]))
    report["edge_synth_s"] = round(time.perf_counter() - t, 1)

    for name, f in files.items():
        res = model.transcribe(str(f), language="en", word_timestamps=True, fp16=(device == "cuda"))
        words = [w for seg in res["segments"] for w in seg["words"]]
        report[name] = {
            "transcript": res["text"].strip(),
            "wer": round(jiwer.wer(normalize(TEXT), normalize(res["text"])), 3),
            "words": len(words),
            "first_word_start_s": round(words[0]["start"], 2) if words else None,
            "bytes": f.stat().st_size,
        }

    (OUT / "smoke_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    ok = all(report[n]["wer"] <= 0.05 for n in files)
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
