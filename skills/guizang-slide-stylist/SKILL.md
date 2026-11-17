---
name: guizang-slide-stylist
description: Adapt editorial and Swiss slide layout principles to video explanation cards. Use for magazine-style slides, restrained typography, asymmetric grids, or layouts inspired by the Guizang presentation skill.
compatibility: Python 3.11 and the Video Creator repository
---

# Editorial Slide Stylist

1. Read `references/editorial_layout.md`.
2. Identify the one claim that the slide supports.
3. Select a layout from `assets/layouts.json`.
4. Place the headline before secondary labels.
5. Align text and images to the same grid.
6. Use the selected Video Creator theme tokens.
7. Keep source screenshots inside the internal variant.
8. Reserve the bottom 160 pixels for subtitles.
9. Inspect the slide at its final output size.

## Outputs

Return the layout choice, content map, and asset references.
Use `style-director` for token validation.
Use `script-copywriter` for narration checks.
This local adaptation does not reproduce the upstream locked slide templates.
