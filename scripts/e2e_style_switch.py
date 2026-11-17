"""M4 端到端驗證：同一份場景在不同風格與運鏡設定下，實際建置、lint、渲染並比對輸出。

用法：.venv\\Scripts\\python.exe scripts\\e2e_style_switch.py [--out <dir>] [--no-render]
結束碼 0 表示全部組合通過；非 0 表示至少一項檢查失敗。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vc.hf_scenes import _hf, _run_in, build_project, lint  # noqa: E402
from vc.style_config import project_visual_settings  # noqa: E402
from vc.tools import find_tool  # noqa: E402

COMBOS = [
    ("executive_navy", "fixed"),
    ("swiss_kinetic", "cinematic"),
    ("blueprint", "dynamic"),
]
FPS = 30
DURATION_FRAMES = 135


def make_timeline() -> dict:
    scene = {
        "id": "s01", "duration_frames": DURATION_FRAMES,
        "narration_start_frame": 0, "narration_frames": 105,
        "at_frames": {"claim": 45},
        "visuals": {"public": {"kind": "anim", "template": "title", "images": [],
                               "data": {"title": "Style switch check", "subtitle": "Each claim has a source",
                                        "at_word": "claim"}}},
    }
    return {"fps": FPS, "scenes": [scene]}


def make_project(root: Path, style: str, mode: str) -> Path:
    proj = root / f"{style}__{mode}"
    (proj / "work").mkdir(parents=True, exist_ok=True)
    cfg = {"name": proj.name, "style": style, "camera_mode": mode, "fps": FPS, "resolution": [1920, 1080]}
    (proj / "project.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    if mode == "cinematic":
        plan = {"shots": [{"shot_id": "a", "scene_ref": "s01", "start_time_s": 0, "end_time_s": 4.5,
                           "camera_motion": {"type": "dolly_in", "end_scale": 1.08}}]}
        (proj / "camera_plan.json").write_text(json.dumps(plan), encoding="utf-8")
        cfg["camera_plan"] = "camera_plan.json"
        (proj / "project.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return proj


def sha(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12]


def grab_frame(video: Path, out: Path, second: float) -> None:
    subprocess.run([find_tool("ffmpeg"), "-y", "-v", "error", "-ss", str(second), "-i", str(video),
                    "-frames:v", "1", str(out)], check=True)


def run(out_dir: Path, render: bool) -> int:
    tl = make_timeline()
    report, failures = [], []
    for style, mode in COMBOS:
        proj = make_project(out_dir, style, mode)
        work = proj / "work"
        style_cfg, camera_cfg = project_visual_settings(proj)
        folder = build_project(tl["scenes"][0], "public", tl, work, style_cfg, camera_cfg)
        html = (folder / "index.html").read_text(encoding="utf-8")
        errors, _ = lint(folder)
        entry = {"style": style, "camera_mode": mode, "html_sha": sha(folder / "index.html"),
                 "background": style_cfg["tokens"]["colors"]["background"], "lint_errors": errors,
                 "has_camera_tween": "camera" in html.lower()}
        if errors:
            failures.append(f"{style}/{mode}: lint errors={errors}")
        if render:
            mp4 = proj / "output" / "public" / "s01_public.mp4"
            mp4.parent.mkdir(parents=True, exist_ok=True)
            res = _run_in(folder, [_hf(), "render", "--quality", "draft", "--output", str(mp4)])
            if res.returncode != 0 or not mp4.is_file():
                failures.append(f"{style}/{mode}: render failed: {(res.stdout + res.stderr)[-300:]}")
            else:
                png = proj / "output" / "reports" / "frame_3s.png"
                png.parent.mkdir(parents=True, exist_ok=True)
                grab_frame(mp4, png, 3.0)
                entry.update(mp4=str(mp4.relative_to(out_dir)), mp4_bytes=mp4.stat().st_size, frame_sha=sha(png))
        report.append(entry)
    if len({e["html_sha"] for e in report}) != len(report):
        failures.append("Two combos produced identical HTML.")
    if render and len({e.get("frame_sha") for e in report}) != len(report):
        failures.append("Two combos produced identical frames.")
    if len({e["background"] for e in report}) != len(report):
        failures.append("Two combos share one background color.")
    (out_dir / "e2e_report.json").write_text(json.dumps({"combos": report, "failures": failures}, indent=2),
                                             encoding="utf-8")
    print(json.dumps({"combos": report, "failures": failures}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="vc_e2e_styles_"))
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    return run(out, not args.no_render)


if __name__ == "__main__":
    sys.exit(main())
