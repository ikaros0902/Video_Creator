"""Story 5：為每段旁白產生配音。

- 發音字典（lexicon）在送進 TTS 前替換文字；字幕仍用原始旁白。
- 快取鍵 = 引擎 + 聲音 + 語速 + 替換後文字。只改一段旁白時，只有那一段重新合成。
- 輸出統一成 48 kHz 單聲道 WAV，方便後面混音。

輸出：work/voice/<engine>-<voice>/<scene>.wav、manifest.json、preview.wav（--preview）
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import soundfile as sf

from vc.media import ffmpeg_run
from vc.project import load_project
from vc.script import Script, load_script
from vc.tools import configure_model_cache, detect_torch_device, use_system_certs

SAMPLE_RATE = 48000
# 2026-11-09 實測：Kokoro 每段音檔前後各帶約 0.4 s 靜音，段落間實際停頓變成 1.1–1.7 s。
# 修剪到前後各 0.08 s，段落停頓改由 vc plan 的 GAP_S 統一控制。
TRIM_DB = -45.0
TRIM_PAD_S = 0.08
POST_VERSION = "trim1"   # 後處理方式改變時更新，讓快取失效


def trim_silence(path: Path, db: float = TRIM_DB, pad_s: float = TRIM_PAD_S) -> None:
    """去掉前後的靜音，各保留 pad_s 秒，避免字頭字尾被切掉。"""
    import numpy as np

    data, sr = sf.read(str(path), dtype="int16")
    thr = 32767 * 10 ** (db / 20)
    loud = np.flatnonzero(np.abs(data.astype(np.int32)) > thr)
    if loud.size == 0:
        return
    pad = int(pad_s * sr)
    s, e = max(loud[0] - pad, 0), min(loud[-1] + pad + 1, len(data))
    sf.write(str(path), data[s:e], sr, subtype="PCM_16")


class TTSBackend(Protocol):
    engine: str
    voice: str
    rate: str

    def synth(self, text: str, out_wav: Path) -> None: ...


def apply_lexicon(text: str, lexicon: dict[str, str]) -> str:
    """整詞替換；較長的詞先換，避免 "3.0" 被 "3" 的規則搶先替換。"""
    for src in sorted(lexicon, key=len, reverse=True):
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(src)}(?![A-Za-z0-9])", lexicon[src], text)
    return text


def cache_key(backend: TTSBackend, spoken: str) -> str:
    raw = json.dumps([backend.engine, backend.voice, backend.rate, spoken, POST_VERSION], ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def wav_duration(path: Path) -> float:
    info = sf.info(str(path))
    return info.frames / info.samplerate


def _to_wav48(src: Path, dst: Path) -> None:
    ffmpeg_run(["-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(dst)])


# ---------- 後端 ----------

@dataclass
class EdgeBackend:
    voice: str = "en-US-AndrewNeural"
    rate: str = "+0%"
    engine: str = "edge"
    retries: int = 3

    def __post_init__(self):
        use_system_certs()

    def synth(self, text: str, out_wav: Path) -> None:
        import edge_tts

        tmp = out_wav.with_suffix(".mp3")
        last: Exception | None = None
        # 微軟服務偶爾斷線或回傳空音訊：2026-11-09 Andrew 的 s03 失敗 1 次，
        # 同一段文字之後連續重試 4 次都成功，所以 NoAudioReceived 視為暫時性錯誤。
        # 其他例外（例如聲音名稱錯誤）直接拋出。
        transient = (OSError, asyncio.TimeoutError, edge_tts.exceptions.WebSocketError,
                     edge_tts.exceptions.NoAudioReceived)
        for attempt in range(self.retries):
            try:
                asyncio.run(edge_tts.Communicate(text, self.voice, rate=self.rate).save(str(tmp)))
                break
            except transient as exc:
                last = exc
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"Edge TTS 連線失敗 {self.retries} 次：{last}")
        _to_wav48(tmp, out_wav)
        tmp.unlink(missing_ok=True)


@dataclass
class KokoroBackend:
    voice: str = "am_michael"
    rate: str = "1.0"          # Kokoro 用倍率表示語速
    engine: str = "kokoro"
    _pipe: object = None

    def synth(self, text: str, out_wav: Path) -> None:
        import numpy as np

        if self._pipe is None:
            configure_model_cache()
            from kokoro import KPipeline
            lang = "b" if self.voice.startswith("b") else "a"   # a = 美式、b = 英式
            self._pipe = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M", device=detect_torch_device())
        chunks = [a for _, _, a in self._pipe(text, voice=self.voice, speed=float(self.rate))]
        audio = np.concatenate([c.cpu().numpy() if hasattr(c, "cpu") else c for c in chunks])
        tmp = out_wav.with_name(out_wav.stem + "_24k.wav")
        sf.write(str(tmp), audio, 24000)
        _to_wav48(tmp, out_wav)
        tmp.unlink(missing_ok=True)


def make_backend(engine: str, voice: str | None, rate: str | None) -> TTSBackend:
    if engine == "edge":
        return EdgeBackend(voice=voice or "en-US-AndrewNeural", rate=rate or "+0%")
    if engine == "kokoro":
        return KokoroBackend(voice=voice or "am_michael", rate=rate or "1.0")
    raise ValueError(f"未知的 TTS 引擎：{engine}")


# ---------- 主流程 ----------

def voice_dir(work: Path, backend: TTSBackend) -> Path:
    return work / "voice" / f"{backend.engine}-{backend.voice}"


def generate(script: Script, backend: TTSBackend, work: Path) -> dict:
    """回傳 manifest；manifest 同時寫到 voice 資料夾。"""
    out_dir = voice_dir(work, backend)
    out_dir.mkdir(parents=True, exist_ok=True)
    man_path = out_dir / "manifest.json"
    old = json.loads(man_path.read_text(encoding="utf-8")) if man_path.is_file() else {"scenes": {}}

    scenes, made = {}, []
    for s in script.scenes:
        spoken = apply_lexicon(s.narration, script.lexicon)
        key = cache_key(backend, spoken)
        wav = out_dir / f"{s.id}.wav"
        prev = old["scenes"].get(s.id)
        if not (prev and prev.get("key") == key and wav.is_file()):
            wav.unlink(missing_ok=True)
            backend.synth(spoken, wav)
            trim_silence(wav)
            made.append(s.id)
        scenes[s.id] = {"key": key, "file": wav.name, "narration": s.narration, "spoken": spoken,
                        "duration_s": round(wav_duration(wav), 3)}

    manifest = {"engine": backend.engine, "voice": backend.voice, "rate": backend.rate,
                "sample_rate": SAMPLE_RATE, "scenes": scenes, "generated": made,
                "total_s": round(sum(v["duration_s"] for v in scenes.values()), 3)}
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def preview(manifest: dict, out_dir: Path, gap_s: float = 0.4) -> Path:
    """把各段接起來，段與段之間留 gap_s 秒，給人試聽整體節奏。"""
    files = [out_dir / v["file"] for v in manifest["scenes"].values()]
    args, labels = [], []
    for i, f in enumerate(files):
        args += ["-i", str(f)]
        labels.append(f"[{i}:a]apad=pad_dur={gap_s}[a{i}]")
    concat = ";".join(labels) + ";" + "".join(f"[a{i}]" for i in range(len(files))) + f"concat=n={len(files)}:v=0:a=1[out]"
    out = out_dir / "preview.wav"
    ffmpeg_run([*args, "-filter_complex", concat, "-map", "[out]", "-c:a", "pcm_s16le", str(out)])
    return out


def _opt(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv else None


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc voice <project> [--engine edge|kokoro] [--voice 名稱] [--rate 語速] [--preview]")
        return 2
    proj = load_project(argv[0])
    from vc.script import main as validate
    if validate([str(proj.root)]) != 0:
        return 1
    script = load_script(proj.root / "script.json")
    v = script.meta.voice
    engine = _opt(argv, "--engine") or v.engine
    backend = make_backend(engine, _opt(argv, "--voice") or (v.name if engine == v.engine else None),
                           _opt(argv, "--rate") or (v.rate if engine == v.engine else None))
    t0 = time.perf_counter()
    man = generate(script, backend, proj.work)
    words = sum(len(re.findall(r"\S+", s.narration)) for s in script.scenes)
    print(f"{backend.engine}/{backend.voice} rate={backend.rate}  重新合成 {len(man['generated'])} 段，"
          f"耗時 {time.perf_counter() - t0:.1f}s")
    for sid, sc in man["scenes"].items():
        print(f"  {sid}  {sc['duration_s']:6.2f}s")
    print(f"  合計 {man['total_s']:.2f}s，平均每分鐘 {words / man['total_s'] * 60:.0f} 字")
    if "--preview" in argv:
        out = preview(man, voice_dir(proj.work, backend))
        print(f"  試聽檔：{out}（{wav_duration(out):.2f}s）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
