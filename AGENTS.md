# AGENTS.md — AI Coding Agent Instructions

This repository uses an automated video production pipeline written in Python, Manim, HyperFrames, and Remotion.

All agent rules below follow **ASD-STE100** controlled English. Read [`01_rules/`](01_rules/00_core_rules.md) and [`03_skills/`](03_skills/00_video_creator_pipeline/SKILL.md) before you edit files.

## Mandatory Pre-Flight Rules

1. Run `.venv\Scripts\python.exe -m vc doctor` after any environment change.
2. Run `.venv\Scripts\python.exe -m vc validate <project>` before you synthesize voice or render video.
3. Read [`01_rules/00_core_rules.md`](01_rules/00_core_rules.md) before you write a script or change pipeline code.
4. Read [`02_workflows/00_bmad_bdd_lifecycle.md`](02_workflows/00_bmad_bdd_lifecycle.md) before you create a new video project.
5. Never commit files under `Videos/` or private project folders under `06_projects/`. Only commit `_sample` and `_sample_exec`.

## Repository Map

| Path | Owner | Purpose |
| :--- | :--- | :--- |
| `00_docs/` | Human | Quick start, architecture, requirements, GPU tuning, brief template |
| `01_rules/` | Agent & Human | Core constraints, ASD-STE100, ISO 24495-1, audio/visual targets |
| `02_workflows/` | Agent & Human | BMAD + BDD lifecycle, new-video SOP, agent roles |
| `03_skills/` | Agent | Modular domain skills (also mirrored at `.agents/skills/`) |
| `04_styles/` | Agent & Human | Reusable `STYLE.md` and `style.json` visual themes |
| `05_references/` | Agent & Human | Ecosystem analyses (`lemo-opuscar`, `anatomy`, `hyperframes`, `remotion`) |
| `06_projects/` | Mixed | Video projects (`_sample` and `_sample_exec` are public blueprints) |
| `07_features/` | BDD | Gherkin `.feature` specifications |
| `08_tests/` | Test Suite | `pytest-bdd` test runners |
| `09_scripts/` | Utilities | Environment setup, smoke test, frame grabber, loudness probe |
| `vc/` | Pipeline Core | CLI (`python -m vc`), validators, TTS, alignment, timeline, renderers |
| `remotion/` | Compositor | Master 1080p React/Remotion video composition |

## Mandatory Verification Gate

Run this command after any code, test, or sample project edit:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m vc validate _sample
.venv\Scripts\python.exe -m vc validate _sample_exec
```

Report the exact exit status and counts. Never claim a pass without running tests after the last edit.

## Controlled Language Split

- Write all agent rules, CLI errors, and tool prompts in **ASD-STE100** (see [`01_rules/01_asd_ste100_en.md`](01_rules/01_asd_ste100_en.md)).
- Write all human documentation in **ISO 24495-1** Traditional Chinese (see [`01_rules/02_iso_24495_plain_language.md`](01_rules/02_iso_24495_plain_language.md)).
- Write Python, JavaScript, TypeScript, and PowerShell comments in **Traditional Chinese**.
- Write `vc/manim_scenes.py` and embedded solver script comments in **ASCII English**.
