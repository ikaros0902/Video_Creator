# `_sample` — 標準 7 段教學影片範例專案

本範例展示 **CAD Batch Validator v3.0** 的 7 段標準結構（約 150 秒）：
`vs_intro` → `why_midsurface` → `vs_result` → `theory` → `sop` → `full_chassis` → `roi_time`。

所有數據皆為教學示範用合成範例數值。每個場景只使用一份 `visual` 設定，輸出為單一影片。

直接編輯 [`script.json`](script.json) 的旁白與畫面。數字來源位於 [`facts.yaml`](facts.yaml)，原始素材路徑位於 [`project.yaml`](project.yaml)。

此範例未附帶原始簡報與錄影，可直接驗證文字設定。要產生影片，請先複製成自己的專案、補齊素材，並更新腳本內的錄影片段與動畫設定。

## 快速驗證指令

```powershell
.venv\Scripts\python.exe -m vc validate _sample
```
