---
name: script-copywriter
description: Write and check video narration, hooks, onscreen copy, Chinese spacing, and concrete claims. Use when editing script.json, selecting SCQA or PAS structure, shortening sentences, or removing vague promotional text.
compatibility: Python 3.11 and the Video Creator repository
---

# Script Copywriter

1. Read the audience, purpose, and verified facts.
2. Select one structure from `references/hook_and_fab_formulas.md`.
3. Write one claim per sentence.
4. Keep every technical number linked to a confirmed fact.
5. Read `references/spoken_cadence_guide.md` before writing narration.
6. Preserve the existing `script.json` schema.
7. Keep each `at_word` string inside its narration.
8. Run `python skills/script-copywriter/scripts/lint_copywriting.py PROJECT/script.json`.
9. Run `python skills/script-copywriter/scripts/scan_ai_slop.py PROJECT/script.json`.
10. Run `python -m vc validate PROJECT` before voice synthesis.

Read `references/chinese_typesetting_rules.md` for mixed Chinese and English text.
Read `references/banned_buzzwords_dict.md` when the scan reports a vague phrase.
Use the structural outlines in `assets/templates/` when starting a draft.
These outlines are planning aids, not executable pipeline scripts.

## Outputs

Return the edited script, fact references, and validation findings.
Report uncertain claims as unresolved.
Keep source quotes unchanged when editing would change their meaning.
