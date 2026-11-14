# `_sample` — 標準 7 段教學影片範例專案

本範例展示 **CAD Batch Validator v3.0** 的 7 段標準結構（約 150 秒）：
`vs_intro` → `why_midsurface` → `vs_result` → `theory` → `sop` → `full_chassis` → `roi_time`。

所有數據皆為教學示範用合成範例數值，用於驗證 `vc validate`、BDD 測試與雙軌版本（`internal` 含錄影標註 vs `public` 純動畫脫敏版）。

## 快速驗證指令

```powershell
.venv\Scripts\python.exe -m vc validate _sample
```
