"""Story 6：用 Whisper 把配音轉回文字，產生逐字時間、字幕與發音檢查（WER）。

- WER 比對的是送進 TTS 的文字（套過發音字典），數字兩邊都轉成英文字再比。
- 字幕顯示原始旁白文字（例如 "3.0"），時間取自 Whisper 的逐字時間。
- 時間以每段音檔為基準（scene-local）。整支影片的字幕在時間軸排好後才產生；
  這裡另外輸出 preview.srt，對應 vc voice --preview 的試聽檔，方便先檢查。

輸出：work/align/words.json、work/align/preview.srt
"""
from __future__ import annotations

import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from vc.project import load_project
from vc.script import Script, contains_term, load_script
from vc.voice import make_backend, voice_dir

WER_MAX = 0.05            # 起始值：還沒有用真實素材校準
CUE_MAX_CHARS = 42
CUE_MIN_S = 1.0
PREVIEW_GAP_S = 0.4
_WEAK_END = {"a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "with", "by", "it"}


# ---------- 文字正規化 ----------

_SPOKEN_FIX = {"oh": "zero"}   # "three point oh" 與 Whisper 寫出的 "3.0" 對齊


def _num_to_words(tok: str) -> str:
    from num2words import num2words

    # num2words(3.0) 只會回 "three"，小數點後要逐位念出來才對得上 "three point zero"
    whole, _, frac = tok.partition(".")
    out = num2words(int(whole))
    if frac:
        out += " point " + " ".join(num2words(int(d)) for d in frac)
    return out


def norm_tokens(text: str) -> list[str]:
    """小寫、數字轉英文字、去標點、拆連字號。"""
    text = re.sub(r"\d+(?:\.\d+)?", lambda m: f" {_num_to_words(m.group(0))} ", text)
    text = text.lower().replace("-", " ").replace("–", " ")
    toks = re.findall(r"[a-z']+", text)
    return [_SPOKEN_FIX.get(t, t) for t in toks]


def merge_compounds(ref: list[str], hyp: list[str]) -> list[str]:
    """Whisper 常把複合字拆開寫（例如 wireframe -> wire frame）。發音正確僅拼寫不同，
    因此當相鄰兩字合併等於參考腳本中的單字時，合併為同一字詞再比對。"""
    vocab, out, i = set(ref), [], 0
    while i < len(hyp):
        if i + 1 < len(hyp) and hyp[i] + hyp[i + 1] in vocab and hyp[i] not in vocab:
            out.append(hyp[i] + hyp[i + 1])
            i += 2
        else:
            out.append(hyp[i])
            i += 1
    return out


def _pair(ref: str, hyp: str) -> tuple[list[str], list[str]]:
    a = norm_tokens(ref)
    return a, merge_compounds(a, norm_tokens(hyp))


def wer(ref: str, hyp: str) -> float:
    import jiwer

    a, b = _pair(ref, hyp)
    return jiwer.wer(" ".join(a), " ".join(b)) if a else 0.0


def diff_words(ref: str, hyp: str) -> list[str]:
    a, b = _pair(ref, hyp)
    out = []
    for op, i1, i2, j1, j2 in SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op != "equal":
            out.append(f"{op}: '{' '.join(a[i1:i2])}' -> '{' '.join(b[j1:j2])}'")
    return out


# ---------- 旁白文字對上 Whisper 時間 ----------

def narration_words(narration: str) -> list[str]:
    return narration.split()


def align_words(narration: str, spoken_map: dict[str, str], whisper_words: list[dict]) -> list[dict]:
    """回傳旁白每個字的 start/end（秒）。

    旁白字先套發音字典再正規化成 token；Whisper 的字也正規化成 token。
    兩串 token 用 SequenceMatcher 對齊：相同區塊直接取時間；不同區塊在該區塊的時間範圍內平均分配；
    完全沒對到的字，用前後字的時間內插。
    """
    from vc.voice import apply_lexicon

    words = narration_words(narration)
    ref_tok, ref_owner = [], []
    for wi, w in enumerate(words):
        for t in norm_tokens(apply_lexicon(w, spoken_map)):
            ref_tok.append(t)
            ref_owner.append(wi)

    hyp_tok, hyp_time = [], []
    for w in whisper_words:
        toks = norm_tokens(w["word"])
        n = max(len(toks), 1)
        span = (w["end"] - w["start"]) / n
        for k, t in enumerate(toks):
            hyp_tok.append(t)
            hyp_time.append((w["start"] + k * span, w["start"] + (k + 1) * span))

    tok_time: list[tuple[float, float] | None] = [None] * len(ref_tok)
    for op, i1, i2, j1, j2 in SequenceMatcher(a=ref_tok, b=hyp_tok, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                tok_time[i1 + k] = hyp_time[j1 + k]
        elif op == "replace" and j2 > j1:
            t0, t1 = hyp_time[j1][0], hyp_time[j2 - 1][1]
            n = i2 - i1
            for k in range(n):
                tok_time[i1 + k] = (t0 + (t1 - t0) * k / n, t0 + (t1 - t0) * (k + 1) / n)

    out = []
    for wi, w in enumerate(words):
        times = [tok_time[i] for i, o in enumerate(ref_owner) if o == wi and tok_time[i] is not None]
        out.append({"word": w, "start": min(t[0] for t in times) if times else None,
                    "end": max(t[1] for t in times) if times else None})
    _interpolate(out)
    return out


def _interpolate(items: list[dict]) -> None:
    n = len(items)
    for i, it in enumerate(items):
        if it["start"] is not None:
            continue
        prev_end = next((items[j]["end"] for j in range(i - 1, -1, -1) if items[j]["end"] is not None), 0.0)
        nxt = next((j for j in range(i + 1, n) if items[j]["start"] is not None), None)
        next_start = items[nxt]["start"] if nxt is not None else prev_end + 0.3
        # 前後有對到的字之間，缺時間的字平均分配這段空檔
        gap_words = (nxt - i) if nxt is not None else 1
        step = max(next_start - prev_end, 0.0) / gap_words
        it["start"], it["end"] = prev_end, prev_end + step
    for it in items:
        it["start"], it["end"] = round(it["start"], 3), round(max(it["end"], it["start"]), 3)


def find_word_time(words: list[dict], term: str) -> float | None:
    """at_word 第一次出現的開始時間；比對時忽略標點與大小寫。"""
    for w in words:
        if contains_term(w["word"], term):
            return w["start"]
    return None


# ---------- 字幕 ----------

def _split_sentence(ws: list[dict], max_chars: int) -> list[list[dict]]:
    """把一句切成最少段數，每段不超過 max_chars，且各段長度盡量平均；逗號後斷開有加分。

    先決定段數 k = ceil(總長 / max_chars)，再用動態規劃找斷點。
    平均切法可以避免「Next,」這種只有一個字、一閃而過的字幕。
    """
    import math

    texts = [w["word"] for w in ws]
    n = len(texts)

    def length(i: int, j: int) -> int:          # texts[i:j] 接成一行的字元數
        return len(" ".join(texts[i:j]))

    INF = float("inf")

    def solve(k: int, allow_weak: bool):
        target = length(0, n) / k
        best = [[INF] * (n + 1) for _ in range(k + 1)]
        back = [[0] * (n + 1) for _ in range(k + 1)]
        best[0][0] = 0.0
        for p in range(1, k + 1):
            for j in range(1, n + 1):
                # 不讓一行停在冠詞、介系詞或連接詞上，讀起來像話沒講完
                if j < n and not allow_weak and texts[j - 1].lower() in _WEAK_END:
                    continue
                for i in range(p - 1, j):
                    if best[p - 1][i] == INF or length(i, j) > max_chars:
                        continue
                    cost = best[p - 1][i] + (length(i, j) - target) ** 2
                    if j < n and texts[j - 1].endswith(","):
                        cost -= target ** 2 * 0.25
                    if cost < best[p][j]:
                        best[p][j], back[p][j] = cost, i
        if best[k][n] == INF:
            return None
        pieces, j = [], n
        for p in range(k, 0, -1):
            i = back[p][j]
            pieces.append(ws[i:j])
            j = i
        return [p for p in reversed(pieces) if p]

    k0 = max(1, math.ceil(length(0, n) / max_chars))
    # 先找不停在弱字的切法，必要時多切一段；最多多切兩段，再不行才允許停在弱字
    for allow_weak in (False, True):
        for k in range(k0, min(n, k0 + 2) + 1):
            pieces = solve(k, allow_weak)
            if pieces:
                return pieces
    return [ws]


def make_cues(words: list[dict], max_chars: int = CUE_MAX_CHARS, min_s: float = CUE_MIN_S) -> list[dict]:
    """句尾一定斷開；長句平均切段；太短的字幕延長顯示時間，但不蓋到下一則。"""
    sentences_, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.!?]$", w["word"]):
            sentences_.append(cur)
            cur = []
    if cur:
        sentences_.append(cur)

    cues = []
    for sent in sentences_:
        for piece in _split_sentence(sent, max_chars):
            cues.append({
                "text": " ".join(w["word"] for w in piece),
                "start": piece[0]["start"],
                "end": piece[-1]["end"],
                "words": [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in piece],
            })
    for i, c in enumerate(cues):
        if c["end"] - c["start"] < min_s:
            limit = cues[i + 1]["start"] if i + 1 < len(cues) else c["start"] + min_s
            c["end"] = round(max(c["end"], min(c["start"] + min_s, limit)), 3)
    return cues


def srt_time(t: float) -> str:
    ms = round(t * 1000)
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(cues: list[dict]) -> str:
    return "\n".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n"
                     for i, c in enumerate(cues, 1))


