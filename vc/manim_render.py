"""Story 3：把時間軸上的觸發字換成秒數，交給 Manim 渲染，再把輸出裁成精確影格數。

這個模組不載入 manim（測試可以快速跑）；動畫本身在 vc/manim_scenes.py。

每段產出：
  work/manim/<scene>_cues.json   觸發時間（相對段落起點的秒數）與段落總長
  work/manim/<scene>_sync.json   渲染時記錄的每個觸發點實際時間與延遲
  work/manim/<scene>.mp4         影格數 = 時間軸上的段落影格數
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from vc.fit import count_frames
from vc.media import ffmpeg_run, h264_encode_args
from vc.project import load_project
from vc.tools import ROOT, find_tool

SCENES_FILE = ROOT / "vc" / "manim_scenes.py"
MAX_LATE_FRAMES = 2       # 動畫比旁白晚超過 2 格就視為不同步


def scene_cues(scene: dict, variant: str, fps: int) -> dict:
    """回傳 {"duration": 秒, "cues": {what: 秒}}；cues 的時間相對於段落起點（已含導入空檔）。"""
    data = scene["visuals"][variant]["data"]
    cues = {}
    for c in data.get("cues", []):
        frame = scene["at_frames"].get(c["at_word"])
        if frame is None:
            raise ValueError(f"{scene['id']}: 觸發字「{c['at_word']}」沒有時間")
        cues[c["what"]] = round(frame / fps, 3)
    narration_end = (scene["narration_start_frame"] + scene["narration_frames"]) / fps
    return {"scene": scene["id"], "variant": variant, "duration": round(scene["duration_frames"] / fps, 3),
            "fps": fps, "cues": cues, "narration_end": round(narration_end, 3),
            "options": {k: v for k, v in data.items() if k not in ("cues", "scene_class")}}


def max_lateness_frames(sync: dict, fps: int) -> float:
    return max((max(0.0, e["actual"] - e["target"]) * fps for e in sync["events"]), default=0.0)


def _key(cue_data: dict) -> str:
    raw = json.dumps(cue_data, sort_keys=True) + SCENES_FILE.read_text(encoding="utf-8")
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def render_scene(scene: dict, variant: str, fps: int, out_dir: Path, use_gpu: bool = True, force: bool = False) -> dict:
    cls = scene["visuals"][variant]["data"]["scene_class"]
    cue_data = scene_cues(scene, variant, fps)
    # 片尾 logo 用 vc/brand.py 產生的透明 PNG（只有 internal 版會用到）
    cue_data["options"]["brand_dir"] = str((out_dir.parent / "brand").resolve())
    sid = scene["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cue_path, sync_path, out = out_dir / f"{sid}_cues.json", out_dir / f"{sid}_sync.json", out_dir / f"{sid}.mp4"
    key = _key(cue_data)
    old = json.loads(cue_path.read_text(encoding="utf-8")) if cue_path.is_file() else {}
    if not force and old.get("key") == key and out.is_file() and sync_path.is_file():
        return {"scene": sid, "made": False, "file": out, "sync": json.loads(sync_path.read_text(encoding="utf-8"))}

    cue_path.write_text(json.dumps({**cue_data, "key": key}, ensure_ascii=False, indent=2), encoding="utf-8")
    sync_path.unlink(missing_ok=True)
    media = out_dir / "_media"
    shutil.rmtree(media, ignore_errors=True)
    env = dict(os.environ, VC_MANIM_CUES=str(cue_path), VC_MANIM_SYNC=str(sync_path), PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(find_tool("ffmpeg")).parent) + os.pathsep + env["PATH"]
    cmd = [sys.executable, "-m", "manim", "render", "-r", "1920,1080", "--fps", str(fps),
           "--disable_caching", "--media_dir", str(media), "-o", sid, str(SCENES_FILE), cls]
    res = subprocess.run(cmd, capture_output=True, check=False, text=True, encoding="utf-8", errors="replace",
                         timeout=1800, env=env, cwd=str(ROOT))
    found = list(media.rglob(f"{sid}.mp4"))
    if res.returncode != 0 or not found:
        raise RuntimeError(f"{sid}: Manim 渲染失敗\n{(res.stdout + res.stderr)[-2500:]}")
    # 補停格再截到時間軸的精確影格數
    out.unlink(missing_ok=True)
    ffmpeg_run(["-i", str(found[0]), "-vf", "tpad=stop_mode=clone:stop_duration=2",
                "-frames:v", str(scene["duration_frames"]), "-an",
                *h264_encode_args(quality=14, cpu_preset="medium", use_gpu=use_gpu),
                "-pix_fmt", "yuv420p", "-r", str(fps), str(out)])
    return {"scene": sid, "made": True, "file": out, "sync": json.loads(sync_path.read_text(encoding="utf-8"))}


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc manim <project> [--scene s04] [--no-gpu]")
        return 2
    proj = load_project(argv[0])
    only = argv[argv.index("--scene") + 1] if "--scene" in argv else None
    if "--variant" in argv:
        print("已取消版本選項，請使用單一影片。", file=sys.stderr)
        return 2
    variant = "main"
    use_gpu = "--no-gpu" not in argv
    tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
    fps, bad = tl["fps"], []
    for sc in tl["scenes"]:
        if sc["visuals"][variant]["kind"] != "manim" or (only and sc["id"] != only):
            continue
        from vc.pipeline_safety import media_is_current
        output = proj.work / "manim" / f"{sc['id']}.mp4"
        r = render_scene(sc, variant, fps, proj.work / "manim", use_gpu=use_gpu, force=not media_is_current(output, tl))
        n, late = count_frames(r["file"]), max_lateness_frames(r["sync"], fps)
        ok = n == sc["duration_frames"] and late <= MAX_LATE_FRAMES
        if ok:
            from vc.pipeline_safety import mark_media
            mark_media(r["file"], tl)
        bad += [] if ok else [sc["id"]]
        print(f"{sc['id']}: {n}/{sc['duration_frames']} 格  觸發點 {len(r['sync']['events'])} 個  "
              f"最大延遲 {late:.1f} 格  {'重新渲染' if r['made'] else '快取'}")
        for e in r["sync"]["events"]:
            flag = "  <-- 太晚" if (e["actual"] - e["target"]) * fps > MAX_LATE_FRAMES else ""
            print(f"    {e['cue']:<10} 目標 {e['target']:6.2f}s  實際 {e['actual']:6.2f}s{flag}")
    if bad:
        print(f"沒通過（影格數不符或動畫晚於旁白）：{bad}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
