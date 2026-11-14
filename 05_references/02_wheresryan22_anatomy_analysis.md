# `wheresryan22/anatomy` 深度剖析與等軸 CAD 整合（`05_references/02_wheresryan22_anatomy_analysis.md`）

> 原始專案：[wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) — 專職產出高精度互動式等軸（Isometric）機械剖面與複雜系統圖解的 Agent Skill，輸出純淨 SVG（可選配 WebGL Shaders）。

## 1. 為什麼這個專案對工程與 CAE 影片極具價值？

在 CAD / CAE 教學影片（特別是 `public` 公開版）裡，不能直接放客戶真實模型截圖，必須用乾淨的向量幾何表達「薄殼、偏置、肋條、沉頭孔、多層組件」。`wheresryan22/anatomy` 正是解決 AI 亂畫等軸透視圖的關鍵參考。

## 2. 核心架構與核心工具解構

| 元件 | 核心設計原理 | 解決什麼問題 |
| :--- | :--- | :--- |
| **`SKILL.md`** | 把圖表規模分為三個確定級距（Figure / Hero / Epic），並堅持 **Truth-First Modeling**：先算 3D 幾何數據再投影成 SVG | 杜絕 AI 用手感亂猜多邊形頂點座標，避免面與面交界處裂開 |
| **`kit/iso-kit.mjs`** | 內建 30° 等軸投影數學函式、4 階受光明暗配色（頂面/左面/右面/剖切邊）、以及依質心深度 `x + y + z` 排先後的**畫家演算法** | 徹底解決複雜組裝體的遮擋錯誤（Z-fighting / 圖層前後穿幫） |
| **`kit/tube.mjs` / `lathe.mjs`** | 參數化旋轉體（軸承、圓筒）與掃掠管路幾何生成器 | 讓工程圓柱孔與倒角在純 SVG 中精準呈現、不失真 |
| **`references/webgl.md`** | 當加入 WebGL Shader 效果時，強制限制 `devicePixelRatio <= 2` 並設定明確離屏畫布尺寸 | 防止 Chrome headless 算圖時發生 VRAM 溢位或 OOM 閃退 |
| **`references/verify.md` & `audit.mjs`** | 透過無頭 Chrome 自動渲染圖檔，並對關鍵接縫角落進行**特寫裁切檢驗（Close-up Inspection）** | 程式自檢圖標文字是否壓到引線或重疊多邊形邊界 |

## 3. 已經與未來可持續強化的落地方向

1. **Skill 規範落地**：已寫入 [`03_skills/02_anatomy_isometric/SKILL.md`](../03_skills/02_anatomy_isometric/SKILL.md) 與主題 [`04_styles/02_isometric_anatomy/`](../04_styles/02_isometric_anatomy/)。
2. **檢視 `vc/hf_scenes.py` 的幾何進化**：目前 `tpl_concept` 已採用乾淨的四階藍調配色與綠色中面線（並刻意把標籤推到右側 `left:1490px` 避開模型本體）。未來若要畫複雜結構（如多層機箱或沉頭孔剖視圖），可直接套用 `anatomy` 的 3D 投影與深度排序函式產生 inline SVG。
3. **特寫視覺檢查**：結合本倉庫的 `09_scripts/grab_frames.py` 與 Chrome 截圖，即可在送出 Remotion 合流前提早抓出字卡重疊。