# ---------- 主流程 ----------

def transcribe_all(script: Script, vdir: Path, manifest: dict) -> dict[str, dict]:
    from vc.tools import (
        WHISPER_DIR,
        configure_model_cache,
        detect_torch_device,
        find_tool,
    )

    configure_model_cache()
    os.environ["PATH"] = str(Path(find_tool("ffmpeg")).parent) + os.pathsep + os.environ["PATH"]
    import whisper

    device = detect_torch_device()
    model = whisper.load_model("small.en", device=device, download_root=str(WHISPER_DIR))
    out = {}
    for s in script.scenes:
        res = model.transcribe(str(vdir / manifest["scenes"][s.id]["file"]), language="en",
                               word_timestamps=True, fp16=(device == "cuda"), condition_on_previous_text=False)
        out[s.id] = {"text": res["text"].strip(),
                     "words": [{"word": w["word"].strip(), "start": w["start"], "end": w["end"]}
                               for seg in res["segments"] for w in seg["words"]]}
    return out


def build(script: Script, manifest: dict, transcripts: dict[str, dict]) -> dict:
    scenes = {}
    for s in script.scenes:
        tr = transcripts[s.id]
        spoken = manifest["scenes"][s.id]["spoken"]
        words = align_words(s.narration, script.lexicon, tr["words"])
        at = {}
        for v in s.visuals.values():
            for c in v.callouts:
                at[c.at_word] = find_word_time(words, c.at_word)
            for item in [*v.data.get("cards", []), *v.data.get("steps", []), v.data.get("inset") or {}]:
                if isinstance(item, dict) and item.get("at_word"):
                    at[item["at_word"]] = find_word_time(words, item["at_word"])
        scenes[s.id] = {
            "duration_s": manifest["scenes"][s.id]["duration_s"],
            "transcript": tr["text"],
            "wer": round(wer(spoken, tr["text"]), 4),
            "diff": diff_words(spoken, tr["text"]),
            "words": words,
            "cues": make_cues(words),
            "at_word": at,
        }
    return {"voice": {k: manifest[k] for k in ("engine", "voice", "rate")}, "wer_max": WER_MAX, "scenes": scenes}


