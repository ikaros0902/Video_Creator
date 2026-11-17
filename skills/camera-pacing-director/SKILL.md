---
name: camera-pacing-director
description: Plan deterministic camera movement, focal zooms, shot pacing, and measured beat alignment. Use when creating camera_plan.json, choosing fixed, dynamic, or cinematic motion, or checking shot duration.
compatibility: Python 3.11 and the Video Creator repository
---

# Camera Pacing Director

1. Read the aligned narration and scene durations.
2. Read `references/camera_grammar_matrix.md` before selecting motion.
3. Select a camera preset from `assets/camera_presets/`.
4. Set `scene_ref` to an existing animated scene.
5. Set shot times relative to that scene.
6. Keep explicit shots from 1.5 to 5.5 seconds.
7. Run `python skills/camera-pacing-director/scripts/audit_shot_pacing.py PROJECT/camera_plan.json`.
8. Set `camera_plan: camera_plan.json` in `project.yaml`.
9. Generate a preview and inspect the focal target.
10. Check that labels and subtitles stay visible during motion.

Read `references/recordly_motion_physics.md` for spring parameters.
Read `references/chaojifeng_rhythm_curve.md` before aligning cuts with music.
Run `scripts/beat_sync_aligner.py PLAN BEATS` only with measured scene-relative beats.
The command writes a proposed plan to standard output.
Review its timing before saving it.

## Outputs

Return the camera plan, timing audit, and preview path.
Explain any automatic mode separately from explicit shots.
Automatic modes preserve full narration duration and do not enforce editorial shot limits.
Orbit and whip transitions need another renderer.
Do not label them as supported HyperFrames operators.
