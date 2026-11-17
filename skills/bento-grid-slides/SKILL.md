---
name: bento-grid-slides
description: Organize related video or presentation facts into a small modular card grid. Use when arranging metrics, feature summaries, or a product overview as bento cards with clear reading order.
compatibility: Python 3.11 and the Video Creator repository
---

# Bento Grid Slides

1. Read `references/grid_contract.md`.
2. Group facts by the decision they support.
3. Select a grid from `assets/grids.json`.
4. Give the main fact the largest cell.
5. Keep card headings short.
6. Use one unit and one scale per metric group.
7. Reveal cards in narration order.
8. Check that every source value matches `facts.yaml`.
9. Inspect long labels at 1920 by 1080 pixels.

## Outputs

Return a grid map with cell coordinates and content.
Return the reading order and `at_word` anchors.
Use the `cards3` template for three narrated facts.
Use `steps4` for a four-step process.
Create a new template when the layout needs different geometry.
