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
    p = Path(path)
    try:
        if p.drive and work.drive and p.drive.lower() != work.drive.lower():
            return p.resolve().as_posix()
        return Path(os.path.relpath(path, work)).as_posix()
    except ValueError:
        return p.resolve().as_posix()


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
    return subprocess.run(cmd, cwd=str(REMOTION_DIR), capture_output=True, check=False, text=True, encoding="utf-8",
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


def get_loudness_targets(proj_root: Path) -> tuple[float, float]:
    """從 project.yaml 讀取目標響度與 True Peak 限制，預設回退至 LOUDNESS_I (-14.0) 與 LOUDNESS_TP (-1.5)。"""
    cfg_path = proj_root / "project.yaml"
    if not cfg_path.is_file():
        return LOUDNESS_I, LOUDNESS_TP
    import yaml
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError, yaml.YAMLError):
        return LOUDNESS_I, LOUDNESS_TP

    if not isinstance(cfg, dict):
        return LOUDNESS_I, LOUDNESS_TP

    target_lufs = LOUDNESS_I
    target_tp = LOUDNESS_TP

    loud_cfg = cfg.get("loudness")
    if isinstance(loud_cfg, dict):
        if "target_lufs" in loud_cfg:
            target_lufs = float(loud_cfg["target_lufs"])
        elif "target_i" in loud_cfg:
            target_lufs = float(loud_cfg["target_i"])
        elif "i" in loud_cfg:
            target_lufs = float(loud_cfg["i"])
        if "true_peak" in loud_cfg:
            target_tp = float(loud_cfg["true_peak"])
        elif "true_peak_max_dbtp" in loud_cfg:
            target_tp = float(loud_cfg["true_peak_max_dbtp"])
        elif "tp" in loud_cfg:
            target_tp = float(loud_cfg["tp"])
    elif isinstance(loud_cfg, (int, float)):
        target_lufs = float(loud_cfg)

    if "target_lufs" in cfg and not (isinstance(loud_cfg, dict) and "target_lufs" in loud_cfg):
        target_lufs = float(cfg["target_lufs"])

    if "true_peak" in cfg and not (isinstance(loud_cfg, dict) and "true_peak" in loud_cfg):
        target_tp = float(cfg["true_peak"])
    elif "true_peak_max_dbtp" in cfg and not (isinstance(loud_cfg, dict) and "true_peak_max_dbtp" in loud_cfg):
        target_tp = float(cfg["true_peak_max_dbtp"])

    return target_lufs, target_tp


