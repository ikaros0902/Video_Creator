"""Story 7：依 timeline.json 把每段錄影裁切、變速、補停格，輸出影格數完全正確的片段。

輸出：work/fit/<scene>_c<k>.mp4（30 fps、無聲音）與 work/fit/manifest.json（快取）
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from vc.media import ffmpeg_run, ffprobe, h264_encode_args
from vc.project import load_project
from vc.tools import run


def clip_filter(clip: dict, fps: int) -> str:
    parts = []
    if clip.get("crop"):
        x, y, w, h = (int(v) for v in clip["crop"])
        parts.append(f"crop={w - w % 2}:{h - h % 2}:{x}:{y}")
    parts.append(f"setpts=(PTS-STARTPTS)/{clip['speed']}")
    parts.append(f"fps={fps}")
    # 停格多給一點緩衝，最後用 -frames:v 截到精確格數
    parts.append(f"tpad=stop_mode=clone:stop_duration={clip['freeze_frames'] / fps + 1.0:.3f}")
    return ",".join(parts)


def render_clip(clip: dict, fps: int, out: Path, use_gpu: bool = True) -> None:
    s0, s1 = clip["source"]
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_run(["-ss", f"{s0:.3f}", "-t", f"{s1 - s0:.3f}", "-i", clip["source_file"],
                "-vf", clip_filter(clip, fps), "-frames:v", str(clip["duration_frames"]), "-an",
                *h264_encode_args(quality=16, cpu_preset="veryfast", use_gpu=use_gpu), "-pix_fmt", "yuv420p",
                "-r", str(fps), str(out)])


def count_frames(path: Path) -> int:
    res = run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-count_frames",
               "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)])
    # Remotion 輸出的 MP4 會讓 csv 多一個空欄位（例如 "1946,"），只取第一欄
    return int(res.stdout.strip().split(",")[0])


def clip_key(clip: dict, fps: int) -> str:
    fields = {k: clip[k] for k in ("source_file", "source", "crop", "speed", "freeze_frames", "duration_frames")}
    return hashlib.sha1(json.dumps([fields, fps], sort_keys=True).encode()).hexdigest()[:16]


def fit_all(tl: dict, work: Path, use_gpu: bool = True) -> list[dict]:
    fps = tl["fps"]
    man_path = work / "fit" / "manifest.json"
    old = json.loads(man_path.read_text(encoding="utf-8")) if man_path.is_file() else {}
    new, report = {}, []
    for sc in tl["scenes"]:
        for clip in sc["visuals"]["internal"].get("clips", []):
            out = work / clip["file"]
            key = clip_key(clip, fps)
            made = False
            if not (old.get(clip["file"]) == key and out.is_file()):
                out.unlink(missing_ok=True)
                render_clip(clip, fps, out, use_gpu=use_gpu)
                made = True
            n = count_frames(out)
            new[clip["file"]] = key
            report.append({"file": clip["file"], "expected": clip["duration_frames"], "frames": n, "made": made})
    man_path.parent.mkdir(parents=True, exist_ok=True)
    man_path.write_text(json.dumps(new, indent=2), encoding="utf-8")
    return report


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc fit <project> [--no-gpu]")
        return 2
    proj = load_project(argv[0])
    use_gpu = "--no-gpu" not in argv
    tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
    report = fit_all(tl, proj.work, use_gpu=use_gpu)
    bad = [r for r in report if r["frames"] != r["expected"]]
    for r in report:
        print(f"{r['file']:<20} 影格 {r['frames']:>4} / {r['expected']:<4} {'重新輸出' if r['made'] else '快取'}")
    if bad:
        print(f"影格數不符：{[r['file'] for r in bad]}", file=sys.stderr)
        return 1
    print("全部片段影格數正確。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
