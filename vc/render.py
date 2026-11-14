"""Story 9：把 timeline.json 轉成 Remotion props，渲染 internal / public 兩個版本。

Remotion 以專案的 work/ 當 public 資料夾，所以 props 裡的檔案路徑都相對於 work/。
動畫段落若還沒有 HyperFrames 片段，會顯示佔位畫面。

輸出：output/<variant>/<name>.mp4，預設 name=draft
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from vc.fit import count_frames
from vc.media import probe
from vc.project import load_project
from vc.tools import ROOT, find_tool

REMOTION_DIR = ROOT / "remotion"


def _rel(path: str, work: Path) -> str:
    return Path(os.path.relpath(path, work)).as_posix()


def build_props(tl: dict, variant: str, work: Path,
                rec_size: tuple[int, int] | dict[str, tuple[int, int]],
                bgm_levels: tuple[float, float] | None = None) -> dict:
    # 各支來源錄影解析度可能不同（如 1912x1020 與 1920x1200），
    # 片段與標註框皆須以各自來源尺寸換算，避免畫面變形與座標偏移。
    sizes = rec_size if isinstance(rec_size, dict) else {}
    default = next(iter(sizes.values())) if sizes else rec_size
    scenes = []
    for sc in tl["scenes"]:
        v = sc["visuals"][variant]
        anim = work / "hf" / variant / f"{sc['id']}.mp4"
        manim_file = work / "manim" / f"{sc['id']}.mp4"
        timer = v.get("data", {}).get("timer_card") if v["kind"] == "recording" and "data" in v else None

        anim_src = None
        if v["kind"] == "anim" and anim.is_file():
            anim_src = f"hf/{variant}/{sc['id']}.mp4"
        elif v["kind"] == "manim" and manim_file.is_file():
            anim_src = f"manim/{sc['id']}.mp4"

        scenes.append({
            "id": sc["id"],
            "start_frame": sc["start_frame"],
            "duration_frames": sc["duration_frames"],
            "kind": v["kind"],
            "anim_src": anim_src,
            "clips": [
                {
                    "src": c["file"],
                    "start_frame": c["start_frame"],
                    "duration_frames": c["duration_frames"],
                    "crop": c["crop"],
                    "label": c["label"],
                    "camera": c.get("camera"),
                    "rec_size": list(sizes.get(c.get("recording"), default)),
                }
                for c in v.get("clips", [])
            ],
            "callouts": [
                {
                    "frame": c["frame"],
                    "box": c["box"],
                    "text": c["text"],
                    "clip": c["clip"],
                }
                for c in v.get("callouts", [])
            ],
            "timer": {"clip": timer["clip"], "text": timer["text"]} if timer else None,
            "bg_image": v.get("data", {}).get("bg_image"),
            "overlay_title": v.get("data", {}).get("overlay_title"),
            "logo": v.get("data", {}).get("logo", False),
        })
    props = {
        "variant": variant,
        "fps": tl["fps"],
        "size": tl["size"],
        "total_frames": tl["total_frames"],
        "rec_size": list(default),
        "audio": [
            {
                "src": _rel(a["file"], work),
                "start_frame": a["start_frame"],
                "duration_frames": a["duration_frames"],
            }
            for a in tl["audio"]
        ],
        "cues": tl["cues"],
        "scenes": scenes,
    }
    bgm_file = work / "bgm.mp3"
    if bgm_file.is_file() and bgm_levels:
        speech, gap = bgm_gains(*bgm_levels)
        props["bgm"] = {"src": "bgm.mp3", "speech_volume": speech, "gap_volume": gap}
    return props


def measure_bgm_levels(work: Path, voice_files: list[Path]) -> tuple[float, float] | None:
    """量配樂與旁白（各段平均）的整合響度。"""
    bgm = work / "bgm.mp3"
    if not bgm.is_file() or not voice_files:
        return None
    music = measure_loudness(bgm)["I"]
    voices = [measure_loudness(f)["I"] for f in voice_files]
    voices = [v for v in voices if v is not None]
    if music is None or not voices:
        return None
    return music, sum(voices) / len(voices)


def render(props_path: Path, out: Path, work: Path, use_gpu: bool = True) -> subprocess.CompletedProcess:
    exe = find_tool("remotion")
    if not exe:
        raise FileNotFoundError("找不到 remotion，在 remotion\\ 執行 npm install")
    out.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, NODE_USE_SYSTEM_CA="1")
    cmd = [exe, "render", "src/index.ts", "Main", str(out), f"--props={props_path}",
           f"--public-dir={work}", "--log=error"]
    # 啟用 ANGLE GPU 與硬體加速（無可用 GPU 時自動回退軟體算圖）
    if use_gpu and os.environ.get("VC_GPU", "auto").strip().lower() not in {"0", "false", "off", "cpu"}:
        cmd.extend(["--gl=angle", "--hardware-acceleration=if-possible"])
    return subprocess.run(cmd, cwd=str(REMOTION_DIR), capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=3600, env=env)


LOUDNESS_I = -14.0     # YouTube 等平台的常用目標
LOUDNESS_TP = -1.5
# 配樂相對旁白的響度：旁白進行時低 20 dB、停頓時低 14 dB。
# 2026-11-13 實測配樂 -12.4 LUFS、旁白 -27.4 LUFS，舊的固定倍率讓停頓時配樂比旁白還大聲。
BGM_UNDER_SPEECH_DB = 20.0
BGM_UNDER_GAP_DB = 14.0


def bgm_gains(music_lufs: float, voice_lufs: float) -> tuple[float, float]:
    """回傳（旁白時、停頓時）的配樂線性音量倍率。"""
    def gain(target_db_below: float) -> float:
        return round(10 ** ((voice_lufs - target_db_below - music_lufs) / 20), 4)
    return min(gain(BGM_UNDER_SPEECH_DB), 1.0), min(gain(BGM_UNDER_GAP_DB), 1.0)


def measure_loudness(path: Path) -> dict:
    """ebur128 量整合響度（LUFS）與 true peak（dBTP）。"""
    from vc.media import ffmpeg
    from vc.tools import run

    res = run([ffmpeg(), "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
               "-f", "null", "-"], timeout=600)
    import re
    tail = res.stderr[res.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"True peak:\s+Peak:\s+(-?[\d.]+) dBFS", tail)
    return {"I": float(i.group(1)) if i else None, "TP": float(tp.group(1)) if tp else None}


def normalize_loudness(src: Path, dst: Path) -> dict:
    """兩階段 loudnorm：先量測再套用，結果比單階段準。影像直接複製不重新編碼。"""
    from vc.media import ffmpeg, ffmpeg_run
    from vc.tools import run

    target = f"I={LOUDNESS_I}:TP={LOUDNESS_TP}:LRA=11"
    res = run([ffmpeg(), "-hide_banner", "-nostats", "-i", str(src), "-af", f"loudnorm={target}:print_format=json",
               "-f", "null", "-"], timeout=600)
    m = json.loads(res.stderr[res.stderr.rfind("{"):res.stderr.rfind("}") + 1])
    second = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg_run(["-i", str(src), "-c:v", "copy", "-af", second, "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(dst)], timeout=900)
    return measure_loudness(dst)


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc render <project> [--variant internal|public|all] [--name draft] [--no-gpu]")
        return 2
    proj = load_project(argv[0])
    variant = argv[argv.index("--variant") + 1] if "--variant" in argv else "all"
    name = argv[argv.index("--name") + 1] if "--name" in argv else "draft"
    use_gpu = "--no-gpu" not in argv
    tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
    recs = json.loads((proj.work / "recordings.json").read_text(encoding="utf-8"))["recordings"]
    rec_sizes = {r["id"]: (r["probe"]["width"], r["probe"]["height"]) for r in recs}
    variants = ("internal", "public") if variant == "all" else (variant,)

    import shutil
    # 配樂優先序：專案 input/bgm.mp3 -> 專案根目錄 bgm.mp3 -> 共用範本 Videos/Templates/bgm.mp3
    bgm_candidates = [proj.input / "bgm.mp3", proj.dir / "bgm.mp3", ROOT / "Videos" / "Templates" / "bgm.mp3"]
    bgm_src = next((p for p in bgm_candidates if p.is_file()), None)
    bgm_dst = proj.work / "bgm.mp3"
    if bgm_src is not None:
        if not bgm_dst.is_file() or bgm_src.stat().st_mtime > bgm_dst.stat().st_mtime:
            shutil.copyfile(bgm_src, bgm_dst)
    else:
        bgm_dst.unlink(missing_ok=True)

    levels = measure_bgm_levels(proj.work, [Path(a["file"]) for a in tl["audio"]])
    if levels:
        sp, gp = bgm_gains(*levels)
        print(f"配樂 {levels[0]:.1f} LUFS、旁白平均 {levels[1]:.1f} LUFS → 配樂音量 旁白時 {sp}、停頓時 {gp}")

    failed = []
    for v in variants:
        props = build_props(tl, v, proj.work, rec_sizes, levels)
        missing = [s["id"] for s in props["scenes"] if s["kind"] in ("anim", "manim") and not s["anim_src"]]
        props_path = proj.work / "remotion" / f"props_{v}.json"
        props_path.parent.mkdir(parents=True, exist_ok=True)
        props_path.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
        out = proj.output / v / f"{name}.mp4"
        raw = proj.work / "remotion" / f"raw_{v}.mp4"
        raw.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
        # 首次渲染啟用 GPU（若遇 ERR_NETWORK_CHANGED 或驅動不相容則自動回退 CPU 重試）
        for attempt in range(2):
            res = render(props_path, raw, proj.work, use_gpu=use_gpu and attempt == 0)
            if res.returncode == 0 and raw.is_file():
                break
        if res.returncode != 0 or not raw.is_file():
            print(f"{v}: Remotion 渲染失敗\n{(res.stdout + res.stderr)[-2000:]}", file=sys.stderr)
            failed.append(v)
            continue
        loud = normalize_loudness(raw, out)
        info, n = probe(out), count_frames(out)
        ok = (n == tl["total_frames"] and info["has_audio"] and loud["I"] is not None
              and abs(loud["I"] - LOUDNESS_I) <= 1.0 and (loud["TP"] is None or loud["TP"] <= LOUDNESS_TP + 0.7))
        failed += [] if ok else [v]
        print(f"{v}: {out}  {info['duration']:.2f}s  {n}/{tl['total_frames']} 格  "
              f"{info['width']}x{info['height']}  {loud['I']} LUFS  峰值 {loud['TP']} dBTP  佔位畫面={missing or '無'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
