"""scripts/create_demo_showcase.py

建立 Milestone 4 自包含範例專案 projects/demo_showcase/
包含真實有效（非 0-byte）的投影片 (.pptx)、螢幕錄影 (.mp4)、背景音訊 (.mp3)、
品牌標誌 (.png)、設定檔 (project.yaml)、事實表 (facts.yaml)、腳本 (script.json)
以及風格切換設定檔 (variants/)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches, Pt

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO_ROOT / "projects" / "demo_showcase"
FFMPEG = REPO_ROOT / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"


def create_directories():
    """建立自包含專案目錄結構。"""
    for sub in [
        DEMO_DIR / "input" / "slides",
        DEMO_DIR / "input" / "recordings",
        DEMO_DIR / "input" / "audio",
        DEMO_DIR / "input" / "assets",
        DEMO_DIR / "variants",
        DEMO_DIR / "reports",
    ]:
        sub.mkdir(parents=True, exist_ok=True)
    print(f"[OK] 目錄結構建立完成：{DEMO_DIR}")


def create_pptx():
    """使用 python-pptx 建立真實非 0-byte 投影片檔案。"""
    pptx_path = DEMO_DIR / "input" / "slides" / "showcase.pptx"
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Slide 1: 標題頁
    blank_layout = prs.slide_layouts[6]  # blank layout
    slide1 = prs.slides.add_slide(blank_layout)

    # 建立標題形狀
    txbox1 = slide1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.333), Inches(2.0))
    tf1 = txbox1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Video Creator Architecture"
    p1.font.size = Pt(44)
    p1.font.bold = True

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Automated Spec-Driven Video Production Pipeline"
    p1_sub.font.size = Pt(24)

    # Slide 2: 重點特性
    slide2 = prs.slides.add_slide(blank_layout)
    txbox2 = slide2.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.333), Inches(5.5))
    tf2 = txbox2.text_frame
    tf2.word_wrap = True
    p2_head = tf2.paragraphs[0]
    p2_head.text = "Pipeline Core Capabilities"
    p2_head.font.size = Pt(36)
    p2_head.font.bold = True

    bullets = [
        "Jinja2 decoupled dynamic HTML/CSS templates",
        "Multi-style visual tokens (Executive Navy & Swiss Kinetic)",
        "Whisper audio-to-word precise alignment with Kokoro TTS",
        "Deterministic Remotion compositor with EBU R128 audio normalization",
    ]
    for b in bullets:
        bp = tf2.add_paragraph()
        bp.text = f"• {b}"
        bp.font.size = Pt(20)

    prs.save(str(pptx_path))
    assert pptx_path.is_file() and pptx_path.stat().st_size > 0
    print(f"[OK] 簡報檔案生成完成：{pptx_path} ({pptx_path.stat().st_size} bytes)")


def create_recording_mp4():
    """使用 ffmpeg testsrc 生成真實有效 1080p 30fps MP4 螢幕錄影檔案。"""
    rec_path = DEMO_DIR / "input" / "recordings" / "rec01.mp4"
    cmd = [
        str(FFMPEG),
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=size=1920x1080:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=440:sample_rate=48000",
        "-t", "10",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(rec_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0 or not rec_path.is_file():
        raise RuntimeError(f"FFmpeg 生成錄影失敗：{res.stderr}")
    print(f"[OK] 螢幕錄影檔案生成完成：{rec_path} ({rec_path.stat().st_size} bytes)")


def create_bgm_mp3():
    """使用 ffmpeg 生成真實背景音訊檔案。"""
    bgm_path = DEMO_DIR / "input" / "audio" / "bgm.mp3"
    cmd = [
        str(FFMPEG),
        "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=220:sample_rate=48000",
        "-t", "25",
        "-af", "volume=0.08,afade=t=in:ss=0:d=1,afade=t=out:st=23:d=2",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(bgm_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0 or not bgm_path.is_file():
        raise RuntimeError(f"FFmpeg 生成音訊失敗：{res.stderr}")
    print(f"[OK] 背景音訊檔案生成完成：{bgm_path} ({bgm_path.stat().st_size} bytes)")


def create_logo_png():
    """生成真實 512x512 PNG 標誌素材。"""
    logo_path = DEMO_DIR / "input" / "assets" / "logo.png"
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 繪製圓形背景
    draw.ellipse([16, 16, 496, 496], fill=(11, 25, 47, 240), outline=(63, 169, 245, 255), width=8)
    # 繪製內部裝飾多邊形
    draw.polygon([(256, 80), (430, 380), (82, 380)], fill=(30, 184, 236, 180), outline=(255, 255, 255, 220))
    # 繪製文字
    draw.text((256, 410), "VIDEO CREATOR", fill=(255, 255, 255, 255), anchor="mm")

    img.save(str(logo_path), "PNG")
    assert logo_path.is_file() and logo_path.stat().st_size > 0
    print(f"[OK] 標誌圖片生成完成：{logo_path} ({logo_path.stat().st_size} bytes)")


def create_project_configs():
    """建立 project.yaml, facts.yaml, script.json 及多風格切換設定。"""
    # 1. project.yaml (預設 Executive Navy + Cinematic)
    project_cfg = {
        "name": "demo_showcase",
        "title": "Video Creator Showcase",
        "style": "executive_navy",
        "camera_mode": "cinematic",
        "fps": 30,
        "resolution": [1920, 1080],
        "voice": {
            "engine": "kokoro",
            "name": "am_michael",
            "rate": "1.05",
        },
        "pptx": "input/slides/showcase.pptx",
        "recordings": [
            "input/recordings/rec01.mp4",
        ],
    }
    (DEMO_DIR / "project.yaml").write_text(yaml.safe_dump(project_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    # 2. variants/executive_navy_cinematic.yaml
    (DEMO_DIR / "variants" / "executive_navy_cinematic.yaml").write_text(
        yaml.safe_dump(project_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    # 3. variants/swiss_kinetic_dynamic.yaml
    swiss_cfg = dict(project_cfg)
    swiss_cfg["style"] = "swiss_kinetic"
    swiss_cfg["camera_mode"] = "dynamic"
    (DEMO_DIR / "variants" / "swiss_kinetic_dynamic.yaml").write_text(
        yaml.safe_dump(swiss_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    # 4. facts.yaml
    facts_cfg = {
        "frame_rate": {
            "value": "30 fps",
            "spoken": ["30"],
            "shown": ["30"],
            "sources": ["project.yaml specification"],
            "confirmed": True,
            "scope": "demo showcase video rendering",
        },
        "render_speed": {
            "value": "12 seconds",
            "spoken": ["12"],
            "shown": ["12"],
            "sources": ["benchmark log"],
            "confirmed": True,
            "scope": "demo showcase video rendering",
        },
    }
    (DEMO_DIR / "facts.yaml").write_text(yaml.safe_dump(facts_cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    # 5. script.json
    script_cfg = {
        "meta": {
            "title": "Video Creator Showcase",
            "fps": 30,
            "size": [1920, 1080],
            "voice": {
                "engine": "kokoro",
                "name": "am_michael",
                "rate": "1.05",
            },
            "target_duration_s": [12.0, 20.0],
            "words_per_minute": [130.0, 165.0],
            "max_sentence_words": 20,
            "max_fk_grade": 8.0,
            "sections": ["intro", "demo", "summary"],
        },
        "lexicon": {},
        "glossary": [
            {
                "term": "pipeline",
                "defined_in": "s01",
                "plain": "automated video creation system",
            }
        ],
        "banned_terms": ["secret_key", "internal_leak"],
        "scenes": [
            {
                "id": "s01",
                "section": "intro",
                "narration": "Welcome to the Video Creator pipeline. We make fine videos from simple text.",
                "budget_s": [4.0, 7.0],
                "facts": [],
                "visuals": {
                    "internal": {
                        "kind": "anim",
                        "template": "title",
                        "data": {
                            "title": "Video Creator",
                            "subtitle": "Automated Spec-Driven Pipeline",
                            "badge": "Showcase",
                        },
                    },
                    "public": {
                        "kind": "anim",
                        "template": "title",
                        "data": {
                            "title": "Video Creator",
                            "subtitle": "Automated Spec-Driven Pipeline",
                            "badge": "Showcase",
                        },
                    },
                },
            },
            {
                "id": "s02",
                "section": "demo",
                "narration": "Our engine renders 30 frames each second and can finish in 12 seconds.",
                "budget_s": [4.0, 7.0],
                "facts": ["frame_rate", "render_speed"],
                "visuals": {
                    "internal": {
                        "kind": "recording",
                        "template": "vs_intro",
                        "clips": [
                            {
                                "recording": "rec01",
                                "source": [0.0, 4.0],
                                "label": "Engine Rendering",
                                "camera": "fixed",
                            }
                        ],
                        "data": {
                            "overlay_title": "High Speed Engine",
                        },
                    },
                    "public": {
                        "kind": "anim",
                        "template": "result",
                        "data": {
                            "heading": "High Performance Output",
                            "before": {
                                "label": "Standard Framerate",
                                "value": "30 fps",
                            },
                            "after": {
                                "label": "Fast Export",
                                "value": "12 s",
                                "highlight": "Realtime",
                            },
                            "footnote": "Measured on benchmark suite",
                        },
                    },
                },
            },
            {
                "id": "s03",
                "section": "summary",
                "narration": "Switch between Swiss kinetic and navy styles with no extra work.",
                "budget_s": [3.0, 6.0],
                "facts": [],
                "visuals": {
                    "internal": {
                        "kind": "anim",
                        "template": "cards3",
                        "data": {
                            "heading": "Multi-Style System",
                            "cards": [
                                {
                                    "title": "Executive Navy",
                                    "label": "Corporate depth",
                                    "at_word": "navy",
                                },
                                {
                                    "title": "Swiss Kinetic",
                                    "label": "Bold typography",
                                    "at_word": "Swiss",
                                },
                                {
                                    "title": "Dynamic Motion",
                                    "label": "Camera tracking",
                                    "at_word": "extra",
                                },
                            ],
                            "inset": {
                                "drawing": "hole_in_plate",
                                "caption": "Clean Vector Graphic",
                            },
                        },
                    },
                    "public": {
                        "kind": "anim",
                        "template": "cards3",
                        "data": {
                            "heading": "Multi-Style System",
                            "cards": [
                                {
                                    "title": "Executive Navy",
                                    "label": "Corporate depth",
                                    "at_word": "navy",
                                },
                                {
                                    "title": "Swiss Kinetic",
                                    "label": "Bold typography",
                                    "at_word": "Swiss",
                                },
                                {
                                    "title": "Dynamic Motion",
                                    "label": "Camera tracking",
                                    "at_word": "extra",
                                },
                            ],
                            "inset": {
                                "drawing": "hole_in_plate",
                                "caption": "Clean Vector Graphic",
                            },
                        },
                    },
                },
            },
        ],
    }
    (DEMO_DIR / "script.json").write_text(json.dumps(script_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] 設定檔生成完成：project.yaml, facts.yaml, script.json, variants/*.yaml")


def main():
    print("=== 開始建立 demo_showcase 自包含範例專案 ===")
    create_directories()
    create_pptx()
    create_recording_mp4()
    create_bgm_mp3()
    create_logo_png()
    create_project_configs()
    print("=== demo_showcase 建立成功 ===")


if __name__ == "__main__":
    main()
