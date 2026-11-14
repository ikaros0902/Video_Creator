---
name: lemo-opuscar-director
description: Code-driven film directing and pacing grammar inspired by `lemomo-ai/lemo-opuscar`. Use when storyboarding scenes, setting camera transitions, choosing a `04_styles/` preset, or auditing shot pacing.
---

# Lemo-Opuscar Director Skill (`03_skills/01_lemo_opuscar_director/SKILL.md`)

This skill applies the code-first directing discipline of `lemomo-ai/lemo-opuscar` to automated technical videos.

## Director Checklist

1. **Select One Visual System Before Coding**: Load palette, typography, grain, and motion tokens from one folder under `04_styles/`. Never mix two unrelated visual themes in one video.
2. **Enforce Shot Rhythm**: Alternates high-density technical visuals (`manim` or `recording`) with clean typographic anchors (`cards3` or `result`). Hold critical numbers for at least `1.8 seconds`.
3. **Establish Motivated Camera Moves**: Use only three purposeful moves in `script.json` (`fixed`, `dolly_in`, `dolly_out`). Lock `dolly_in` origin onto the first callout box (`remotion/src/Main.tsx`).
4. **Drive Transitions From Spoken Beats**: Bind every visual reveal (`cues`, `cards`, `callouts`) to an exact `at_word` token so visuals hit the ear and eye simultaneously.
5. **Render Against Absolute Time**: Use GSAP paused timelines (`HyperFrames`) or explicit wait targets (`Manim` `self.wait_until(...)`) instead of `setTimeout` or `requestAnimationFrame`.
6. **Audit Boundary Frames**: Grab frames at `0.3s` after scene start, at the midpoint beat, and `0.3s` before scene end using `09_scripts/grab_frames.py`. Verify zero clipping and zero subtitle collisions.
