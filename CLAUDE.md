# CLAUDE.md — Claude Code Entrypoint

Use the exact instructions in [`AGENTS.md`](AGENTS.md).

## Quick Command Reference

- Verify environment & GPU: `.venv\Scripts\python.exe -m vc doctor`
- Run offline BDD suite: `.venv\Scripts\python.exe -m pytest -q`
- Validate sample scripts: `.venv\Scripts\python.exe -m vc validate _sample`
- Inspect GPU acceleration settings: see [`00_docs/03_gpu_acceleration.md`](00_docs/03_gpu_acceleration.md)
- Choose a style token preset: browse [`04_styles/`](04_styles/)
- Review active skills: browse `.agents/skills/` (symlink/mirror of [`03_skills/`](03_skills/))

## Hard Boundaries

1. Do not delete local files under `Videos/` or custom folders under `06_projects/`.
2. Do not bypass `vc validate` checks (`strict_facts`, glossary order, FK grade, sentence length).
3. Do not invent numeric metrics. Every number in narration or visuals must trace to `facts.yaml`.
4. Use `--no-gpu` or `VC_GPU=off` only when hardware acceleration causes driver instability.
