# Core Engineering Rules (`01_rules/00_core_rules.md`)

All rules below apply to both AI agents and human operators.

## 1. Truth-First Fact Grounding

1. Record every technical number in `facts.yaml` before you write `script.json`.
2. Mark `confirmed: true` only after you verify the raw source file or log.
3. Turn on `meta.strict_facts: true` and assign `scope` to every fact for executive cuts.
4. Never invent metrics, frame timings, or benchmark results.

## 2. BMAD Before Code

1. Complete the Project Brief (`00_docs/04_project_brief_template.md`) before you write narration.
2. Specify the 7-section or 5-section arc before you slice screen recordings.
3. Update `07_features/*.feature` before you change pipeline behavior.

## 3. Frame-Accurate Synchronization

1. Let narration drive scene duration (`vc voice` -> `vc align` -> `vc plan`).
2. Never cut video clips manually to fixed guessed seconds.
3. Use `at_word` triggers in `script.json` so animations and callouts lock to spoken words.
4. Never slow a clip down to fill empty time; clamp slow clips cleanly or freeze the final frame.

## 4. Dual-Track Privacy Split

1. `internal` variant may include real screen recordings (`kind: recording`) and approved brand logos.
2. `public` variant must use only programmatic animation (`kind: anim` or `kind: manim`) and zero proprietary images.
3. Never commit `Videos/` or private project folders to GitHub.

## 5. GPU With Deterministic CPU Fallback

1. Use auto-detected GPU backends by default (`cuda`/`mps` for Torch, `nvenc`/`qsv`/`amf` for FFmpeg, ANGLE for Remotion).
2. Always keep `--no-gpu` and `VC_GPU=off` working so CI and CPU-only hosts remain reproducible.