def preview_srt(result: dict, gap_s: float = PREVIEW_GAP_S) -> str:
    cues, offset = [], 0.0
    for sc in result["scenes"].values():
        for c in sc["cues"]:
            cues.append({"text": c["text"], "start": c["start"] + offset, "end": c["end"] + offset})
        offset += sc["duration_s"] + gap_s
    return to_srt(cues)


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc align <project>")
        return 2
    proj = load_project(argv[0])
    script = load_script(proj.root / "script.json")
    v = script.meta.voice
    vdir = voice_dir(proj.work, make_backend(v.engine, v.name, v.rate))
    manifest = json.loads((vdir / "manifest.json").read_text(encoding="utf-8"))
    from vc.pipeline_safety import check_voice, script_fingerprint, voice_fingerprint
    try:
        check_voice(script, manifest, vdir)
    except (ValueError, OSError, KeyError) as exc:
        print(f"語音資料無效：{exc}，請重新執行 vc voice", file=sys.stderr)
        return 1
    if manifest.get("rate") != v.rate:
        print(f"配音的語速 {manifest.get('rate')} 和 script.json 的 {v.rate} 不同，先執行 vc voice", file=sys.stderr)
        return 1

    result = build(script, manifest, transcribe_all(script, vdir, manifest))
    out_dir = proj.work / "align"
    out_dir.mkdir(parents=True, exist_ok=True)

    bad = []
    print(f"{'場景':<6}{'WER':>7}  字幕數  缺時間的標註字")
    for sid, sc in result["scenes"].items():
        missing = [k for k, t in sc["at_word"].items() if t is None]
        print(f"{sid:<6}{sc['wer']:>7.1%}  {len(sc['cues']):>5}  {missing or '-'}")
        for d in sc["diff"]:
            print(f"        {d}")
        if sc["wer"] > WER_MAX or missing:
            bad.append(sid)
    print(f"-> {out_dir / 'words.json'}、{out_dir / 'preview.srt'}")
    if bad:
        print(f"沒通過（WER > {WER_MAX:.0%} 或標註字找不到時間）：{', '.join(bad)}")
        return 1
    result.update(valid=True, voice_fingerprint=voice_fingerprint(manifest, vdir), script_fingerprint=script_fingerprint(script))
    from vc.pipeline_safety import atomic_write
    atomic_write(out_dir / "words.json", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
    atomic_write(out_dir / "preview.srt", preview_srt(result).encode("utf-8"))
    print("全部通過。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
