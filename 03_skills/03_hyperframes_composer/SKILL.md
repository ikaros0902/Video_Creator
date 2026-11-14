---
name: hyperframes-composer
description: Authoring and GPU-rendering deterministic HTML/GSAP scenes with `heygen-com/hyperframes`. Use when creating or debugging `kind: anim` templates in `vc/hf_scenes.py`.
---

# HyperFrames Composer Skill (`03_skills/03_hyperframes_composer/SKILL.md`)

Use this manual when editing `vc/hf_scenes.py` or building standalone HTML compositions rendered by HyperFrames (`v0.9.26`).

## Composition Contract

1. Mark the root stage container with `data-composition-id="<sid>-<variant>"` and `data-duration="<seconds>"` (`1920x1080`).
2. Create one paused GSAP timeline: `const tl = gsap.timeline({ paused: true });`.
3. Register that timeline globally before frame capture starts: `window.__timelines["<sid>-<variant>"] = tl;`.
4. Keep every visual element static at `t = 0` unless animated exclusively inside `tl`. Never use CSS `@keyframes` or unpaused transitions.
5. Place inline SVG, fonts, and copied `assets/` files inside the scene folder so headless Chromium loads zero external CDNs (prevents enterprise proxy timeouts).

## GPU Capture Flags & Disk Safety

- `vc/hf_scenes.py` runs `hyperframes render --gpu --browser-gpu` when `VC_GPU != off` and falls back to software capture cleanly on failure.
- Set `--frames-cache-dir <path_on_large_drive>` if the Windows `C:` drive has low free space during multi-minute batch captures.
- Clamp GSAP durations to positive numbers (`Math.max(..., 0.25)`) when narration cues occur close together.
