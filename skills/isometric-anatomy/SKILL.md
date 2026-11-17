---
name: isometric-anatomy
description: Plan isometric technical illustrations, layered assemblies, and exploded explanatory views for video. Use when depicting components, showing an assembly relationship, or preparing public diagrams without proprietary screenshots.
compatibility: Python 3.11 and the Video Creator repository
---

# Isometric Anatomy

1. Read `references/projection_and_layers.md`.
2. Identify the components and their verified relationships.
3. Select one projection for the full scene.
4. Separate functional layers by depth and label.
5. Use a consistent light direction.
6. Keep leader lines clear of labels and important boundaries.
7. Tie each reveal to a narration anchor.
8. Keep source geometry and exported illustrations separate.
9. Inspect overlaps and hidden components before rendering.

## Outputs

Return a component map, layer order, and reveal schedule.
Label conceptual diagrams as illustrations when dimensions are not verified.
Use Manim for geometry animation.
Use SVG in HyperFrames for a static diagram with timed reveals.
Read the existing `03_skills/02_anatomy_isometric/SKILL.md` for the repository rendering workflow.
