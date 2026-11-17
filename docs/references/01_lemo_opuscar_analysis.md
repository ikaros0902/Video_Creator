# `lemomo-ai/lemo-opuscar` 深度剖析與整合策略（`05_references/01_lemo_opuscar_analysis.md`）

> 原始專案：[lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) — 一套用程式碼拍片的風格工具箱（內建 99 種電影/平面/紀錄片視覺風格包，完全不依賴文生視頻擴散模型）。

## 1. 核心架構解構

`lemo-opuscar` 的強大之處在於它將「**導演思維（Narrative & Camera Grammar）**」、「**美術風格（Style Tokens）**」與「**算圖引擎（Absolute-Time Renderer）**」徹底拆開：

| 核心元件 | 原始作用 | 對我們的啟發 |
| :--- | :--- | :--- |
| **`SKILL.md`** | Agent 進入點：決定先寫分鏡、選單一風格、再寫動畫程式碼的硬順序 | 我們在 `03_skills/01_lemo_opuscar_director/SKILL.md` 建立相同前置紀律 |
| **`DIRECTOR.md`** | 定義鏡頭語言（景別節奏、字卡最低停留時間、鏡頭運動動機、完片邊界幀自檢） | 直接對應 `vc/manim_scenes.py`、`remotion/src/Main.tsx` 的 `camera` 與安全停留時間 |
| **`TECHNIQUE.md`** | 規範「以絕對時間 `t` 驅動 Canvas / WebGL 繪圖、程式化音效與 FFmpeg 音畫合流」 | 與本專案 `vc plan` + paused GSAP / Remotion frame 計算理念高度一致 |
| **`styles/<slug>/`** | 每個風格獨立存放 `STYLE.md`、`style.json` 與 `DEMO.md`（涵蓋紀錄片證據風、工程藍圖、手繪、印刷設計、東方視覺等領域） | 直接化為本專案的 [`04_styles/`](../04_styles/) 架構（`00_template` 到 `04_swiss_kinetic_type`） |

## 2. `STYLE.md` + `style.json` 雙檔設計精髓

在傳統 AI 輔助寫動畫時，如果只用自然語言對 LLM 說「做一個酷炫深藍簡報」，每次產出的色碼與圓角都會飄移。`lemo-opuscar` 透過兩個檔案鎖死一致性：
- **`style.json`**：提供機器精確讀取的色碼表（主底色、卡片底色、強調色、語意警戒色）、字級階梯、預設緩動曲線與 `safe_zone`。
- **`STYLE.md`**：給 Agent 與人類導演看的「設計品味合約」，明確寫出什麼情境該用這個風格、哪些視覺手法（例如彩虹漸層、過度彈跳緩動）**禁止出現**。

## 3. 我們採納與取捨的地方

- **採納並實作**：
  1. 建立 `04_styles/` 目錄，以標準化的 `STYLE.md` + `style.json` 提供 4 套企業與工程專用視覺主題。
  2. 將 `DIRECTOR.md` 的「文字最短停留（`>= 1.8s`）」、「有動機的三種運鏡（`fixed`, `dolly_in`, `dolly_out`）」與「頭中尾關鍵幀抽查」寫入 `03_skills/01_lemo_opuscar_director/SKILL.md`。
- **刻意不直接照搬的部分**：
  - `lemo-opuscar` 原生以單一自訂 HTML Canvas/Puppeteer 循環做長片算圖；而我們已經整合 **Manim**（數學公式與精細幾何步驟）、**HyperFrames**（標準 GSAP HTML）與 **Remotion**（實機螢幕錄影剪輯與多軌音畫合流），保留現有三引擎分工反而更適合企業工程軟體教學。
