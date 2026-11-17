"""回報空泛用語與替換方向；保留使用者原文。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from lint_copywriting import text_fields

BANNED = {
    "robust": "State the measured tolerance or failure rate.",
    "seamless": "Name the steps that the tool removes.",
    "game-changing": "Name the observed change.",
    "revolutionary": "Describe the mechanism.",
    "leverage": "Use a direct action verb.",
    "delve": "State the topic directly.",
    "值得注意的是": "直接陳述觀察結果。",
    "賦能": "說明誰能完成哪項工作。",
    "顛覆性": "描述可查證的改變。",
    "無縫": "列出實際省下的步驟。",
    "全方位": "列出明確涵蓋範圍。",
    "極致": "改為可查證的規格。",
}


def scan_text(text):
    matches = []
    for term, suggestion in BANNED.items():
        pattern = rf"\b{re.escape(term)}\b" if term.isascii() else re.escape(term)
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append({"term": term, "offset": match.start(), "suggestion": suggestion})
    return matches


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find vague claims in narration.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8")
        fields = list(text_fields(json.loads(text))) if args.path.suffix == ".json" else [("$", text)]
        if not fields:
            raise ValueError("Add narration or a supported text field.")
        matches = [dict(path=path, **match) for path, text in fields for match in scan_text(text)]
    except (OSError, ValueError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 1
    print(json.dumps({"valid": not matches, "matches": matches}))
    return int(bool(matches))


if __name__ == "__main__":
    raise SystemExit(main())
