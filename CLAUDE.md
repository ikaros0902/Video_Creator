# CLAUDE.md — Claude Code Entrypoint

Use the exact instructions in [`AGENTS.md`](AGENTS.md).

## Quick Command Reference

- Verify environment & GPU: `.venv\Scripts\python.exe -m vc doctor`
- Run the default test suite: `.venv\Scripts\python.exe -m pytest -q`
- Validate sample scripts: `.venv\Scripts\python.exe -m vc validate _sample`
- Inspect GPU settings: see [`docs/03_gpu_acceleration.md`](docs/03_gpu_acceleration.md)
- Choose style tokens: browse [`styles/`](styles/)
- Review project skills: browse [`skills/`](skills/)
- Find sample scripts: see [`projects/README.md`](projects/README.md)

## Hard Boundaries

1. Do not delete local files under `Videos/` or private folders under `projects/`.
2. Do not bypass `vc validate` checks (`strict_facts`, glossary order, FK grade, sentence length).
3. Do not invent numeric metrics. Every number in narration or visuals must trace to `facts.yaml`.
4. Keep `--no-gpu` and `VC_GPU=off` available for CPU hosts and diagnostics.
5. Use one `visual` per scene. Do not create internal/public output branches.
