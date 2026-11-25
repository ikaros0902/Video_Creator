# 多代理協作調度指南

將本專案交給 AI Agent（Claude Code / Antigravity / Cursor）製作新影片時，建議把任務拆分為四個獨立角色分工執行，以防止單一上下文失焦或出現事實幻覺。

## 角色矩陣

| 角色 | 適用 Skill | 主要輸入 | 必須產出的客觀證據 |
| :--- | :--- | :--- | :--- |
| **1. Director & Fact Checker** | `style-director`、`script-copywriter` | `input/` 素材、Brief、`styles/` | `facts.yaml`、`script.json`、`vc validate` 結果 |
| **2. Isometric & HTML Animator** | `isometric-anatomy` | `timeline.json`、場景文字 | 瀏覽器畫面與時間軸檢查結果 |
| **3. Manim & Remotion Engineer** | `remotion-engineering` | `timeline.json`、錄影尺寸表 | `vc manim` 影格及延遲檢查結果 |
| **4. Maker-Checker QA Reviewer** | `tests/features/*.feature` | `output/*.mp4`、`pytest` | 測試結果、抽幀檢查及專案響度報告 |

## 平行化規則

1. `vc align` 產出 `words.json` 並執行 `vc plan` 後，`manim`、`hf`、`fit` 三條軌道彼此完全獨立，可平行執行。
2. 不可為了趕工跳過 **Fact Checker**：凡是 `script.json` 修改過任何一個數字，必須重跑 `vc validate` 並重新觸發 Maker-Checker 確認。
3. 修改動畫樣板後，應在 `tests/features/` 與 `tests/bdd/` 補充適當的行為測試。
