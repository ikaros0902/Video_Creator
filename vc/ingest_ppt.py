"""Story 2：從 PPT 抽出每頁的文字、表格、圖片與備註，並用 PowerPoint 匯出整頁預覽圖。

輸出：
  work/slides.json
  work/slides/images/slideNN_picK.<ext>
  work/slides/previews/slide_NN.png（需要 PowerPoint）
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

from vc.project import load_project


def _iter_shapes(shapes):
    """展開群組，讓群組內的圖片與文字也被擷取。"""
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _iter_shapes(sh.shapes)
        else:
            yield sh


def _box(sh, slide_w: int, slide_h: int) -> list[float] | None:
    """位置與大小換成投影片比例（0–1），版型重排時用得到。"""
    if sh.left is None or sh.width is None:
        return None
    return [
        round(Emu(sh.left) / slide_w, 4),
        round(Emu(sh.top) / slide_h, 4),
        round(Emu(sh.width) / slide_w, 4),
        round(Emu(sh.height) / slide_h, 4),
    ]


def extract(pptx_path: Path, out_dir: Path) -> dict:
    prs = Presentation(str(pptx_path))
    sw, sh_ = prs.slide_width, prs.slide_height
    img_dir = out_dir / "slides" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    slides = []
    for idx, slide in enumerate(prs.slides, 1):
        title_shape = slide.shapes.title
        texts, tables, pictures = [], [], []
        pic_k = 0
        # 依畫面由上而下、由左而右排序，接近閱讀順序
        ordered = sorted(_iter_shapes(slide.shapes), key=lambda s: ((s.top or 0), (s.left or 0)))
        for shape in ordered:
            if getattr(shape, "has_table", False) and shape.has_table:
                rows = [[c.text.strip() for c in r.cells] for r in shape.table.rows]
                tables.append({"box": _box(shape, sw, sh_), "rows": rows})
                continue
            image = None
            try:
                image = shape.image  # 圖片與含圖片的版面配置區都有 image 屬性
            except (AttributeError, ValueError):
                pass
            if image is not None:
                pic_k += 1
                name = f"slide{idx:02d}_pic{pic_k}.{image.ext}"
                (img_dir / name).write_bytes(image.blob)
                w, h = image.size
                pictures.append({
                    "file": f"slides/images/{name}",
                    "px": [w, h],
                    "box": _box(shape, sw, sh_),
                    "sha1": hashlib.sha1(image.blob).hexdigest()[:12],
                })
                continue
            if shape.has_text_frame:
                paras = [
                    {"text": p.text.strip(), "level": p.level}
                    for p in shape.text_frame.paragraphs
                    if p.text.strip()
                ]
                if paras:
                    texts.append({
                        "name": shape.name,
                        "is_title": title_shape is not None and shape.shape_id == title_shape.shape_id,
                        "box": _box(shape, sw, sh_),
                        "paragraphs": paras,
                    })

        title = title_shape.text_frame.text.strip() if title_shape is not None and title_shape.has_text_frame else ""
        notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        slides.append({
            "index": idx,
            "layout": slide.slide_layout.name,
            "title": title,
            "texts": texts,
            "tables": tables,
            "pictures": pictures,
            "notes": notes,
            "preview": None,
        })

    return {
        "source": str(pptx_path),
        "slide_size_emu": [sw, sh_],
        "aspect": round(sw / sh_, 4),
        "slides": slides,
    }


# PowerShell 腳本：只有在 PowerPoint 原本沒開時才關閉它，避免關掉使用者正在編輯的簡報
_PS_EXPORT = r"""
$ErrorActionPreference = 'Stop'
$src = $args[0]; $dst = $args[1]; $w = [int]$args[2]; $h = [int]$args[3]
$wasRunning = [bool](Get-Process POWERPNT -ErrorAction SilentlyContinue)
$app = New-Object -ComObject PowerPoint.Application
try {
  $p = $app.Presentations.Open($src, -1, 0, 0)
  try {
    $n = $p.Slides.Count
    for ($i = 1; $i -le $n; $i++) {
      $f = Join-Path $dst ('slide_{0:D2}.png' -f $i)
      $p.Slides.Item($i).Export($f, 'PNG', $w, $h)
    }
    Write-Output "EXPORTED=$n"
  } finally { $p.Close() }
} finally {
  if (-not $wasRunning) { $app.Quit() }
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
"""


def export_previews(pptx_path: Path, out_dir: Path, width: int = 1920, height: int = 1080) -> int:
    prev_dir = out_dir / "slides" / "previews"
    prev_dir.mkdir(parents=True, exist_ok=True)
    for old in prev_dir.glob("slide_*.png"):
        old.unlink()
    script = prev_dir.parent / "_export.ps1"
    script.write_text(_PS_EXPORT, encoding="utf-8")
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
         str(pptx_path), str(prev_dir), str(width), str(height)],
        capture_output=True, check=False, text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    script.unlink(missing_ok=True)
    if res.returncode != 0:
        raise RuntimeError(f"PowerPoint 匯出失敗：{res.stderr.strip()[-400:]}")
    return len(list(prev_dir.glob("slide_*.png")))


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc ingest-ppt <project> [--no-preview]")
        return 2
    proj = load_project(argv[0])
    if proj.pptx is None:
        print("project.yaml 沒有設定 pptx", file=sys.stderr)
        return 1
    from vc.pipeline_safety import file_hash
    source_hash = file_hash(proj.pptx)
    proj.work.mkdir(parents=True, exist_ok=True)
    data = extract(proj.pptx, proj.work)
    previews_current = False

    if "--no-preview" not in argv:
        from vc.doctor import check_powerpoint
        if check_powerpoint().ok:
            n = export_previews(proj.pptx, proj.work)
            for s in data["slides"]:
                f = proj.work / "slides" / "previews" / f"slide_{s['index']:02d}.png"
                if f.is_file():
                    s["preview"] = f"slides/previews/{f.name}"
            previews_current = n == len(data["slides"]) and all("preview" in s for s in data["slides"])
            print(f"預覽圖：{n} 張")
        else:
            print("找不到 PowerPoint，略過預覽圖")

    if source_hash != file_hash(proj.pptx):
        print("簡報在匯入期間變更，請重新執行。", file=sys.stderr)
        return 1
    data["source_sha256"] = source_hash
    if previews_current:
        data["preview_source_sha256"] = source_hash
    out = proj.work / "slides.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    pics = sum(len(s["pictures"]) for s in data["slides"])
    print(f"{len(data['slides'])} 頁，{pics} 張圖片 -> {out}")
    for s in data["slides"]:
        print(f"  {s['index']:>2}  文字框 {len(s['texts']):>2}  表格 {len(s['tables'])}  圖片 {len(s['pictures'])}  {s['title'][:50]}")
    return 0
