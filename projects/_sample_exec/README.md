# `_sample_exec` — 嚴格數字範圍精簡版範例專案（60–90 秒）

本範例展示開啟 `strict_facts: true` 的 5 段主管摘要剪輯（Executive Cut）：
`hook` → `why_midsurface` → `manual` → `act` → `roi_time`。

`strict_facts: true` 會驗證每段旁白與畫面文字的數字，必須存在於該段引用的 `facts.yaml` 條目。事實條目也需附上 `scope`（適用範圍）。

直接編輯 [`script.json`](script.json) 的旁白與單一 `visual` 畫面。數據來源位於 [`facts.yaml`](facts.yaml)，素材路徑位於 [`project.yaml`](project.yaml)。

此範例保留文字設定，未附帶原始簡報、錄影或成品。要渲染影片，請先準備素材並調整腳本。風格比較設定位於 [`style_demo/`](style_demo/README.md)。

## 快速驗證指令

```powershell
.venv\Scripts\python.exe -m vc validate _sample_exec
```
