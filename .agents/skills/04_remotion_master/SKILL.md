---
name: remotion-master
description: Master 1080p video composition, spring typography, and GPU-accelerated rendering with Remotion (`remotion/src/Main.tsx` and `vc/render.py`). Use when extending master overlays, camera transforms, or caption tracks.
---

# Remotion Master Compositor Skill (`03_skills/04_remotion_master/SKILL.md`)

Apply clean React/Remotion patterns aligned with `remotion-dev/skills` inside `remotion/src/`.

## Composition Rules

1. **Use Relative Public Assets**: Pass only work-relative paths (`hf/...`, `manim/...`, `fit/...`, `voice/...`) inside `props_<variant>.json`. Set `--public-dir=<work>`.
2. **Drive Motion With `spring()` and `interpolate()`**: Clamped strictly (`extrapolateRight: "clamp"`). Prefer damped spring physics (`damping: 16-20`, `stiffness: 170`) for callout boxes and timer badges.
3. **Avoid Hardcoded Proprietary Labels**: Keep UI component color/badge logic (`isAct`, overlay headers) parameter-driven from JSON props (`Main.tsx`).
4. **Reserve Subtitle Clearance**: Keep all floating cards, progress bars, and screen crops above `y = 920 px` (`160 px` bottom reserve).
5. **Render With ANGLE GPU & Resilient Retry**: `vc/render.py` passes `--gl=angle --hardware-acceleration=if-possible` on attempt 1 and falls back to CPU on attempt 2 if Chromium reports a transient GPU or `ERR_NETWORK_CHANGED` failure.
6. **Follow Render With Loudness Gate**: Always pipe raw Remotion output through `normalize_loudness()` (`-16.0 LUFS`, `-1.5 dBTP` true peak) and verify exact `total_frames`.
