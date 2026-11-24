"""在獨立工具環境分析本機參考影片，保留來源與待人工確認狀態。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from vc.media import probe
from vc.project import load_project
from vc.tools import ROOT, find_tool

REA_COMMIT = "bc97f214ebedfdc6510a9b2241cd8f8222f63517"


class ReferenceError(ValueError):
    """參考影片無法分析，或工具產物不完整。"""


def tool_path() -> Path:
    folder = ROOT / "tools" / "rea-video" / ".venv"
    return folder / ("Scripts/rea-video.exe" if os.name == "nt" else "bin/rea-video")


def source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def analyze(project_root: Path, video: Path, name: str = "reference", *,
            executable: Path | None = None, timeout: float = 3600) -> Path:
    video = video.expanduser().resolve()
    if not video.is_file():
        raise ReferenceError("Select an existing local video file.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", name):
        raise ReferenceError("Use 1 to 80 letters, digits, hyphens, or underscores for the analysis name.")
    executable = (executable or tool_path()).resolve()
    if not executable.is_file():
        raise ReferenceError("Install the isolated tool with scripts/setup-reference.ps1.")
    try:
        info = probe(video)
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ReferenceError("Select a valid video that FFmpeg can read.") from exc
    if not info.get("duration", 0) > 0:
        raise ReferenceError("Select a valid video with a positive duration.")

    root = project_root.resolve() / "work" / "references"
    out = root / name
    root.mkdir(parents=True, exist_ok=True)
    # 直接保留工具的輸出路徑，避免移動目錄後使上游報告中的絕對路徑失效。
    try:
        out.mkdir()
    except FileExistsError as exc:
        raise ReferenceError("The analysis already exists. Select a new name.") from exc
    state = out / ".state"
    state.mkdir()
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("REA_", "GEMINI_", "GOOGLE_", "OPENAI_", "CAPSULE_"))}
    env.update(REA_VIDEO_HOME=str(state), REA_VIDEO_MODELS=str(ROOT / "models" / "rea-video"),
               PYTHONIOENCODING="utf-8")
    ffmpeg = find_tool("ffmpeg")
    if ffmpeg:
        env["PATH"] = str(Path(ffmpeg).parent) + os.pathsep + env.get("PATH", "")
    command = [str(executable), "decompose", str(video), "-o", str(out), "--no-vlm", "--lang", "zh"]
    try:
        result = subprocess.run(command, cwd=str(out), env=env, capture_output=True, check=False,
                                text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReferenceError(f"The local analysis tool did not complete. Inspect {out}.") from exc
    if result.returncode:
        (out / "tool.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        raise ReferenceError(f"The local analysis tool failed with exit code {result.returncode}. Inspect {out / 'tool.log'}.")
    required = ("VIDEO.md", "report.html", "breakdown.json")
    if any(not (out / filename).is_file() for filename in required):
        raise ReferenceError(f"The analysis lacks required reports. Inspect {out}.")
    try:
        breakdown = json.loads((out / "breakdown.json").read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise ReferenceError("The analysis report contains invalid JSON.") from exc
    manifest = {"schema_version": 1, "source": str(video), "source_sha256": source_hash(video),
                "tool_commit": REA_COMMIT, "cloud_models": False, "review_required": True,
                "media": info, "summary": breakdown.get("summary", {})}
    (out / "analysis.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Analyze a local reference video without cloud models.")
    parser.add_argument("project")
    parser.add_argument("video", type=Path)
    parser.add_argument("--name", default="reference")
    args = parser.parse_args(argv)
    try:
        out = analyze(load_project(args.project).root, args.video, args.name)
    except (ReferenceError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Analysis: {out}\nReview all inferred claims before use.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
