"""Story 10：把 kind=anim 的段落產生成 HyperFrames 專案並渲染成 MP4。

每個段落、每個版本各一個資料夾：work/hf/<variant>/<scene>/index.html。
動畫時間點來自 timeline.json 的 at_frames（旁白念到某個字的影格），所以畫面跟旁白同步。
畫面下方 150 px 保留給字幕，範本不放內容。

輸出：work/hf/<variant>/<scene>.mp4 與 work/hf/manifest.json（快取）
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from vc.media import can_use_nvenc
from vc.project import load_project
from vc.tools import ROOT, find_tool
from vc.style_config import load_style, project_visual_settings, validate_style, _number
from vc.camera import scene_camera

FONT_SRC = {"segoeui.ttf": Path("C:/Windows/Fonts/segoeui.ttf"), "segoeuib.ttf": Path("C:/Windows/Fonts/segoeuib.ttf")}
GSAP = ROOT / "node_modules" / "gsap" / "dist" / "gsap.min.js"

TEMPLATE_NAMES = ("title", "concept", "cards3", "steps4", "result", "demo_mock", "vs_intro_mock", "chassis_mock")
TEMPLATE_ENV = Environment(loader=FileSystemLoader(ROOT / "styles" / "templates"),
                           autoescape=True, undefined=StrictUndefined)


def render_scene_html(scene_type: str, context: dict, style_config: dict | None = None,
                      camera_config: dict | None = None) -> str:
    """以外部 Jinja2 樣板生成場景，文字預設 HTML 跳脫。"""
    if scene_type not in TEMPLATE_NAMES:
        raise ValueError(f"Unknown scene template: {scene_type}.")
    style = validate_style(style_config) if style_config is not None else load_style()
    duration = _number(context.get("duration"), "duration", 0.01, 86400)
    fps = _number(context.get("fps", 30), "fps", 1, 240)
    comp_id = context.get("comp_id", "scene-public")
    if not isinstance(comp_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", comp_id):
        raise ValueError("Use letters, digits, underscores, or hyphens in composition IDs.")
    data = context.get("data", {})
    at = context.get("at_frames", {})
    if not isinstance(data, dict) or not isinstance(at, dict):
        raise ValueError("Set scene data and at_frames to objects.")
    for frame in at.values():
        if frame is not None:
            _number(frame, "at_frames", 0, duration * fps)
    def cue(term, fallback):
        frame = at.get(term)
        return round(frame / fps, 3) if frame is not None else fallback
    reveal = {item["what"]: cue(item["at_word"], 0) for item in data.get("reveal", [])}
    count_prefix, count_suffix, count_value = "", "", None
    if scene_type == "result":
        value = str(data["after"]["value"])
        match = re.search(r"[0-9]+", value)
        if match:
            count_prefix, count_suffix = value[:match.start()], value[match.end():]
            count_value = int(match.group())
        else:
            count_prefix = value
    if scene_type in ("cards3", "steps4"):
        inset = data.get("inset", {})
        if "image" not in inset and inset.get("drawing") not in ("hole_in_plate", "offset_half"):
            raise ValueError("Set inset to a supported drawing or an image index.")
    shots = scene_camera(camera_config, context.get("scene_id", comp_id), duration)
    html = TEMPLATE_ENV.get_template(f"{scene_type}.html.j2").render(
        style=style, d=data, D=duration, duration=duration, fps=fps, comp_id=comp_id,
        images=context.get("images", {"list": []}), cue=cue, reveal=reveal,
        count_prefix=count_prefix, count_suffix=count_suffix, count_value=count_value,
        camera_shots=shots)
    for shot in shots:
        motion = shot["camera_motion"]
        if motion["type"] == "focus_target" and f'id="{motion["target_selector"][1:]}"' not in html:
            raise ValueError(f"Camera target does not exist: {motion['target_selector']}.")
    return html


# ---------- 產生與渲染 ----------

def brand_logos(work: Path) -> dict[str, Path]:
    """產生深色背景適用的高解析度透明 PNG 品牌標誌（internal 版使用）。"""
    from vc.brand import TEMPLATES, make_logos

    out = work / "brand"
    files = {"primary": out / "primary_white.png", "secondary": out / "secondary_white.png"}
    custom = [TEMPLATES / "primary_logo.png", TEMPLATES / "secondary_logo.png"]
    custom_mtime = max((s.stat().st_mtime for s in custom if s.is_file()), default=0.0)
    if not all(f.is_file() for f in files.values()) or (
        custom_mtime and custom_mtime > min(f.stat().st_mtime for f in files.values())
    ):
        files = make_logos(out)
    return files


def build_project(scene: dict, variant: str, tl: dict, work: Path,
                  style_config: dict | None = None, camera_config: dict | None = None) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", scene["id"]) or variant not in ("internal", "public"):
        raise ValueError("Use safe scene IDs and internal or public variants.")
    vis = scene["visuals"][variant]
    if variant == "public" and vis.get("images"):
        raise ValueError("Remove source images from the public variant.")
    if style_config is None or camera_config is None:
        project_style, project_camera = project_visual_settings(work.parent)
        style_config = project_style if style_config is None else style_config
        camera_config = project_camera if camera_config is None else camera_config
    fps = tl["fps"]
    D = round(scene["duration_frames"] / fps, 4)
    folder = work / "hf" / variant / scene["id"]
    assets = folder / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GSAP, assets / "gsap.min.js")
    for name, src in FONT_SRC.items():
        shutil.copyfile(src, assets / name)
    images = {"list": []}
    for i, img in enumerate(vis.get("images", [])):
        dst = assets / f"img{i}{Path(img).suffix}"
        shutil.copyfile(img, dst)
        images["list"].append(f"assets/{dst.name}")
    if variant == "internal":
        for name, f in brand_logos(work).items():
            shutil.copyfile(f, assets / f.name)
            images[name] = f"assets/{f.name}"
    data = dict(vis["data"])
    # 旁白念完後 0.4 s 才換片尾，避免最後一句還沒講完畫面就變
    data["outro_at_s"] = round((scene["narration_start_frame"] + scene["narration_frames"]) / fps + 0.4, 3)
    html = render_scene_html(vis["template"], {
        "data": data, "at_frames": scene["at_frames"], "duration": D, "fps": fps,
        "images": images, "scene_id": scene["id"], "comp_id": f"{scene['id']}-{variant}",
    }, style_config, camera_config)
    (folder / "index.html").write_text(html, encoding="utf-8")
    return folder


def _hf() -> str:
    exe = find_tool("hyperframes")
    if not exe:
        raise FileNotFoundError("找不到 hyperframes，在專案根目錄執行 npm install")
    return exe


def folder_key(folder: Path) -> str:
    h = hashlib.sha1()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and ".hyperframes" not in p.parts:
            h.update(p.relative_to(folder).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def lint(folder: Path) -> tuple[int, str]:
    res = _run_in(folder, [_hf(), "lint"], timeout=300)
    text = res.stdout + res.stderr
    m = re.search(r"(\d+) error", text)
    return (int(m.group(1)) if m else (0 if res.returncode == 0 else 1)), text


def _run_in(folder: Path, cmd: list[str], timeout: float = 900):
    env = dict(os.environ, NODE_USE_SYSTEM_CA="1")
    env["PATH"] = str(Path(find_tool("ffmpeg")).parent) + os.pathsep + env["PATH"]
    return subprocess.run(cmd, cwd=str(folder), capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, env=env)


def render_all(tl: dict, work: Path, quality: str = "draft", use_gpu: bool = True) -> list[dict]:
    man_path = work / "hf" / "manifest.json"
    old = json.loads(man_path.read_text(encoding="utf-8")) if man_path.is_file() else {}
    style_config, camera_config = project_visual_settings(work.parent)
    scene_ids = {scene["id"] for scene in tl["scenes"]}
    camera_scene_ids = {shot["scene_ref"] for shot in camera_config["shots"]}
    unknown = camera_scene_ids - scene_ids
    if unknown:
        raise ValueError(f"Camera plan contains unknown scene IDs: {sorted(unknown)}.")
    unsupported = [f"{scene['id']}/{variant} ({visual.get('kind')})"
                   for scene in tl["scenes"] if scene["id"] in camera_scene_ids
                   for variant, visual in scene["visuals"].items() if visual.get("kind") != "anim"]
    if unsupported:
        raise ValueError(f"Camera plans support only anim scenes. Unsupported targets: {', '.join(unsupported)}.")
    gpu_ready = use_gpu and can_use_nvenc()
    new, report = {}, []
    for sc in tl["scenes"]:
        for variant in ("internal", "public"):
            if sc["visuals"][variant]["kind"] != "anim":
                continue
            folder = build_project(sc, variant, tl, work, style_config, camera_config)
            out = work / "hf" / variant / f"{sc['id']}.mp4"
            key = folder_key(folder) + quality
            entry = {"scene": sc["id"], "variant": variant, "file": str(out.relative_to(work)).replace("\\", "/")}
            if old.get(entry["file"]) == key and out.is_file():
                entry["made"] = False
            else:
                errors, text = lint(folder)
                if errors:
                    raise RuntimeError(f"{sc['id']}/{variant} lint 有 {errors} 個錯誤：\n{text[-1500:]}")
                out.unlink(missing_ok=True)
                cpu_cmd = [_hf(), "render", "--quality", quality, "--output", str(out)]
                if gpu_ready:
                    gpu_cmd = [_hf(), "render", "--gpu", "--browser-gpu", "--quality", quality, "--output", str(out)]
                    res = _run_in(folder, gpu_cmd)
                    if res.returncode != 0 or not out.is_file():
                        out.unlink(missing_ok=True)
                        res = _run_in(folder, cpu_cmd)
                else:
                    res = _run_in(folder, cpu_cmd)
                if res.returncode != 0 or not out.is_file():
                    raise RuntimeError(f"{sc['id']}/{variant} 渲染失敗：\n{(res.stdout + res.stderr)[-1500:]}")
                entry["made"] = True
            new[entry["file"]] = key
            report.append(entry)
            man_path.write_text(json.dumps(new, indent=2), encoding="utf-8")
    return report


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc hf <project> [--quality draft|looks|delivery] [--no-gpu]")
        return 2
    proj = load_project(argv[0])
    quality = argv[argv.index("--quality") + 1] if "--quality" in argv else "draft"
    use_gpu = "--no-gpu" not in argv
    tl = json.loads((proj.work / "timeline.json").read_text(encoding="utf-8"))
    from vc.fit import count_frames

    report = render_all(tl, proj.work, quality, use_gpu=use_gpu)
    frames = {s["id"]: s["duration_frames"] for s in tl["scenes"]}
    bad = []
    for r in report:
        n = count_frames(proj.work / r["file"])
        ok = abs(n - frames[r["scene"]]) <= 1
        bad += [] if ok else [r["file"]]
        print(f"{r['file']:<28} 影格 {n:>4} / {frames[r['scene']]:<4} {'重新渲染' if r['made'] else '快取'}")
    if bad:
        print(f"影格數不符：{bad}", file=sys.stderr)
        return 1
    print("全部動畫段落渲染完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
