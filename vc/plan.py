"""Story 8：把腳本、配音長度、逐字時間合成時間軸 work/timeline.json（以影格為單位）。

時間規則（以旁白為準）：
- 每段長度 = 旁白長度 + 段後空檔；第一段前面多一點導入，最後一段後面停留久一點。
- 有錄影的段落再多 0.5 秒，讓最後一個操作畫面看得清楚。
- 起點影格一律由累計秒數換算後才四捨五入，避免每段各自捨入造成誤差累積。

錄影片段的時間窗：
- 設了 start_at_word 的 clip 從那個字開始出現；第一段從 0 開始；
- 沒設定的 clip 和前一段共用時間窗，依原始長度比例分配；
- 播放倍率 = 原始長度 / 畫面長度。超過 2.5 倍視為錯誤；不到 1 倍時以原速播放，剩下時間停在最後一格。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from vc.align import srt_time
from vc.project import load_project
from vc.script import Script, load_script
from vc.voice import make_backend, voice_dir

# 2026-11-09：配音改成修剪前後靜音（前後各留 0.08 s），段落停頓全部由這裡控制。
# 使用者回饋「結尾倉促」：片尾停留改成 3.2 s，放片名與 logo。
# 2026-11-13：語速改 1.05 倍、段落停頓加長到 0.7 s，回應「旁白偏快」
LEAD_IN_S = 0.4
GAP_S = 0.7
RECORDING_EXTRA_S = 0.5
END_HOLD_S = 3.2
MAX_SPEED = 2.5


class PlanError(ValueError):
    pass


def _f(seconds: float, fps: int) -> int:
    return int(round(seconds * fps))


def scene_lengths(script: Script, narration_s: dict[str, float]) -> list[tuple[float, float]]:
    """回傳每段的（導入秒數, 總秒數）。"""
    out, n = [], len(script.scenes)
    for i, s in enumerate(script.scenes):
        lead = LEAD_IN_S if i == 0 else 0.0
        tail = END_HOLD_S if i == n - 1 else GAP_S
        extra = RECORDING_EXTRA_S if any(v.kind == "recording" for v in s.visuals.values()) else 0.0
        out.append((lead, lead + narration_s[s.id] + tail + extra))
    return out


def clip_windows(clips, word_time, lead_s: float, scene_frames: int, fps: int) -> list[dict]:
    """把 clips 排進段落時間窗，回傳每段的 start/duration 影格與倍率。"""
    # 先找出每個時間窗的起點（影格，相對段落起點）
    groups: list[list[int]] = []
    starts: list[int] = []
    for k, c in enumerate(clips):
        if k == 0 or c.start_at_word:
            t = 0.0 if k == 0 and not c.start_at_word else word_time(c.start_at_word)
            if t is None:
                raise PlanError(f"clip {k} 的 start_at_word「{c.start_at_word}」找不到時間")
            starts.append(0 if k == 0 else _f(lead_s + t, fps))
            groups.append([k])
        else:
            groups[-1].append(k)
    bounds = starts + [scene_frames]
    if any(b2 <= b1 for b1, b2 in zip(bounds, bounds[1:])):
        raise PlanError(f"錄影時間窗的起點沒有遞增：{bounds}")

    result: list[dict] = [{} for _ in clips]
    for g, members in enumerate(groups):
        w0, w1 = bounds[g], bounds[g + 1]
        src = [clips[k].source[1] - clips[k].source[0] for k in members]
        total_src = sum(src)
        cum, prev = 0.0, w0
        for k, sl in zip(members, src):
            cum += sl
            end = w0 + int(round((w1 - w0) * cum / total_src))
            frames = end - prev
            out_s = frames / fps
            speed = sl / out_s
            if speed > MAX_SPEED + 1e-9:
                raise PlanError(f"clip {k} 需要 {speed:.2f} 倍速（原始 {sl:.2f}s → 畫面 {out_s:.2f}s），超過 {MAX_SPEED} 倍")
            play = max(speed, 1.0)
            freeze = frames - min(frames, _f(sl / play, fps))
            result[k] = {"start_frame": prev, "duration_frames": frames, "speed": round(play, 4),
                         "freeze_frames": freeze}
            prev = end
    return result


def build_timeline(script: Script, manifest: dict, aligned: dict, voice_files: dict[str, str],
                   recordings: dict[str, str], work: Path | None = None) -> dict:
    fps = script.meta.fps
    narr = {sid: sc["duration_s"] for sid, sc in manifest["scenes"].items()}
    lengths = scene_lengths(script, narr)

    scenes, audio, cues, cum = [], [], [], 0.0
    for s, (lead, length) in zip(script.scenes, lengths):
        start = _f(cum, fps)
        cum += length
        frames = _f(cum, fps) - start
        lead_f = _f(lead, fps)
        al = aligned["scenes"][s.id]

        def word_time(term, _al=al):
            return _al["at_word"].get(term) if term in _al["at_word"] else _find(_al["words"], term)

        audio.append({"scene": s.id, "file": voice_files[s.id], "start_frame": start + lead_f,
                      "duration_frames": _f(narr[s.id], fps)})
        for c in al["cues"]:
            c_entry = {
                "text": c["text"],
                "start_frame": start + lead_f + _f(c["start"], fps),
                "end_frame": start + lead_f + _f(c["end"], fps),
            }
            if "words" in c:
                c_entry["words"] = [
                    {
                        "word": w["word"],
                        "start_frame": start + lead_f + _f(w["start"], fps),
                        "end_frame": start + lead_f + _f(w["end"], fps),
                    }
                    for w in c["words"]
                ]
            cues.append(c_entry)
        at_frames = {k: (lead_f + _f(t, fps) if t is not None else None) for k, t in al["at_word"].items()}
        # 動畫範本 data 裡任何一層的 at_word 都換算成影格，讓範本不必自己查字的時間
        for v in s.visuals.values():
            for term in _data_words(v.data):
                if term not in at_frames:
                    t = word_time(term)
                    if t is None:
                        raise PlanError(f"{s.id}: 動畫的 at_word「{term}」找不到時間")
                    at_frames[term] = lead_f + _f(t, fps)

        visuals = {}
        for variant, v in s.visuals.items():
            vis = {"kind": v.kind, "template": v.template, "data": v.data,
                   "images": [str((work / i).resolve()) if work else i for i in v.images]}
            if v.clips:
                wins = clip_windows(v.clips, word_time, lead, frames, fps)
                vis["clips"] = [{"index": k, "recording": c.recording, "source_file": recordings[c.recording],
                                 "source": list(c.source), "crop": list(c.crop) if c.crop else None,
                                 "label": c.label, "camera": getattr(c, "camera", None),
                                 "file": f"fit/{s.id}_c{k}.mp4", **w}
                                for k, (c, w) in enumerate(zip(v.clips, wins))]
            vis["callouts"] = []
            for c in v.callouts:
                t = word_time(c.at_word)
                vis["callouts"].append({"frame": lead_f + _f(t, fps), "box": list(c.box), "text": c.text,
                                        "clip": c.clip, "at_word": c.at_word})
            visuals[variant] = vis

        scenes.append({"id": s.id, "section": s.section, "start_frame": start, "duration_frames": frames,
                       "narration_start_frame": lead_f, "narration_frames": _f(narr[s.id], fps),
                       "at_frames": at_frames, "visuals": visuals})

    total = _f(cum, fps)
    return {"fps": fps, "size": list(script.meta.size), "total_frames": total, "total_s": round(total / fps, 3),
            "voice": {k: manifest[k] for k in ("engine", "voice", "rate")},
            "audio": audio, "cues": cues, "scenes": scenes}


def _data_words(obj) -> list[str]:
    if isinstance(obj, dict):
        out = [obj["at_word"]] if isinstance(obj.get("at_word"), str) else []
        for v in obj.values():
            out += _data_words(v)
        return out
    if isinstance(obj, list):
        return [w for v in obj for w in _data_words(v)]
    return []


def _find(words, term):
    from vc.align import find_word_time
    return find_word_time(words, term)


def timeline_srt(tl: dict) -> str:
    fps = tl["fps"]
    return "\n".join(f"{i}\n{srt_time(c['start_frame'] / fps)} --> {srt_time(c['end_frame'] / fps)}\n{c['text']}\n"
                     for i, c in enumerate(tl["cues"], 1))


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc plan <project>")
        return 2
    proj = load_project(argv[0])
    script = load_script(proj.root / "script.json")
    v = script.meta.voice
    vdir = voice_dir(proj.work, make_backend(v.engine, v.name, v.rate))
    manifest = json.loads((vdir / "manifest.json").read_text(encoding="utf-8"))
    aligned = json.loads((proj.work / "align" / "words.json").read_text(encoding="utf-8"))
    if aligned["voice"] != {k: manifest[k] for k in ("engine", "voice", "rate")}:
        print("words.json 和目前的配音不一致，先執行 vc align", file=sys.stderr)
        return 1
    rec_json = json.loads((proj.work / "recordings.json").read_text(encoding="utf-8"))
    recordings = {r["id"]: r["file"] for r in rec_json["recordings"]}
    voice_files = {sid: str((vdir / sc["file"]).resolve()) for sid, sc in manifest["scenes"].items()}

    try:
        tl = build_timeline(script, manifest, aligned, voice_files, recordings, proj.work)
    except PlanError as exc:
        print(f"時間軸錯誤：{exc}", file=sys.stderr)
        return 1
    (proj.work / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    for variant in ("internal", "public"):
        out = proj.output / variant
        out.mkdir(parents=True, exist_ok=True)
        (out / "final.srt").write_text(timeline_srt(tl), encoding="utf-8")

    fps = tl["fps"]
    print(f"{'場景':<6}{'起點':>8}{'長度':>8}{'旁白':>8}")
    for sc in tl["scenes"]:
        print(f"{sc['id']:<6}{sc['start_frame'] / fps:>7.2f}s{sc['duration_frames'] / fps:>7.2f}s"
              f"{sc['narration_frames'] / fps:>7.2f}s")
        for c in sc["visuals"]["internal"].get("clips", []):
            print(f"        clip {c['index']}  {c['source'][0]:>5.1f}–{c['source'][1]:<5.1f}s → "
                  f"{c['duration_frames'] / fps:.2f}s  {c['speed']:.2f}x  停格 {c['freeze_frames'] / fps:.2f}s  {c['label']}")
    lo, hi = script.meta.target_duration_s
    print(f"總長 {tl['total_s']:.2f}s（{tl['total_frames']} 格），目標 {lo:g}–{hi:g}s，字幕 {len(tl['cues'])} 則")
    if not lo <= tl["total_s"] <= hi:
        print("總長超出目標", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
