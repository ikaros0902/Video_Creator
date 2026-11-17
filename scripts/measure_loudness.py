"""量測多個音檔的整合響度（LUFS）與 true peak，結果印出並寫入 work/loudness.json。

用法：.venv\\Scripts\\python.exe 09_scripts\\measure_loudness.py <輸出 json> <檔案> [<檔案> ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vc.media import probe  # noqa: E402
from vc.render import measure_loudness  # noqa: E402

out = {}
for f in sys.argv[2:]:
    p = Path(f)
    if not p.is_file():
        out[f] = None
        print(f"{f}: 不存在")
        continue
    r = measure_loudness(p) | {"duration": round(probe(p)["duration"], 2)}
    out[f] = r
    print(f"{f}: {r}")
Path(sys.argv[1]).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
