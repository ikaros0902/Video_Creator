"""產生深色背景可用的高解析度透明品牌 PNG（internal 版片尾使用）。

若指定的範本資料夾內有自訂圖片（primary_logo.png / secondary_logo.png），
會自動去除淺色或深色背景並轉成白字透明 PNG；
若無自訂圖片，則自動以向量幾何樣式繪製通用品牌標誌，確保開源環境零相依即可渲染。
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from vc.tools import ROOT

TEMPLATES = ROOT / "assets" / "templates" if (ROOT / "assets" / "templates").exists() else ROOT / "Videos" / "Templates"


def _crop(rgba: np.ndarray, pad: int = 6) -> np.ndarray:
    coords = cv2.boundingRect((rgba[:, :, 3] > 10).astype(np.uint8))
    x, y, w, h = coords
    if w == 0 or h == 0:
        return rgba
    y0, x0 = max(y - pad, 0), max(x - pad, 0)
    return rgba[y0:y + h + pad, x0:x + w + pad]


def light_bg_to_white(src: Path) -> np.ndarray:
    """將白底深色文字轉成深色背景適用的白字透明 PNG（保留亮青色強調）。"""
    bgr = cv2.imread(str(src), cv2.IMREAD_COLOR).astype(np.float32)
    ink_min = 20.0
    a = np.clip((255.0 - bgr.min(axis=2)) / (255.0 - ink_min), 0, 1)
    a[a < 0.15] = 0
    safe = np.maximum(a, 1e-3)[..., None]
    ink = (bgr - (1 - safe) * 255.0) / safe
    accent = (ink[:, :, 1] > 120) & (ink[:, :, 0] > 150)
    out = np.where(accent[..., None], np.clip(ink, 0, 255), 255.0)
    rgba = np.dstack([out, a * 255.0]).astype(np.uint8)
    return _crop(rgba)


def dark_ink_to_white(src: Path) -> np.ndarray:
    """將已去背 PNG 的深色筆畫轉成白色（保留彩色幾何圖示）。"""
    rgba = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    if rgba.ndim == 2:
        rgba = cv2.cvtColor(rgba, cv2.COLOR_GRAY2BGRA)
    elif rgba.shape[2] == 3:
        rgba = np.dstack([rgba, np.full(rgba.shape[:2], 255, dtype=np.uint8)])
    dark = rgba[:, :, :3].max(axis=2) < 110
    rgba[dark, :3] = 255
    return _crop(rgba)


def _draw_geometric_badge(label: str, accent_bgr: tuple[int, int, int]) -> np.ndarray:
    """繪製高解析度透明底幾何品牌識別圖（供未提供自訂 logo 時使用）。"""
    w, h = 460, 120
    canvas = np.zeros((h, w, 4), dtype=np.uint8)
    # 左側幾何六角盾形徽章
    pts = np.array([[56, 20], [88, 38], [88, 78], [56, 96], [24, 78], [24, 38]], dtype=np.int32)
    cv2.polylines(canvas, [pts], True, (*accent_bgr, 255), 5, lineType=cv2.LINE_AA)
    cv2.circle(canvas, (56, 58), 11, (*accent_bgr, 255), -1, lineType=cv2.LINE_AA)
    # 右側白色無襯線文字
    cv2.putText(canvas, label, (112, 74), cv2.FONT_HERSHEY_SIMPLEX, 1.55, (255, 255, 255, 255), 4, cv2.LINE_AA)
    return _crop(canvas, pad=8)


def make_logos(out_dir: Path, templates_dir: Path | None = None) -> dict[str, Path]:
    """產出 primary_white.png 與 secondary_white.png。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    tdir = templates_dir or TEMPLATES
    files = {
        "primary": out_dir / "primary_white.png",
        "secondary": out_dir / "secondary_white.png",
    }
    custom_primary = tdir / "primary_logo.png"
    custom_secondary = tdir / "secondary_logo.png"

    if custom_primary.is_file():
        img1 = cv2.imread(str(custom_primary), cv2.IMREAD_UNCHANGED)
        if img1 is not None and img1.ndim == 3 and img1.shape[2] == 4:
            cv2.imwrite(str(files["primary"]), dark_ink_to_white(custom_primary))
        else:
            cv2.imwrite(str(files["primary"]), light_bg_to_white(custom_primary))
    else:
        cv2.imwrite(str(files["primary"]), _draw_geometric_badge("STUDIO", (236, 184, 30)))

    if custom_secondary.is_file():
        img2 = cv2.imread(str(custom_secondary), cv2.IMREAD_UNCHANGED)
        if img2 is not None and img2.ndim == 3 and img2.shape[2] == 4:
            cv2.imwrite(str(files["secondary"]), dark_ink_to_white(custom_secondary))
        else:
            cv2.imwrite(str(files["secondary"]), light_bg_to_white(custom_secondary))
    else:
        cv2.imwrite(str(files["secondary"]), _draw_geometric_badge("ENGINE", (65, 184, 245)))

    return files
