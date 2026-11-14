# 開源程式化影片生態系對照總覽（`05_references/00_ecosystem_overview.md`）

本專案（`Video_Creator`）不是閉門造車。我們深度分析了 2025–2026 年主流的「AI 程式碼拍片（Code-First Video）」開源專案與 Agent Skills，萃取各自最成熟的設計，直接整合進 `03_skills/`、`04_styles/`、`vc/` 與 `remotion/`。

## 四大生態系對照矩陣

| 專案 / 生態系 | 核心理念與技術路線 | 最強設計亮點 | 在本專案的落地位置 | 深入分析 |
| :--- | :--- | :--- | :--- | :--- |
| **`lemomo-ai/lemo-opuscar`** | 不用影片擴散模型，以 `DIRECTOR.md` 導演語法 + `styles/<slug>/` 規格包全程式生成影片 | `STYLE.md` + `style.json` 主題解耦、絕對時間軸繪製、鏡頭節奏檢驗 | [`04_styles/`](../04_styles/) 風格庫與 [`03_skills/01_lemo_opuscar_director/`](../03_skills/01_lemo_opuscar_director/SKILL.md) | [`01_lemo_opuscar_analysis.md`](01_lemo_opuscar_analysis.md) |
| **`wheresryan22/anatomy`** | 專精機械與複雜系統的互動式等軸幾何插畫（SVG + 選配 WebGL Shader） | Truth-First 3D 座標建模、四階受光明度、畫家深度排序、無頭瀏覽器特寫稽核 | [`03_skills/02_anatomy_isometric/`](../03_skills/02_anatomy_isometric/SKILL.md) 與 [`vc/hf_scenes.py`](../vc/hf_scenes.py) 等軸 SVG | [`02_wheresryan22_anatomy_analysis.md`](02_wheresryan22_anatomy_analysis.md) |
| **`heygen-com/hyperframes`** | Write HTML. Render video. 專為 Agent 打造的 HTML + GSAP 確定性算圖 CLI | `data-composition-id` + 暫停的 GSAP `window.__timelines` 合約、`--gpu --browser-gpu` 硬體加速 | 本機已裝 `v0.9.26`、`vc/hf_scenes.py`、`03_skills/03_hyperframes_composer/` | [`03_heygen_hyperframes_analysis.md`](03_heygen_hyperframes_analysis.md) |
| **`remotion-dev/skills` & 社群專案** | React / TypeScript 元件化影片合成與生態系自動化工作流 | `spring()` 阻尼物理曲線、非線性緩動、Whisper 字幕對齊、`--gl=angle` GPU 合成 | [`remotion/src/`](../remotion/src/)、[`vc/render.py`](../vc/render.py)、[`03_skills/04_remotion_master/`](../03_skills/04_remotion_master/SKILL.md) | [`04_remotion_and_community_projects.md`](04_remotion_and_community_projects.md) |

## 與現有專案最大的差異化優勢

單純的 Prompt-to-Video Agent 常出現三個工程痛點：**數字幻覺、聲音畫面錯位、缺乏自動化回歸測試**。`Video_Creator` 補齊了完整的確定性工業級底座：
1. **`facts.yaml` + `strict_facts: true`**：每個說出口與畫在字卡上的數字都必須經人類或 Log 驗證並標示適用範圍。
2. **配音驅動整數影格時間軸（`vc plan`）**：改動腳本文字後，不靠人工憑感覺調秒數，而是由 Whisper 逐字時間戳重算所有動畫觸發點與錄影裁切。
3. **BDD + Gherkin 契約測試（`07_features/` + `08_tests/`）**：把易讀度、詞彙出現順序、公開版無真實錄影、響度規範全部轉成 `pytest-bdd` 自動化測試。
