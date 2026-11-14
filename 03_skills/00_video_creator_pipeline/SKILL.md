---
name: video-creator-pipeline
description: Master skill for running and extending the deterministic Video_Creator pipeline (`python -m vc`). Use when creating video projects, editing `script.json`, adding templates, or validating outputs.
---

# Video Creator Pipeline Skill (`03_skills/00_video_creator_pipeline/SKILL.md`)

Follow **ASD-STE100** rules in `01_rules/01_asd_ste100_en.md` for all prompts and scripts.

## Mandatory Execution Order

1. Run `.venv\Scripts\python.exe -m vc doctor` to confirm tool and GPU status.
2. Collect source truth into `06_projects/<name>/facts.yaml`. Mark `confirmed: true` only for verified data.
3. Write `06_projects/<name>/script.json`. Keep sentences at 20 words or fewer.
4. Run `.venv\Scripts\python.exe -m vc validate <name>`. Stop until exit code equals `0`.
5. Run `.venv\Scripts\python.exe -m vc voice <name>`. Listen to the preview WAV for pronunciation errors.
6. Run `.venv\Scripts\python.exe -m vc align <name>` and `vc plan <name>`.
7. Render tracks (`manim`, `hf`, `fit`) and compose final MP4 via `vc render <name> --variant all`.
8. Run `.venv\Scripts\python.exe -m pytest -q` after any pipeline or template change.

## Hard Constraints

- Never bypass `vc validate`. Fix `facts.yaml`, `glossary`, or `banned_terms` violations instead.
- Never place real screen recordings or proprietary images into `visuals.public`.
- Keep all `at_word` trigger strings present inside the exact `narration` string of that scene.
- Enable GPU by default (`VC_GPU=auto`); add `--no-gpu` only to debug driver faults or verify pixel determinism.
