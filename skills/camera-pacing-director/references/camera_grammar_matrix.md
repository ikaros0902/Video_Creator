# 運鏡介面

所有時間以單一場景起點為零。`shots` 的每個項目包含 `scene_ref`、`start_time_s`、`end_time_s` 與 `camera_motion`。
明確配置的鏡頭長度介於 1.5–5.5 秒，不得重疊或超出場景。長旁白可拆成連續鏡頭，不必裁短音訊。

| type | 用途 | 參數 |
|---|---|---|
| static_lock | 閱讀密集圖表 | start_scale |
| dolly_in | 強調重點 | start_scale、end_scale、focal_point |
| dolly_out | 從細節回到上下文 | start_scale、end_scale、focal_point |
| pan_horizontal | 橫向比較 | distance_px |
| pan_vertical | 垂直層次 | distance_px |
| focus_target | 聚焦元素 | target_selector、target_scale |

scale 限制為 1–1.5；焦點座標各介於 0–1；平移上限為 120 px。
focus_target 只接受單一元素 ID，例如 #title。找不到元素會中止動畫腳本。
2D HyperFrames 不支援真正的 3D orbit 或 whip transition；這些鏡頭需另用 Manim 或專門模板。

`camera_mode: fixed` 不加入自動位移；dynamic 加入輕微橫移；cinematic 加入緩慢推近。
自動模式沿用場景長度。顯式 camera_plan 優先於自動模式。
顯式計畫要求目標場景的所有版本均為 anim。只要其中一版為 recording 或 manim，HyperFrames 會拒絕執行並列出目標。
