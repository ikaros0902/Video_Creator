"""產生透明 logo，並貼在影片的深色底上輸出預覽圖，方便目視檢查邊緣與顏色。"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from vc.brand import make_logos  # noqa: E402

out = Path(sys.argv[1])
files = make_logos(out)
bg = np.zeros((360, 1400, 3), np.float32)
bg[:] = (32, 18, 11)                       # 影片背景色 #0b1220（BGR）
x = 40
for k, f in files.items():
    im = cv2.imread(str(f), cv2.IMREAD_UNCHANGED)
    print(k, im.shape)
    s = 110 / im.shape[0]
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA).astype(np.float32)
    h, w = im.shape[:2]
    a = im[:, :, 3:] / 255.0
    bg[120:120 + h, x:x + w] = bg[120:120 + h, x:x + w] * (1 - a) + im[:, :, :3] * a
    x += w + 80
cv2.imwrite(str(out / "preview.png"), bg.astype(np.uint8))
