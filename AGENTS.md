# AGENTS.md — AI Coding Agent Instructions

This repository uses an automated video production pipeline written in Python, Manim, HyperFrames, and Remotion.

Use short, explicit English for agent instructions. Read [`rules/`](rules/00_core_rules.md) and the relevant [`skills/`](skills/) before you edit files.

The current pipeline produces one video. Each scene uses one `visual` object. Do not restore internal/public branches.

## Mandatory Pre-Flight Rules

1. Run `.venv\Scripts\python.exe -m vc doctor` after any environment change.
2. Run `.venv\Scripts\python.exe -m vc validate <project>` before you synthesize voice or render video.
3. Read [`rules/00_core_rules.md`](rules/00_core_rules.md) before you write a script or change pipeline code.
4. Read [`workflows/00_bmad_bdd_lifecycle.md`](workflows/00_bmad_bdd_lifecycle.md) before you create a new video project.
5. Never commit files under `Videos/` or private project folders under `projects/`. Only commit the `_sample` and `_sample_exec` blueprints.

## Repository Map

| Path | Owner | Purpose |
| :--- | :--- | :--- |
| `docs/` | Human | User guides, environment requirements, design tools, reference analysis |
| `rules/` | Agent & Human | Engineering, language, and audio/visual rules |
| `workflows/` | Agent & Human | Development lifecycle and video production steps |
| `skills/` | Agent | Domain skills and validation scripts |
| `styles/` | Agent & Human | Style tokens and Jinja2 animation templates |
| `docs/references/` | Agent & Human | External project analyses |
| `projects/` | Mixed | Video projects and sample script blueprints |
| `tests/features/` | BDD | Gherkin behavior specifications |
| `tests/` | Test Suite | Unit, BDD, and integration tests |
| `scripts/` | Utilities | Setup, smoke tests, and media inspection tools |
| `assets/` | Media | Shared template assets |
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
Report skipped and deselected tests separately. They do not prove that a feature passed.
Set `VC_PIPELINE_PROJECT` for prepared-project integration tests. Set `VC_SHOWCASE_PROJECT` for showcase tests.

## Controlled Language Split

- Apply the English writing rules in [`rules/01_asd_ste100_en.md`](rules/01_asd_ste100_en.md) to agent instructions and CLI text.
- Write human documentation in clear Traditional Chinese. Read [`rules/02_iso_24495_plain_language.md`](rules/02_iso_24495_plain_language.md).
- Write Python, JavaScript, TypeScript, and PowerShell comments in **Traditional Chinese**.
- Write `vc/manim_scenes.py` and embedded solver script comments in **ASCII English**.