def normalize_loudness(src: Path, dst: Path, target_i: float = LOUDNESS_I, target_tp: float = LOUDNESS_TP) -> dict:
    """兩階段 loudnorm：先量測再套用，結果比單階段準。影像直接複製不重新編碼。"""
    from vc.media import ffmpeg, ffmpeg_run
    from vc.tools import run

    target = f"I={target_i}:TP={target_tp}:LRA=11"
    res = run([ffmpeg(), "-hide_banner", "-nostats", "-i", str(src), "-af", f"loudnorm={target}:print_format=json",
               "-f", "null", "-"], timeout=600)
    m = json.loads(res.stderr[res.stderr.rfind("{"):res.stderr.rfind("}") + 1])
    second = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg_run(["-i", str(src), "-c:v", "copy", "-af", second, "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(dst)], timeout=900)
    return measure_loudness(dst)


def main(argv: list[str]) -> int:
    import re
    import shutil
    import tempfile

    from vc.pipeline_safety import (
        alignment_is_current,
        atomic_write,
        check_ingest,
        check_voice,
        file_hash,
        media_is_current,
        missing_media,
        script_fingerprint,
        visual_fingerprint,
    )
    from vc.script import load_script
    from vc.script import main as validate
    from vc.voice import make_backend, voice_dir

    if not argv:
        print("用法：python -m vc render <project> [--name draft] [--no-gpu]")
        return 2
    if "--variant" in argv:
        print("已取消版本選項。請先執行 vc migrate，再使用單一影片輸出。", file=sys.stderr)
        return 2
    proj = load_project(argv[0])
    if validate([str(proj.root)]) != 0:
        return 1
    name = argv[argv.index("--name") + 1] if "--name" in argv else "draft"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        print("影片名稱只能包含英數字、底線及連字號。", file=sys.stderr)
        return 2
    try:
        script = load_script(proj.root / "script.json")
        v = script.meta.voice
        vdir = voice_dir(proj.work, make_backend(v.engine, v.name, v.rate))
        manifest = json.loads((vdir / "manifest.json").read_text(encoding="utf-8"))
        aligned = json.loads((proj.work / "align" / "words.json").read_text(encoding="utf-8"))
        tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
        check_voice(script, manifest, vdir)
        if (not alignment_is_current(aligned, manifest, vdir)
                or aligned.get("script_fingerprint") != script_fingerprint(script)
                or tl.get("script_fingerprint") != script_fingerprint(script)
                or tl.get("visual_fingerprint") != visual_fingerprint(proj.root, script, proj.work)
                or tl.get("voice_fingerprint") != aligned.get("voice_fingerprint")):
            raise ValueError("管線資料已過期，請依序執行 vc voice、vc align 和 vc plan。")
        rec_file = proj.work / "recordings.json"
        recs = json.loads(rec_file.read_text(encoding="utf-8"))["recordings"] if rec_file.is_file() else []
        check_ingest(proj, recs, script)
        current_recordings = {r["id"]: file_hash(Path(r["file"])) for r in recs}
        if tl.get("recording_fingerprints") != current_recordings:
            raise ValueError("錄影來源已變更，請重新執行 vc ingest-rec 和 vc plan。")
        rec_sizes = {r["id"]: (r["probe"]["width"], r["probe"]["height"]) for r in recs}
        if not rec_sizes:
            rec_sizes = tuple(tl["size"])
        props = build_props(tl, "main", proj.work, rec_sizes)
        missing = missing_media(props, proj.work)
        if missing:
            raise ValueError("缺少影片素材，請先渲染場景：" + ", ".join(sorted(set(missing))))
        for scene in props["scenes"]:
            sources = ([scene["anim_src"]] if scene.get("anim_src") else []) + [c["src"] for c in scene.get("clips", [])]
            if any(not media_is_current(proj.work / src, tl) for src in sources):
                raise ValueError(f"{scene['id']} 的畫面已過期，請重新執行 vc hf、vc manim 或 vc fit。")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"無法渲染：{exc}", file=sys.stderr)
        return 1

    bgm_candidates = [proj.input / "bgm.mp3", proj.input / "audio" / "bgm.mp3", proj.root / "bgm.mp3"]
    bgm_src = next((p for p in bgm_candidates if p.is_file()), None)
    bgm_dst = proj.work / "bgm.mp3"
    if bgm_src:
        shutil.copyfile(bgm_src, bgm_dst)
    elif bgm_dst.exists():
        bgm_dst.unlink()
    levels = measure_bgm_levels(proj.work, [Path(a["file"]) for a in tl["audio"]])
    props = build_props(tl, "main", proj.work, rec_sizes, levels)
    props_path = proj.work / "remotion" / "props.json"
    atomic_write(props_path, json.dumps(props, ensure_ascii=False).encode("utf-8"))
    proj.output.mkdir(parents=True, exist_ok=True)
    out = proj.output / f"{name}.mp4"
    target_lufs, target_tp = get_loudness_targets(proj.root)
    try:
        with tempfile.TemporaryDirectory(prefix=".render-", dir=proj.output) as temp:
            raw = Path(temp) / "raw.mp4"
            candidate = Path(temp) / "result.mp4"
            res = render(props_path, raw, proj.work, use_gpu="--no-gpu" not in argv)
            if res.returncode != 0 or not raw.is_file():
                raise RuntimeError("Remotion 渲染失敗：" + (res.stdout + res.stderr)[-2000:])
            loud = normalize_loudness(raw, candidate, target_i=target_lufs, target_tp=target_tp)
            info, frames = probe(candidate), count_frames(candidate)
            if not (frames == tl["total_frames"] and info["has_audio"] and loud["I"] is not None
                    and abs(loud["I"] - target_lufs) <= 1.0
                    and loud["TP"] is not None and loud["TP"] <= target_tp + 0.1):
                raise RuntimeError("輸出未通過影格數、音訊或響度檢查。")
            os.replace(candidate, out)
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"渲染失敗：{exc}", file=sys.stderr)
        return 1
    reports = proj.output / "reports"
    metadata = {"project": proj.name, "file": out.name, "fps": tl["fps"], "total_frames": frames,
                "duration_s": info["duration"], "width": info["width"], "height": info["height"],
                "file_size_bytes": out.stat().st_size}
    loudness = {"target_lufs": target_lufs, "true_peak_max_dbtp": target_tp,
                "integrated_lufs": loud["I"], "true_peak_dbtp": loud["TP"], "compliant": True}
    atomic_write(reports / "metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"))
    atomic_write(reports / "loudness_report.json", json.dumps(loudness, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"影片完成：{out}，{frames} 格，{loud['I']} LUFS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
