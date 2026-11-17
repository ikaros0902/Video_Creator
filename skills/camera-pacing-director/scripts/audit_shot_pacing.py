"""檢查鏡頭計畫或時間軸的停留時長。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from vc.camera import validate_camera_plan
from vc.style_config import _number


def audit(data):
    if not isinstance(data, dict):
        raise ValueError("Set the input to an object.")
    if "shots" in data:
        shots = validate_camera_plan(data)["shots"]
        if not shots:
            raise ValueError("Add at least one shot.")
        return len(shots)
    fps = _number(data.get("fps"), "fps", 1, 240)
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Add scenes or shots to the input.")
    for scene in scenes:
        duration = _number(scene.get("duration_frames"), "duration_frames", 1, 20736000) / fps
        if not 1.5 <= duration <= 5.5:
            raise ValueError(f"Split scene {scene.get('id', '?')} into shots from 1.5 to 5.5 seconds. Keep narration timing.")
    return len(scenes)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check shot timing from 1.5 to 5.5 seconds.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        count = audit(json.loads(args.path.read_text(encoding="utf-8")))
    except (OSError, ValueError, AttributeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 1
    print(json.dumps({"valid": True, "shots": count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
