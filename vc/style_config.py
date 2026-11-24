"""載入與驗證可移植的視覺設計參數。"""
from __future__ import annotations

import copy
import json
import math
import re
from pathlib import Path

import yaml

from vc.tools import ROOT

STYLES = ROOT / "styles"
PRESETS = ("executive_navy", "swiss_kinetic", "blueprint", "cyberpunk_neon")
COLOR_KEYS = ("primary", "secondary", "accent", "background", "surface", "text_primary", "text_secondary", "positive", "negative", "border")


def _number(value, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Set {name} to a finite number from {low} to {high}.")
    return value


def contrast_ratio(first: str, second: str) -> float:
    """依 sRGB 相對亮度計算兩個六碼色值的對比度。"""
    def luminance(color):
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError("Use six-digit hexadecimal colors.")
        values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(a * b for a, b in zip(values, (0.2126, 0.7152, 0.0722)))
    a, b = sorted((luminance(first), luminance(second)))
    return (b + 0.05) / (a + 0.05)


def validate_style(config: dict) -> dict:
    if not isinstance(config, dict) or not isinstance(config.get("tokens"), dict):
        raise ValueError("Set style.tokens to an object.")  # noqa: TRY004 - 維持輸入驗證介面
    result = copy.deepcopy(config)
    tokens = result["tokens"]
    colors = tokens.get("colors")
    if not isinstance(colors, dict):
        raise ValueError("Set tokens.colors to an object.")  # noqa: TRY004 - 維持輸入驗證介面
    for key in COLOR_KEYS:
        value = colors.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError(f"Set tokens.colors.{key} to a six-digit hexadecimal color.")
    for foreground in ("text_primary", "text_secondary", "accent", "positive", "negative"):
        for background in ("background", "surface"):
            if contrast_ratio(colors[foreground], colors[background]) < 4.5:
                raise ValueError(f"Increase {foreground}/{background} contrast to at least 4.5:1.")
    typography = tokens.get("typography")
    surface = tokens.get("surface")
    spacing = tokens.get("spacing")
    if not all(isinstance(value, dict) for value in (typography, surface, spacing)):
        raise ValueError("Set typography, surface, and spacing tokens to objects.")
    for key in ("heading_font", "body_font"):
        value = typography.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9 ,\-]+", value) or len(value) > 160:
            raise ValueError(f"Use plain font family names in {key}.")
    _number(typography.get("base_size_px"), "base_size_px", 18, 60)
    _number(typography.get("scale_ratio"), "scale_ratio", 1, 2)
    for key, low, high in (("line_height", 1, 2), ("letter_spacing_px", -2, 8), ("content_gap_px", 8, 120)):
        if key in typography:
            _number(typography[key], key, low, high)
    _number(surface.get("card_corner_radius"), "card_corner_radius", 0, 64)
    _number(surface.get("border_width"), "border_width", 0, 8)
    _number(spacing.get("safe_margin_px"), "safe_margin_px", 60, 160)
    if surface.get("shadow") not in ("none", "soft"):
        raise ValueError("Set surface.shadow to none or soft.")
    return result


def load_style(identifier: str = "executive_navy", project_root: Path | None = None) -> dict:
    if not isinstance(identifier, str) or not identifier:
        raise ValueError("Set style to a preset name or a local JSON path.")
    if identifier in PRESETS:
        path = STYLES / identifier / "style.json"
    elif project_root is not None and identifier.endswith(".json"):
        root = project_root.resolve()
        path = (root / identifier).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Keep custom style files inside the project folder.")
    else:
        raise ValueError(f"Unknown style: {identifier}. Use a preset or a project JSON path.")
    return validate_style(json.loads(path.read_text(encoding="utf-8")))


def project_visual_settings(project_root: Path) -> tuple[dict, dict]:
    path = project_root / "project.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else {}
    if cfg is None:
        cfg = {}
    if not isinstance(cfg, dict):
        raise ValueError("Set project.yaml to an object.")  # noqa: TRY004 - 維持輸入驗證介面
    style = load_style(cfg.get("style", "executive_navy"), project_root)
    mode = cfg.get("camera_mode", "fixed")
    if mode not in ("fixed", "dynamic", "cinematic"):
        raise ValueError("Set camera_mode to fixed, dynamic, or cinematic.")
    camera = {"mode": mode, "shots": []}
    plan_name = cfg.get("camera_plan")
    if plan_name is not None:
        if not isinstance(plan_name, str):
            raise ValueError("Set camera_plan to a project JSON path.")
        path = (project_root / plan_name).resolve()
        if not path.is_relative_to(project_root.resolve()):
            raise ValueError("Keep camera plans inside the project folder.")
        from vc.camera import validate_camera_plan
        camera = validate_camera_plan(json.loads(path.read_text(encoding="utf-8")))
        camera["mode"] = mode
    return style, camera
