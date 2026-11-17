# 風格參數

`project.yaml` 的 `style` 可用 `executive_navy`、`swiss_kinetic`、`blueprint`、`cyberpunk_neon`，或專案內 JSON 相對路徑。
自訂檔案不可跳出專案目錄。四個正式預設存放於 `styles/`；技能的 `assets/presets/` 提供起始副本。

`tokens.colors` 必須包含 primary、secondary、accent、background、surface、text_primary、text_secondary、positive、negative、border。
色值使用六碼十六進位格式。五種文字角色對 background 與 surface 的對比度均需達到 4.5:1。
primary、secondary 可供圖形填色使用，不代表可直接作為文字色。

`tokens.typography` 包含 heading_font、body_font、base_size_px（18–60）與 scale_ratio（1–2）。
字型名稱只允許英數、空格、逗號與連字號。渲染機必須具有所選字型；缺字需在預覽中檢查。
`tokens.surface` 包含 card_corner_radius（0–64）、border_width（0–8）、shadow（none 或 soft）。
`tokens.spacing.safe_margin_px` 介於 60–160。
這個值控制主要標題與內容容器的水平起點；標題頁保留額外 40 px 的版面偏移。
部分圖解內部座標維持固定，以保留既有幾何比例。

模板位於 `styles/templates/`。色彩、字型、卡片邊界可直接套用；新增版面時應使用字級與間距 tokens。
視覺風格驗證不代表內容正確，也不代表每一張圖片上的文字均有足夠對比。
