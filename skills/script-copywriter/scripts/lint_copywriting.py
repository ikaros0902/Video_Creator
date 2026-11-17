"""檢查旁白句長、中英間距與標點；不改寫原文。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

TEXT_KEYS = {"narration", "title", "subtitle", "heading", "label", "caption", "footnote", "outro_title", "onscreen_text", "result_line"}
HAN = r"\u3400-\u9fff"


def text_fields(value, path="$"):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TEXT_KEYS and isinstance(item, str):
                yield f"{path}.{key}", item
            elif isinstance(item, (dict, list)):
                yield from text_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from text_fields(item, f"{path}[{index}]")


def lint_text(text: str, max_words=20, max_han_chars=20) -> list[str]:
    errors = []
    if re.search(fr"[{HAN}][A-Za-z0-9]|[A-Za-z0-9][{HAN}]", text):
        errors.append("Add a space between Chinese and Latin letters or digits.")
    if re.search(fr"[{HAN}][,;:!?]|[,;:!?][{HAN}]", text):
        errors.append("Use fullwidth punctuation next to Chinese text.")
    if re.search(r"[\uff10-\uff19\uff21-\uff3a\uff41-\uff5a]", text):
        errors.append("Use halfwidth Latin letters and digits.")
    for sentence in re.split(r"[.!?。！？\n]+", text):
        words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", sentence)
        count = len(re.findall(fr"[{HAN}]", sentence))
        if len(words) > max_words:
            errors.append(f"Shorten the sentence to {max_words} English words.")
        if count > max_han_chars:
            errors.append(f"Shorten the sentence to {max_han_chars} Chinese characters.")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check narration length and Chinese typography.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--max-words", type=int, default=20)
    parser.add_argument("--max-han-chars", type=int, default=20)
    args = parser.parse_args(argv)
    if args.max_words < 1 or args.max_han_chars < 1:
        parser.error("Set sentence limits above zero.")
    try:
        text = args.path.read_text(encoding="utf-8")
        fields = list(text_fields(json.loads(text))) if args.path.suffix == ".json" else [("$", text)]
        if not fields:
            raise ValueError("Add narration or a supported text field.")
        issues = [{"path": path, "error": error} for path, text in fields
                  for error in lint_text(text, args.max_words, args.max_han_chars)]
    except (OSError, ValueError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 1
    print(json.dumps({"valid": not issues, "fields": len(fields), "issues": issues}))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
