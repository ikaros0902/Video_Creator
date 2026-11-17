"""從錄影擷取指定秒數的全解析度畫面，可選擇裁切，並拼成 2 欄總覽圖，用來人工確認剪點。

用法：.venv\\Scripts\\python.exe 09_scripts\\grab_frames.py <影片> <輸出 jpg> <秒數,秒數,...> [x,y,w,h] [欄寬]
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

src, out = sys.argv[1], Path(sys.argv[2])
times = [float(t) for t in sys.argv[3].split(",")]
crop = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
col_w = int(sys.argv[5]) if len(sys.argv) > 5 else 960

cap = cv2.VideoCapture(src)
tiles = []
for t in times:
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    if not ok:
        print(f"{t}: 讀不到影格")
        continue
    if crop:
        x, y, w, h = crop
        f = f[y:y + h, x:x + w]
    s = col_w / f.shape[1]
    f = cv2.resize(f, (col_w, int(f.shape[0] * s)), interpolation=cv2.INTER_AREA)
    cv2.rectangle(f, (0, 0), (110, 34), (0, 0, 0), -1)
    cv2.putText(f, f"{t:.1f}s", (6, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    tiles.append(f)
cap.release()
h = max(t.shape[0] for t in tiles)
tiles = [np.pad(t, ((0, h - t.shape[0]), (0, 0), (0, 0))) for t in tiles]
if len(tiles) % 2:
    tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + 2]) for i in range(0, len(tiles), 2)]
out.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(out), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
print(f"{out}  {len(times)} 張")
