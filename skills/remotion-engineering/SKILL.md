---
name: remotion-engineering
description: Integrate frame-based video compositions with the Video Creator Remotion compositor. Use when editing React compositions, checking clip timing, adding captions, or combining generated scenes and narration.
compatibility: Python 3.11 and the Video Creator repository
---

# Remotion Engineering

1. Read `references/compositor_contract.md`.
2. Read the current `work/timeline.json` contract.
3. Use frame values from the narration timeline.
4. Keep local asset paths relative to the rendering workspace.
5. Separate internal and public variants.
6. Derive visual state from the current frame.
7. Keep random values seeded when they affect frames.
8. Run project validation before rendering.
9. Check the final frame count and audio duration.
10. Report actual render results and failures.

## Outputs

Return the changed composition, props contract, and validation evidence.
HyperFrames produces animated clips.
Remotion composes those clips, audio, subtitles, and recordings.
Do not apply a second camera transform to an already transformed clip.
Read the upstream official skills only when this local contract lacks required detail.
