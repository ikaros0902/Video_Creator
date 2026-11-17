"""專案設定：06_projects/<name>/project.yaml 或 projects/<name>/project.yaml 指向原始素材，產物寫到 work/ 和 output/。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from vc.tools import ROOT


@dataclass(frozen=True)
class Project:
    root: Path
    name: str
    pptx: Path | None
    recordings: tuple[Path, ...]

    @property
    def input(self) -> Path:
        return self.root / "input"

    @property
    def dir(self) -> Path:
        return self.root

    @property
    def work(self) -> Path:
        return self.root / "work"

    @property
    def output(self) -> Path:
        return self.root / "output"


def resolve_project_dir(arg: str) -> Path:
    """接受專案名稱（projects/<name> 或 06_projects/<name>）或任意資料夾路徑。"""
    p = Path(arg)
    if p.is_absolute() and p.is_dir():
        return p.resolve()
    if p.is_dir():
        return p.resolve()
    if (ROOT / arg).is_dir():
        return (ROOT / arg).resolve()

    # 提取純專案名稱（處理 'projects/name' 或 '06_projects/name' 或 'name'）
    pure_name = Path(arg).name
    cand = ROOT / "projects" / pure_name
    legacy = ROOT / "06_projects" / pure_name

    if cand.is_dir():
        return cand.resolve()
    if legacy.is_dir():
        return legacy.resolve()

    return cand.resolve()


def load_project(arg: str) -> Project:
    root = resolve_project_dir(arg)
    cfg_path = root / "project.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"找不到 {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    def _resolve(rel: str) -> Path:
        path = (root / rel).resolve()
        if path.is_file():
            return path

        filename = Path(rel).name
        # 產生檔名候選（含空格與底線互換、拼寫相容）
        name_candidates = [filename]
        if " " in filename:
            name_candidates.append(filename.replace(" ", "_"))
        if "_" in filename:
            name_candidates.append(filename.replace("_", " "))
        if "Midsuface" in filename:
            name_candidates.append(filename.replace("Midsuface", "Midsurface"))
        if "Midsurface" in filename:
            name_candidates.append(filename.replace("Midsurface", "Midsuface"))

        # 自愈候選：優先在專案 input/ 及其子目錄查找
        input_dirs = [
            root / "input",
            root / "input" / "slides",
            root / "input" / "recordings",
            root / "input" / "audio",
            root / "input" / "assets",
        ]
        # 若 root 本身在 06_projects，也嘗試相應 projects/ 的 input 目錄
        if "06_projects" in root.parts:
            alt_root = ROOT / "projects" / root.name
            input_dirs.extend([
                alt_root / "input",
                alt_root / "input" / "slides",
                alt_root / "input" / "recordings",
                alt_root / "input" / "audio",
                alt_root / "input" / "assets",
            ])

        for idir in input_dirs:
            for fname in name_candidates:
                cand = idir / fname
                if cand.is_file():
                    return cand.resolve()

        # 反向 fallback：若 rel 為 input/... 但本地尚未搬遷，或檔案在歷史 Videos/ 下
        video_dirs = [
            ROOT / "Videos" / "Midsuface",
            ROOT / "Videos" / "midsurface",
            ROOT / "Videos" / "Templates",
            ROOT / "archive" / "Videos" / "Midsuface",
            ROOT / "assets" / "templates",
            ROOT / "assets" / "templates" / "audio",
            ROOT / "assets" / "templates" / "backgrounds",
            ROOT / "assets" / "brand",
        ]
        for vdir in video_dirs:
            for fname in name_candidates:
                cand = vdir / fname
                if cand.is_file():
                    return cand.resolve()

        raise FileNotFoundError(f"project.yaml 指向的檔案不存在：{path}")

    pptx = _resolve(cfg["pptx"]) if cfg.get("pptx") else None
    recs = tuple(_resolve(r) for r in cfg.get("recordings", []))
    return Project(root=root, name=cfg.get("name", root.name), pptx=pptx, recordings=recs)
