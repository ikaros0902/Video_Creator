---
name: style-director
description: Manage visual themes, design tokens, readable colors, and typography for Video Creator. Use when selecting a video style, changing brand colors, editing style.json, or creating a theme preset.
compatibility: Python 3.11 and the Video Creator repository
---

# Style Director

1. Read the project brief and the selected audience.
2. Read `references/token_schema.md` before you change tokens.
3. Select a preset from `assets/presets/`.
4. Copy the preset into the project before customization.
5. Run `python skills/style-director/scripts/validate_tokens.py PROJECT/style.json` from the repository root.
6. Set `style: style.json` in `project.yaml` after validation succeeds.
7. Generate the same scene with both themes.
8. Check text, safe margins, and meaning in both outputs.

Keep technical values tied to `facts.yaml`.
Use one accent role for emphasis.
Keep state colors consistent across scenes.
Preserve narration timestamps when changing style.

## Outputs

Return the style path, validation result, and selected preset.
Return a short explanation for each changed token.
Read `references/visual_balance_guide.md` when content needs a new layout.

## Limits

Tokens currently control HyperFrames scenes.
Remotion composes the rendered clips without applying these tokens again.
Use separate Manim configuration for Manim scenes.
