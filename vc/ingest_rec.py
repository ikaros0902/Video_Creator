"""Story 3：分析螢幕錄影，產生縮圖總覽、場景切點與每秒畫面變化量，供挑選操作片段。

輸出：
  work/recordings.json
  work/recordings/<id>/thumb_XXXX.jpg、sheet_N.jpg
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np

from vc.media import ffmpeg, probe
from vc.project import load_project
from vc.tools import run

THUMB_W = 384
SHEET_COLS = 6
SHEET_ROWS = 5


def detect_scenes(path: Path, threshold: float = 27.0) -> list[dict]:
    from scenedetect import ContentDetector, detect

    scenes = detect(str(path), ContentDetector(threshold=threshold), show_progress=False)
    return [{"start": round(s.seconds, 3), "end": round(e.seconds, 3)} for s, e in scenes]


def sample_video(path: Path, every: float, step: float = 0.5) -> tuple[list[float], list[tuple[float, np.ndarray]]]:
    """循序讀影格：每 step 秒算一次畫面變化量，每 every 秒存一張縮圖。

    變化量 = 相鄰取樣的灰階縮小圖平均絕對差（0–255）。螢幕錄影大部分時間畫面不動，
    這個數字能看出哪幾秒在操作、哪幾秒在等待。
    """
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV 打不開 {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    activity: list[float] = []
    thumbs: list[tuple[float, np.ndarray]] = []
    prev_small = None
    next_sample, next_thumb = 0.0, 0.0
    frame_i = 0
    while True:
        if not cap.grab():
            break
        t = frame_i / fps
        frame_i += 1
        need_sample = t + 1e-6 >= next_sample
        need_thumb = t + 1e-6 >= next_thumb
        if not (need_sample or need_thumb):
            continue
        ok, frame = cap.retrieve()
        if not ok:
            break
        if need_sample:
            small = cv2.cvtColor(cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            if prev_small is not None:
                activity.append(round(float(np.mean(cv2.absdiff(small, prev_small))), 2))
            prev_small = small
            next_sample += step
        if need_thumb:
            h = int(frame.shape[0] * THUMB_W / frame.shape[1])
            thumbs.append((round(t, 2), cv2.resize(frame, (THUMB_W, h), interpolation=cv2.INTER_AREA)))
            next_thumb += every
    cap.release()
    return activity, thumbs


def _label(img: np.ndarray, text: str) -> np.ndarray:
    out = img.copy()
    cv2.rectangle(out, (0, 0), (92, 26), (0, 0, 0), -1)
    cv2.putText(out, text, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def contact_sheets(thumbs: list[tuple[float, np.ndarray]], out_dir: Path) -> list[str]:
    per = SHEET_COLS * SHEET_ROWS
    names = []
    for k in range(0, len(thumbs), per):
        chunk = [_label(img, f"{t:6.1f}s") for t, img in thumbs[k:k + per]]
        _h, _w = chunk[0].shape[:2]
        blank = np.zeros_like(chunk[0])
        while len(chunk) % SHEET_COLS:
            chunk.append(blank)
        rows = [np.hstack(chunk[i:i + SHEET_COLS]) for i in range(0, len(chunk), SHEET_COLS)]
        name = f"sheet_{k // per + 1}.jpg"
        cv2.imwrite(str(out_dir / name), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
        names.append(name)
    return names


def mean_volume(path: Path) -> float | None:
    res = run([ffmpeg(), "-hide_banner", "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"], timeout=300)
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", res.stderr)
    return float(m.group(1)) if m else None


def analyze(path: Path, out_dir: Path, rec_id: str, every: float = 2.0) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in list(out_dir.glob("thumb_*.jpg")) + list(out_dir.glob("sheet_*.jpg")):
        old.unlink()
    info = probe(path)
    activity, thumbs = sample_video(path, every)
    thumb_files = []
    for t, img in thumbs:
        name = f"thumb_{t:07.2f}.jpg".replace(".", "_", 1)
        cv2.imwrite(str(out_dir / name), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        thumb_files.append({"t": t, "file": name})
    sheets = contact_sheets(thumbs, out_dir) if thumbs else []
    return {
        "id": rec_id,
        "file": str(path),
        "probe": info,
        "mean_volume_db": mean_volume(path) if info["has_audio"] else None,
        "scenes": detect_scenes(path),
        "activity_step_s": 0.5,
        "activity": activity,
        "thumb_every_s": every,
        "thumbs": thumb_files,
        "sheets": sheets,
        "dir": str(out_dir.relative_to(out_dir.parents[1])).replace("\\", "/"),
    }


def active_ranges(activity: list[float], step: float, threshold: float = 0.5, min_gap: float = 1.0) -> list[list[float]]:
    """把變化量超過門檻的取樣點合併成區間；間隔小於 min_gap 秒的區間視為同一段操作。"""
    ranges: list[list[float]] = []
    for i, a in enumerate(activity):
        if a < threshold:
            continue
        t0, t1 = i * step, (i + 1) * step
        if ranges and t0 - ranges[-1][1] <= min_gap:
            ranges[-1][1] = t1
        else:
            ranges.append([t0, t1])
    return [[round(a, 2), round(b, 2)] for a, b in ranges]


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc ingest-rec <project> [--every 秒數]")
        return 2
    every = float(argv[argv.index("--every") + 1]) if "--every" in argv else 2.0
    proj = load_project(argv[0])
    results = []
    for i, rec in enumerate(proj.recordings, 1):
        rec_id = f"rec{i:02d}"
        from vc.pipeline_safety import file_hash
        source_hash = file_hash(rec)
        r = analyze(rec, proj.work / "recordings" / rec_id, rec_id, every)
        if source_hash != file_hash(rec):
            print(f"{rec_id} 在匯入期間變更，請重新執行。", file=sys.stderr)
            return 1
        r["source_sha256"] = source_hash
        r["active_ranges"] = active_ranges(r["activity"], r["activity_step_s"])
        results.append(r)
        p = r["probe"]
        print(f"{rec_id}  {Path(r['file']).name}  {p['duration']:.1f}s  {p['width']}x{p['height']}  {p['fps']} fps  "
              f"audio={p['has_audio']}  mean_vol={r['mean_volume_db']}  scenes={len(r['scenes'])}  "
              f"thumbs={len(r['thumbs'])}  sheets={len(r['sheets'])}")
        print(f"  有操作的區間（秒）：{r['active_ranges']}")
    out = proj.work / "recordings.json"
    out.write_text(json.dumps({"recordings": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    return 0
