"""Story 4：script.json 的格式、驗證與淺白語言檢查。

script.json 是唯一由人編輯的檔案。facts.yaml 列出旁白可以引用的數字與出處。
`python -m vc validate <project>` 會跑全部檢查，任何錯誤以非零代碼結束。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from vc.project import load_project

# 2026-11-12 使用者核可的 7 段順序：先看到問題（人工 vs ACT、內建工具 vs ACT），再講原理，最後講操作與規模
SECTIONS = ("vs_intro", "why_midsurface", "vs_result", "theory", "sop", "full_chassis", "roi_time")
VARIANTS = ("internal", "public")
# public 版只能用重新畫的動畫與 Manim，不能用真實錄影或 PPT 截圖
PUBLIC_ALLOWED_KINDS = {"anim", "manim"}

Box = tuple[float, float, float, float]


class Voice(BaseModel):
    engine: Literal["edge", "kokoro"] = "edge"
    name: str = "en-US-AndrewNeural"
    rate: str = "+0%"


class Meta(BaseModel):
    title: str
    fps: int = Field(default=30, gt=0)
    size: tuple[int, int] = (1920, 1080)
    voice: Voice = Voice()
    target_duration_s: tuple[float, float] = (130.0, 170.0)
    words_per_minute: tuple[float, float] = (130.0, 165.0)
    max_sentence_words: int = 20
    max_fk_grade: float = 8.0
    # 段落順序；沒設定時用完整版的 7 段。精簡版等其他剪法各自定義
    sections: tuple[str, ...] | None = None
    # 開啟後，每段旁白與畫面上的數字都只能來自這一段引用的 facts（精簡版用；完整版不開，行為不變）
    strict_facts: bool = False

    @model_validator(mode="after")
    def _validate_meta(self):
        if self.fps <= 0:
            raise ValueError(f"fps must be greater than 0, got {self.fps}")
        if self.size[0] <= 0 or self.size[1] <= 0:
            raise ValueError(f"size dimensions must be positive, got {self.size}")
        return self


class Clip(BaseModel):
    """錄影的一段。source 為原始秒數；crop 為原始像素 [x, y, w, h]。"""
    recording: str = "rec01"
    source: tuple[float, float]
    crop: Box | None = None
    label: str | None = None
    camera: str | None = None
    # 這段畫面從旁白的哪個字開始出現；沒設定的 clip 跟前一段共用時間窗
    start_at_word: str | None = None

    @model_validator(mode="after")
    def _order(self):
        if self.source[1] <= self.source[0]:
            raise ValueError(f"source 結束時間必須大於開始時間：{self.source}")
        return self


class Callout(BaseModel):
    at_word: str
    box: Box
    text: str
    clip: int = 0


class Visual(BaseModel):
    kind: Literal["anim", "recording", "manim"]
    template: str
    data: dict = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)  # 相對於 work/ 的 PPT 圖片
    clips: list[Clip] = Field(default_factory=list)
    callouts: list[Callout] = Field(default_factory=list)

    @model_validator(mode="after")
    def _recording_needs_clips(self):
        if self.kind == "recording" and not self.clips:
            raise ValueError("kind=recording 至少要有一段 clips")
        return self


class Scene(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    section: str               # 必須在 meta.sections（或預設 SECTIONS）之內，由 check() 驗證
    narration: str
    budget_s: tuple[float, float]
    facts: list[str] = Field(default_factory=list)
    visual: Visual

    @model_validator(mode="after")
    def _all_variants(self):
        return self

    @property
    def visuals(self) -> dict[str, Visual]:
        return {"main": self.visual}


class GlossaryEntry(BaseModel):
    term: str
    defined_in: str
    plain: str


class Script(BaseModel):
    schema_version: Literal[2] = 2
    meta: Meta
    lexicon: dict[str, str] = Field(default_factory=dict)  # TTS 前的文字替換
    glossary: list[GlossaryEntry] = Field(default_factory=list)
    banned_terms: list[str] = Field(default_factory=list)
    scenes: list[Scene]


class Fact(BaseModel):
    value: str
    spoken: list[str]          # 旁白中允許出現的數字寫法
    sources: list[str]
    confirmed: bool
    scope: str | None = None   # 這個數字的適用範圍（例如「只限這台測試模型」）
    shown: list[str] = Field(default_factory=list)  # 畫面（字卡、標註）允許出現的數字寫法


# ---------- 文字工具 ----------

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|(?<=[。！？])\s*")
_NUM = re.compile(r"\d+(?:\.\d+)?")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def words(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9][A-Za-z0-9.'\-]*", text)


def numbers(text: str) -> list[str]:
    return _NUM.findall(text)


def contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", text, re.IGNORECASE) is not None


def _screen_texts(v: Visual) -> list[str]:
    """收集這個版面畫面上會出現的文字：clip 的 label、callout 的 text，以及 data 裡所有字串
    （遞迴走 dict/list，略過 key scene_class 與 cues，這兩個不是畫面上的文字）。"""
    texts = [c.label for c in v.clips if c.label] + [c.text for c in v.callouts]

    def walk(node) -> None:
        if isinstance(node, dict):
            for k, val in node.items():
                if k in ("scene_class", "cues"):
                    continue
                walk(val)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            texts.append(node)

    walk(v.data)
    return texts


# ---------- 檢查 ----------

def check(script: Script, facts: dict[str, Fact], rec_durations: dict[str, float] | None = None,
          work_dir: Path | None = None) -> tuple[list[str], dict]:
    """回傳（錯誤清單, 統計）。錯誤訊息一律以場景 id 開頭，方便定位。"""
    errors: list[str] = []
    m = script.meta

    ids = [s.id for s in script.scenes]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"{dup}: 場景 id 重複")

    order = [s.section for s in script.scenes]
    dedup = [s for i, s in enumerate(order) if i == 0 or order[i - 1] != s]
    sections = list(m.sections or SECTIONS)
    if dedup != sections:
        errors.append(f"script: 段落順序必須是 {', '.join(sections)}，目前是 {', '.join(dedup)}")

    allowed_numbers = {n for f in facts.values() if f.confirmed for n in f.spoken}
    for s in script.scenes:
        for fid in s.facts:
            if fid not in facts:
                errors.append(f"{s.id}: 引用了不存在的事實 {fid}")
            elif not facts[fid].confirmed:
                errors.append(f"{s.id}: 事實 {fid} 尚未確認")
        for n in numbers(s.narration):
            if n not in allowed_numbers:
                errors.append(f"{s.id}: 旁白中的數字 {n} 不在已確認的事實表")

        if m.strict_facts:
            own_facts = [facts[fid] for fid in s.facts if fid in facts and facts[fid].confirmed]
            own_spoken = {n for f in own_facts for n in f.spoken}
            own_all = {n for f in own_facts for n in f.spoken + f.shown}
            for fid in s.facts:
                if fid in facts and facts[fid].confirmed and not facts[fid].scope:
                    errors.append(f"{s.id}: 事實 {fid} 沒有寫適用範圍 scope")
            for n in numbers(s.narration):
                if n not in own_spoken:
                    errors.append(f"{s.id}: 旁白中的數字 {n} 不屬於本段引用的事實（{', '.join(s.facts) or '無'}）")
            for variant, v in s.visuals.items():
                for text in _screen_texts(v):
                    for n in numbers(text):
                        if n not in own_all:
                            errors.append(f"{s.id}/{variant}: 畫面文字「{text}」的數字 {n} 不屬於本段引用的事實")

        for sent in sentences(s.narration):
            if len(words(sent)) > m.max_sentence_words:
                errors.append(f"{s.id}: 句子超過 {m.max_sentence_words} 字（{len(words(sent))} 字）：{sent}")
        for term in script.banned_terms:
            if contains_term(s.narration, term):
                errors.append(f"{s.id}: 旁白出現內部術語「{term}」")

        for variant, v in s.visuals.items():
            for img in v.images:
                if work_dir is not None and not (work_dir / img).is_file():
                    errors.append(f"{s.id}/{variant}: 找不到圖片 {img}")
            for k, c in enumerate(v.clips):
                if rec_durations is not None:
                    dur = rec_durations.get(c.recording)
                    if dur is None:
                        errors.append(f"{s.id}/{variant}: 找不到錄影 {c.recording}")
                    elif c.source[1] > dur + 1e-6:
                        errors.append(f"{s.id}/{variant}: clip {k} 結束於 {c.source[1]}s，超過錄影長度 {dur:.2f}s")
            for k, c in enumerate(v.clips):
                if c.start_at_word and not contains_term(s.narration, c.start_at_word):
                    errors.append(f"{s.id}/{variant}: clip {k} 的 start_at_word「{c.start_at_word}」不在旁白中")
            for c in v.callouts:
                if not contains_term(s.narration, c.at_word):
                    errors.append(f"{s.id}/{variant}: 標註的 at_word「{c.at_word}」不在旁白中")
                if c.clip >= max(len(v.clips), 1):
                    errors.append(f"{s.id}/{variant}: 標註指向不存在的 clip {c.clip}")

    # 術語必須在指定場景第一次出現，之前的場景不能先用
    for g in script.glossary:
        first = next((s.id for s in script.scenes if contains_term(s.narration, g.term)), None)
        if first is None:
            errors.append(f"glossary: 術語「{g.term}」沒有出現在旁白")
        elif first != g.defined_in:
            errors.append(f"glossary: 術語「{g.term}」在 {first} 就先出現，應該先在 {g.defined_in} 解釋")

    stats = stats_for(script)
    lo, hi = m.target_duration_s
    if not lo <= stats["estimated_s"] <= hi:
        errors.append(f"script: 以每分鐘 150 字估計長度 {stats['estimated_s']:.1f}s，超出 {lo}–{hi}s")
    if stats["fk_grade"] > m.max_fk_grade:
        errors.append(f"script: 易讀等級 {stats['fk_grade']:.1f} 超過 {m.max_fk_grade}")
    for s in script.scenes:
        est = stats["scenes"][s.id]["estimated_s"]
        if not s.budget_s[0] - 1.0 <= est <= s.budget_s[1] + 1.0:
            errors.append(f"{s.id}: 估計 {est:.1f}s，超出時間預算 {s.budget_s[0]}–{s.budget_s[1]}s（容許 ±1s）")
    return errors, stats


ESTIMATE_WPM = 150.0


def stats_for(script: Script) -> dict:
    import textstat

    full = " ".join(s.narration for s in script.scenes)
    per = {s.id: {"words": len(words(s.narration)),
                  "estimated_s": round(len(words(s.narration)) / ESTIMATE_WPM * 60, 1)} for s in script.scenes}
    total_words = len(words(full))
    return {
        "words": total_words,
        "estimated_s": round(total_words / ESTIMATE_WPM * 60, 1),
        "fk_grade": round(textstat.flesch_kincaid_grade(full), 1),
        "longest_sentence": max((len(words(x)) for x in sentences(full)), default=0),
        "scenes": per,
    }


# ---------- 載入與 CLI ----------

def load_script(path: Path) -> Script:
    # utf-8-sig：Windows 編輯器（含 PowerShell 5 的 Set-Content）常在檔頭加 BOM
    return Script.model_validate_json(path.read_text(encoding="utf-8-sig"))


def load_facts(path: Path) -> dict[str, Fact]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {k: Fact.model_validate(v) for k, v in raw.items()}


def recording_durations(work_dir: Path) -> dict[str, float] | None:
    f = work_dir / "recordings.json"
    if not f.is_file():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    return {r["id"]: r["probe"]["duration"] for r in data["recordings"]}


def main(argv: list[str]) -> int:
    if not argv:
        print("用法：python -m vc validate <project>")
        return 2
    proj = load_project(argv[0])
    try:
        script = load_script(proj.root / "script.json")
    except ValidationError as exc:
        print(f"script.json 格式錯誤：\n{exc}")
        return 1
    facts = load_facts(proj.root / "facts.yaml")
    rec = recording_durations(proj.work)
    if rec is None:
        print("警告：找不到 work/recordings.json，略過錄影區間檢查（先執行 vc ingest-rec）")
    errors, st = check(script, facts, rec, proj.work)

    print(f"{'場景':<6}{'段落':<9}{'字數':>4}{'估計秒數':>9}  預算")
    for s in script.scenes:
        sc = st["scenes"][s.id]
        print(f"{s.id:<6}{s.section:<9}{sc['words']:>4}{sc['estimated_s']:>9.1f}  {s.budget_s[0]:g}–{s.budget_s[1]:g}")
    print(f"總字數 {st['words']}，估計 {st['estimated_s']}s，易讀等級 {st['fk_grade']}，最長句 {st['longest_sentence']} 字")
    if errors:
        print(f"\n錯誤 {len(errors)} 項：")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\n全部檢查通過。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
