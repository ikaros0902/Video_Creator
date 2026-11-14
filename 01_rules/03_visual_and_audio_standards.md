# Visual, Typography & Audio Standards (`01_rules/03_visual_and_audio_standards.md`)

All pipeline exports adhere to deterministic broadcast and accessibility thresholds verified by `vc` modules.

## 1. Video & Safe Frame Targets

- **Resolution**: `1920x1080` (`16:9`), `30 fps`, progressive H.264 (`yuv420p`, `movflags +faststart`).
- **Safe Margins**: Keep critical titles, callouts, and cards inside `120 px` horizontal and `80 px` vertical inset.
- **Subtitle Reserve**: Keep bottom `160 px` clear of cards and charts; Remotion renders burned captions there.
- **Color Contrast**: Maintain `>= 4.5:1` luminance contrast against `#0B1220` dark navy background (see `04_styles/01_executive_navy/`).

## 2. Audio & Loudness Targets (`vc/voice.py` & `vc/render.py`)

- **Intermediate Narration**: `48000 Hz`, `mono`, 16-bit PCM WAV, trimmed silence boundaries (`trim_silence`).
- **Speaking Rate Target**: `130–165 WPM`; estimation baseline `150 WPM`.
- **Master Final Mix (EBU R128)**:
  - Integrated loudness: `-16.0 LUFS` (`tolerance <= 1.0 LU`)
  - True Peak ceiling: `-1.5 dBTP` (`hard fail > -0.8 dBTP`)
  - BGM auto-ducking: `-20 dB` below voice during narration; `-14 dB` during scene pauses.

## 3. Captions & Alignment (`vc/align.py`)

- **Whisper Model**: `small.en` word-level alignment with compound word merging (`merge_compounds`).
- **Subtitle Constraints**: `<= 42 characters` per line; break cleanly at sentence boundaries; never orphan trailing `"a"`, `"the"`, `"of"`, or `"and"`.

## 4. Quality Gates in Code

- `vc manim`: fails if actual animation lag > `MAX_LATE_FRAMES` or total frames != planned frames.
- `vc fit`: fails if clipped segment deviates from exact `duration_frames` or speed exceeds `MAX_SPEED = 2.5`.
- `vc render`: verifies final MP4 frame count matches `timeline.json` `total_frames` and EBU R128 loudness passes.
