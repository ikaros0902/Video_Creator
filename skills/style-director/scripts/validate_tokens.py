"""驗證風格參數及文字對比度。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from vc.style_config import contrast_ratio, validate_style


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check style tokens and text contrast.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        style = validate_style(json.loads(args.path.read_text(encoding="utf-8")))
        colors = style["tokens"]["colors"]
        ratios = {f"{front}/{back}": round(contrast_ratio(colors[front], colors[back]), 3)
                  for front in ("text_primary", "text_secondary", "accent", "positive", "negative")
                  for back in ("background", "surface")}
    except (OSError, ValueError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 1
    print(json.dumps({"valid": True, "contrast": ratios}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
