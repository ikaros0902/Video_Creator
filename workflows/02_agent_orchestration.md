# 多代理協作調度指南（`02_workflows/02_agent_orchestration.md`）

將本專案交給 AI Agent（Claude Code / Antigravity / Cursor）製作新影片時，建議把任務拆分為四個獨立角色分工執行，以防止單一上下文失焦或出現事實幻覺。

## 角色矩陣

| 角色 | 適用 Skill | 主要輸入 | 必須產出的客觀證據 |
| :--- | :--- | :--- | :--- |
| **1. Director & Fact Checker** | `00_video_creator_pipeline` + `01_lemo_opuscar_director` | `input/` 素材、Brief、風格庫 `04_styles/` | `facts.yaml`、`script.json`、`vc validate` 零錯誤輸出 |
| **2. Isometric & HTML Animator** | `02_anatomy_isometric` + `03_hyperframes_composer` | `timeline.json`、場景文字 | 通過 HTML 瀏覽器特寫檢驗、GSAP 時間軸無負延遲或溢位 |
| **3. Manim & Remotion Engineer** | `04_remotion_master` | `timeline.json`、錄影尺寸表 | `vc manim` 影格完全吻合、`MAX_LATE_FRAMES` 零超標 |
| **4. Maker-Checker QA Reviewer** | `07_features/*.feature` | `output/*.mp4`、`pytest` | `pytest -q` 全綠燈、`grab_frames.py` 視覺檢查無疊字、`-16 LUFS` 達標 |

## 平行化規則

1. `vc align` 產出 `words.json` 並執行 `vc plan` 後，`manim`、`hf`、`fit` 三條軌道彼此完全獨立，可平行執行。
2. 不可為了趕工跳過 **Fact Checker**：凡是 `script.json` 修改過任何一個數字，必須重跑 `vc validate` 並重新觸發 Maker-Checker 確認。
3. 修改動畫樣板後，務必把驗證用的固定幀測試寫進 `07_features/` 與 `08_tests/`，使結構迴歸無法重犯。
