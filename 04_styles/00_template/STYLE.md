# `00_template` — 視覺風格設計範本（Style Pack Template）

本範本汲取自 [`lemomo-ai/lemo-opuscar`](../05_references/01_lemo_opuscar_analysis.md) 之 `styles/<slug>/` 規格。

## 建立新風格的步驟

1. 複製本資料夾：`Copy-Item -Recurse 04_styles/00_template 04_styles/<NN_slug>`。
2. 填寫 `style.json` 裡的配色、字體、動態曲線（GSAP / Remotion spring）與禁用清單。
3. 在 `STYLE.md` 用白話寫明：
   - 適用影片類型（教學、發布、摘要）
   - 色彩情緒與對比度保證（>= 4.5:1）
   - 鏡頭運鏡與轉場節奏原則
   - 絕對不可踩的視覺禁忌
