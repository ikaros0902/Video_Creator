"""專案設定：06_projects/<name>/project.yaml 指向原始素材，產物寫到 work/ 和 output/。"""
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
    def work(self) -> Path:
        return self.root / "work"

    @property
    def output(self) -> Path:
        return self.root / "output"


def resolve_project_dir(arg: str) -> Path:
    """接受專案名稱（06_projects/<name> 或 projects/<name>）或任意資料夾路徑。"""
    p = Path(arg)
    if not p.is_absolute() and not p.exists():
        cand = ROOT / "06_projects" / arg
        legacy = ROOT / "projects" / arg
        p = cand if cand.exists() or not legacy.exists() else legacy
    return p.resolve()


def load_project(arg: str) -> Project:
    root = resolve_project_dir(arg)
    cfg_path = root / "project.yaml"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"找不到 {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    def _resolve(rel: str) -> Path:
        path = (root / rel).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"project.yaml 指向的檔案不存在：{path}")
        return path

    pptx = _resolve(cfg["pptx"]) if cfg.get("pptx") else None
    recs = tuple(_resolve(r) for r in cfg.get("recordings", []))
    return Project(root=root, name=cfg.get("name", root.name), pptx=pptx, recordings=recs)
