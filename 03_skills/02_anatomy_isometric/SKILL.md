---
name: anatomy-isometric
description: Technical isometric SVG and mechanical diagram discipline inspired by `wheresryan22/anatomy`. Use when building CAD explainers, cutaway shells, or isometric diagrams in HyperFrames (`vc/hf_scenes.py`).
---

# Isometric Technical Illustration Skill (`03_skills/02_anatomy_isometric/SKILL.md`)

Apply the **Truth-First Geometric Modeling** standard from `wheresryan22/anatomy`.

## Core Workflow

1. **Solve 3D Coordinates Before Drawing SVG**: Compute true 3D `(x, y, z)` vertices and project onto isometric screen space (`cos 30°`, `sin 30°`) in helper functions. Never eyeball skewed trapezoids.
2. **Use Four-Tone Value Hierarchy**: Assign distinct luminance values by surface normal:
   - Top face: `100%` highlight tone (e.g. `#8FB3E8`)
   - Left face: `80%` midtone (e.g. `#5F84BD`)
   - Right face: `65%` shadow tone (e.g. `#4D6FA5`)
   - Edges & section cuts: sharp stroke highlight (`#3FA9F5` / `#3FE08A`)
3. **Sort Faces Back-To-Front (Painter's Order)**: Compute centroid depth (`x + y + z`) and sort polygons back-to-front before emitting `<polygon>` nodes.
4. **Separate Labels Into Exterior Gutter**: Place labels outside bounding boxes (example: right-side offset at `x >= 1490px` in `vc/hf_scenes.py` `tpl_concept`) so text never overlaps vector strokes.
5. **Cap WebGL/Canvas DPR During Render**: If a scene adds optional WebGL shaders or canvas overlays, clamp `Math.min(window.devicePixelRatio, 2)` and allocate offscreen targets at explicit `1920x1080` bounds.
6. **Inspect Close-Ups in Chromium**: Render sample HTML keyframes and verify seam joints, arrowhead clearances, and text contrast (`>= 4.5:1`) before committing templates.
