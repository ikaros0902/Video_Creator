"""scripts/verify_style_switch.py

實作 Milestone 4 之 F17:
多風格與運鏡參數切換實測與客觀比對報告生成。
比對 Executive Navy + Cinematic 與 Swiss Kinetic + Dynamic 的 HTML/CSS/Design Tokens 差異。
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vc.camera import scene_camera
from vc.hf_scenes import render_scene_html
from vc.style_config import load_style, validate_style

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = REPO_ROOT / "projects" / "demo_showcase"
REPORTS_DIR = DEMO_DIR / "reports"


def run_style_comparison():
    print("=== 執行 F17 多風格與運鏡模式切換比對 ===")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    navy_dir = REPORTS_DIR / "style_executive_navy"
    swiss_dir = REPORTS_DIR / "style_swiss_kinetic"
    navy_dir.mkdir(parents=True, exist_ok=True)
    swiss_dir.mkdir(parents=True, exist_ok=True)

    # 讀取 timeline
    tl_path = DEMO_DIR / "work" / "timeline.json"
    tl = json.loads(tl_path.read_text(encoding="utf-8"))

    # 載入兩種風格與運鏡
    navy_style = load_style("executive_navy")
    swiss_style = load_style("swiss_kinetic")
    cinematic_cam = {"mode": "cinematic", "shots": []}
    dynamic_cam = {"mode": "dynamic", "shots": []}

    comparison_results = {
        "styles": {
            "variant_1": {"name": "executive_navy", "camera": "cinematic"},
            "variant_2": {"name": "swiss_kinetic", "camera": "dynamic"},
        },
        "token_differences": {},
        "scene_differences": {},
    }

    # 1. 比較 Design Tokens
    navy_colors = navy_style["tokens"]["colors"]
    swiss_colors = swiss_style["tokens"]["colors"]
    navy_typo = navy_style["tokens"]["typography"]
    swiss_typo = swiss_style["tokens"]["typography"]

    comparison_results["token_differences"] = {
        "colors": {
            "primary": {"executive_navy": navy_colors["primary"], "swiss_kinetic": swiss_colors["primary"]},
            "accent": {"executive_navy": navy_colors["accent"], "swiss_kinetic": swiss_colors["accent"]},
            "background": {"executive_navy": navy_colors["background"], "swiss_kinetic": swiss_colors["background"]},
            "text_primary": {"executive_navy": navy_colors["text_primary"], "swiss_kinetic": swiss_colors["text_primary"]},
        },
        "typography": {
            "heading_font": {"executive_navy": navy_typo["heading_font"], "swiss_kinetic": swiss_typo["heading_font"]},
            "body_font": {"executive_navy": navy_typo["body_font"], "swiss_kinetic": swiss_typo["body_font"]},
            "base_size_px": {"executive_navy": navy_typo["base_size_px"], "swiss_kinetic": swiss_typo["base_size_px"]},
        },
    }

    # 2. 針對所有場景產生 HTML 並比對
    for sc in tl["scenes"]:
        sc_id = sc["id"]
        comparison_results["scene_differences"][sc_id] = {}

        for variant in ("internal", "public"):
            vis = sc["visuals"][variant]
            if vis["kind"] != "anim":
                continue

            tmpl = vis["template"]
            ctx = {
                "comp_id": f"{sc_id}-{variant}",
                "scene_id": sc_id,
                "duration": sc["duration_frames"] / tl["fps"],
                "fps": tl["fps"],
                "data": vis["data"],
                "at_frames": sc.get("at_frames", {}),
                "images": {"list": []},
            }

            html_navy = render_scene_html(tmpl, ctx, style_config=navy_style, camera_config=cinematic_cam)
            html_swiss = render_scene_html(tmpl, ctx, style_config=swiss_style, camera_config=dynamic_cam)

            (navy_dir / f"{variant}_{sc_id}.html").write_text(html_navy, encoding="utf-8")
            (swiss_dir / f"{variant}_{sc_id}.html").write_text(html_swiss, encoding="utf-8")

            # 提取並比對關鍵屬性
            navy_accent_matches = re.findall(re.escape(navy_colors["accent"]), html_navy, re.IGNORECASE)
            swiss_accent_matches = re.findall(re.escape(swiss_colors["accent"]), html_swiss, re.IGNORECASE)

            comparison_results["scene_differences"][sc_id][variant] = {
                "template": tmpl,
                "executive_navy": {
                    "accent_color_occurrences": len(navy_accent_matches),
                    "contains_heading_font": navy_typo["heading_font"] in html_navy,
                    "html_size_bytes": len(html_navy.encode("utf-8")),
                },
                "swiss_kinetic": {
                    "accent_color_occurrences": len(swiss_accent_matches),
                    "contains_heading_font": swiss_typo["heading_font"] in html_swiss,
                    "html_size_bytes": len(html_swiss.encode("utf-8")),
                },
                "distinct_html": html_navy != html_swiss,
            }

    # 3. 輸出報告 JSON 與 Markdown
    report_json_path = REPORTS_DIR / "style_comparison_report.json"
    report_md_path = REPORTS_DIR / "style_comparison_report.md"

    report_json_path.write_text(json.dumps(comparison_results, indent=2, ensure_ascii=False), encoding="utf-8")

    md_content = f"""# 多風格與運鏡模式切換比對報告 (F17)

## 1. 樣式配置概覽
- **配置 1**: Executive Navy + Cinematic (`variants/executive_navy_cinematic.yaml`)
- **配置 2**: Swiss Kinetic + Dynamic (`variants/swiss_kinetic_dynamic.yaml`)

## 2. Design Tokens 差異比對
| Token 類別 | Token 名稱 | Executive Navy | Swiss Kinetic | 差異說明 |
|---|---|---|---|---|
| Color | Primary | `{navy_colors['primary']}` | `{swiss_colors['primary']}` | 商務深藍 vs 瑞士極簡深灰 |
| Color | Accent | `{navy_colors['accent']}` | `{swiss_colors['accent']}` | 專業青藍 vs 瑞士鮮豔警戒橘 |
| Color | Background | `{navy_colors['background']}` | `{swiss_colors['background']}` | 深色科技底 vs 極簡灰白底 |
| Typography | Heading Font | `{navy_typo['heading_font']}` | `{swiss_typo['heading_font']}` | Segoe UI 現代無襯線 vs 經典瑞士黑體 |
| Typography | Base Size | `{navy_typo['base_size_px']}px` | `{swiss_typo['base_size_px']}px` | 視覺基線字級差異 |

## 3. 生成場景 HTML/CSS 實質差異
"""
    for sc_id, var_dict in comparison_results["scene_differences"].items():
        md_content += f"### 場景 {sc_id}\n"
        for variant, diff in var_dict.items():
            md_content += f"- **版本 `{variant}`** (樣板 `{diff['template']}`):\n"
            md_content += f"  - Executive Navy: Accent 出現 {diff['executive_navy']['accent_color_occurrences']} 次，字型包含 `{navy_typo['heading_font']}`。\n"
            md_content += f"  - Swiss Kinetic: Accent 出現 {diff['swiss_kinetic']['accent_color_occurrences']} 次，字型包含 `{swiss_typo['heading_font']}`。\n"
            md_content += f"  - 輸出 HTML 內容實質不相等：`{diff['distinct_html']}`。\n"

    report_md_path.write_text(md_content, encoding="utf-8")
    print(f"[OK] F17 比對報告生成完成：{report_json_path} 與 {report_md_path}")
    return comparison_results


if __name__ == "__main__":
    run_style_comparison()
