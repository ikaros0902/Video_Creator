# `_sample_exec` — 嚴格數字範圍精簡版範例專案（60–90 秒）

本範例展示開啟 `strict_facts: true` 的 5 段主管摘要剪輯（Executive Cut）：
`hook` → `why_midsurface` → `manual` → `act` → `roi_time`。

`strict_facts: true` 會強制驗證**每一段旁白與畫面字卡上出現的所有數字**，都必須宣告於該段引用的 `facts.yaml` 條目且附上明確 `scope`（適用範圍），徹底杜絕單一測試模型數據被誤寫為通用表現。

## 快速驗證指令

```powershell
.venv\Scripts\python.exe -m vc validate _sample_exec
```
