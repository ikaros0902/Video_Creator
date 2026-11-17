"""將鏡頭邊界吸附至已量測鼓點，失敗時保留原始時序。"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from vc.camera import validate_camera_plan
from vc.style_config import _number


def align(plan, beats, tolerance=0.12):
    result = validate_camera_plan(plan)
    _number(tolerance, "tolerance", 0, 0.5)
    if not isinstance(beats, list):
        raise ValueError("Set beats to an array of scene-relative seconds.")
    for beat in beats:
        _number(beat, "beat", 0, 86400)
    for index, shot in enumerate(result["shots"]):
        target = shot["end_time_s"]
        candidates = sorted((beat for beat in beats if abs(beat-target) <= tolerance), key=lambda beat: abs(beat-target))
        for beat in candidates:
            candidate = copy.deepcopy(result)
            candidate["shots"][index]["end_time_s"] = beat
            if index+1 < len(candidate["shots"]):
                following = candidate["shots"][index+1]
                if following["scene_ref"] == shot["scene_ref"] and following["start_time_s"] == target:
                    following["start_time_s"] = beat
            try:
                result = validate_camera_plan(candidate)
                break
            except ValueError:
                continue
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Align shot boundaries to measured beats.")
    parser.add_argument("plan", type=Path)
    parser.add_argument("beats", type=Path)
    args = parser.parse_args(argv)
    try:
        result = align(json.loads(args.plan.read_text(encoding="utf-8")), json.loads(args.beats.read_text(encoding="utf-8")))
    except (OSError, ValueError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
