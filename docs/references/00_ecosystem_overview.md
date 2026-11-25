# 開源程式化影片生態系對照總覽

本文件記錄程式化影片工具的設計參考。實際功能請以 [`vc/`](../../vc/)、[`styles/`](../../styles/) 與 [操作指南](../00_how_to_use.md) 為準；下列專案是參考來源，不代表功能完全相同。

## 四大生態系對照矩陣

| 專案 / 生態系 | 核心理念與技術路線 | 最強設計亮點 | 在本專案的落地位置 | 深入分析 |
| :--- | :--- | :--- | :--- | :--- |
| **`lemomo-ai/lemo-opuscar`** | 以風格包和導演語法製作程式化影片 | 分離風格與動畫內容 | [`styles/`](../../styles/)、[`style-director`](../../skills/style-director/SKILL.md) | [分析](01_lemo_opuscar_analysis.md) |
| **`wheresryan22/anatomy`** | 互動式等軸幾何插畫 | 分析幾何與視覺呈現 | [`isometric-anatomy`](../../skills/isometric-anatomy/SKILL.md)、[`vc/hf_scenes.py`](../../vc/hf_scenes.py) | [分析](02_wheresryan22_anatomy_analysis.md) |
| **`heygen-com/hyperframes`** | 以 HTML 和 GSAP 製作影片 | 時間軸與逐格渲染 | [`vc/hf_scenes.py`](../../vc/hf_scenes.py) | [分析](03_heygen_hyperframes_analysis.md) |
| **`remotion-dev/skills`** | 以 React / TypeScript 組合影片 | 元件化影片合成 | [`remotion/src/`](../../remotion/src/)、[`remotion-engineering`](../../skills/remotion-engineering/SKILL.md) | [分析](04_remotion_and_community_projects.md) |

## 與現有專案最大的差異化優勢

目前管線包含下列檢查與工具：
1. **`facts.yaml` + `strict_facts: true`**：每個說出口與畫在字卡上的數字都必須經人類或 Log 驗證並標示適用範圍。
2. **配音驅動整數影格時間軸（`vc plan`）**：改動腳本文字後，不靠人工憑感覺調秒數，而是由 Whisper 逐字時間戳重算所有動畫觸發點與錄影裁切。
3. **BDD + Gherkin 測試（`tests/features/` + `tests/bdd/`）**：驗證腳本、時間軸與輸出行為。影片目前使用單一版本，發布前仍須審查素材。
