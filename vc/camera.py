"""驗證鏡頭時序，產出可重現的二維運鏡參數。"""
from __future__ import annotations

import copy
import re

from vc.style_config import _number

MOTIONS = ("static_lock", "dolly_in", "dolly_out", "pan_horizontal", "pan_vertical", "focus_target")


def validate_camera_plan(plan: dict) -> dict:
    if not isinstance(plan, dict) or not isinstance(plan.get("shots"), list):
        raise ValueError("Set camera shots to an array.")
    result = copy.deepcopy(plan)
    previous = {}
    ids = set()
    for index, shot in enumerate(result["shots"]):
        if not isinstance(shot, dict):
            raise ValueError(f"Set shot {index} to an object.")
        ref = shot.get("scene_ref")
        if not isinstance(ref, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", ref):
            raise ValueError("Set scene_ref to a scene identifier.")
        sid = shot.get("shot_id", f"shot_{index}")
        if not isinstance(sid, str) or sid in ids:
            raise ValueError("Use a unique string for each shot_id.")
        ids.add(sid)
        start = _number(shot.get("start_time_s"), "start_time_s", 0, 86400)
        end = _number(shot.get("end_time_s"), "end_time_s", 0, 86400)
        if not 1.5 <= end - start <= 5.5:
            raise ValueError("Set each shot duration from 1.5 to 5.5 seconds.")
        if start < previous.get(ref, 0):
            raise ValueError("Order shots by scene time. Do not overlap shots.")
        previous[ref] = end
        motion = shot.get("camera_motion")
        if not isinstance(motion, dict) or motion.get("type") not in MOTIONS:
            raise ValueError("Use a supported camera_motion type.")
        defaults = (("start_scale", 1.08 if motion["type"] == "dolly_out" else 1.0),
                    ("end_scale", 1.08 if motion["type"] == "dolly_in" else 1.0), ("target_scale", 1.2))
        for key, default in defaults:
            motion[key] = _number(motion.get(key, default), key, 1, 1.5)
        if motion["type"] == "dolly_in" and motion["end_scale"] < motion["start_scale"]:
            raise ValueError("Increase scale for dolly_in motion.")
        if motion["type"] == "dolly_out" and motion["end_scale"] > motion["start_scale"]:
            raise ValueError("Decrease scale for dolly_out motion.")
        focal = motion.setdefault("focal_point", [0.5, 0.5])
        if not isinstance(focal, list) or len(focal) != 2:
            raise ValueError("Set focal_point to two normalized coordinates.")
        for value in focal:
            _number(value, "focal_point", 0, 1)
        motion["distance_px"] = _number(motion.get("distance_px", 40), "distance_px", -120, 120)
        if motion["type"] == "focus_target":
            if not isinstance(motion.get("target_selector"), str) or not re.fullmatch(r"#[A-Za-z][A-Za-z0-9_-]*", motion["target_selector"]):
                raise ValueError("Set target_selector to one element ID.")
        if "spring" in motion:
            spring = motion["spring"]
            if not isinstance(spring, dict):
                raise ValueError("Set spring to an object.")
            for key, default, low, high in (("mass", 1, 0.1, 10), ("stiffness", 100, 1, 1000), ("damping", 20, 1, 200)):
                spring[key] = _number(spring.get(key, default), key, low, high)
    return result


def scene_camera(plan: dict | None, scene_id: str, duration: float) -> list[dict]:
    _number(duration, "scene duration", 0.01, 86400)
    plan = validate_camera_plan(plan or {"shots": []})
    shots = [shot for shot in plan["shots"] if shot["scene_ref"] == scene_id]
    if shots:
        if any(shot["end_time_s"] > duration + 0.0001 for shot in shots):
            raise ValueError(f"Keep camera shots inside scene {scene_id}.")
        return shots
    mode = plan.get("mode", "fixed")
    if mode not in ("fixed", "dynamic", "cinematic"):
        raise ValueError("Set camera mode to fixed, dynamic, or cinematic.")
    if mode == "fixed":
        return []
    # 自動模式只改變視覺運鏡，不裁切或拉長旁白時間軸。
    return [{"scene_ref": scene_id, "start_time_s": 0, "end_time_s": duration,
             "camera_motion": {"type": "dolly_in" if mode == "cinematic" else "pan_horizontal",
                               "start_scale": 1.0, "end_scale": 1.06, "distance_px": 28,
                               "focal_point": [0.5, 0.5]}}]
