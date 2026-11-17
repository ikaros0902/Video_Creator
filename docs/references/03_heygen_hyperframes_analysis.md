# `heygen-com/hyperframes` 深度剖析與 GPU 整合（`05_references/03_heygen_hyperframes_analysis.md`）

> 原始專案：[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) — 「Write HTML. Render video. Built for agents.」，一套專為 AI Agent 與程式開發者設計的確定性 HTML/CSS/GSAP 影片算圖引擎。

## 1. HyperFrames 在本專案扮演的角色

本倉庫根目錄的 `package.json` 已直接安裝 `hyperframes ~0.9.26` 與 `gsap ^3.14.2`，並透過 `vc/hf_scenes.py` 驅動所有 `kind: anim` 場景（如 `cards3`、`steps4`、`vs_intro_mock`、`chassis_mock`）。

## 2. HyperFrames 官方專案結構重點

1. **Agent Skills 生態系（9 大官方技能）**：
   包含 `hyperframes`、`hyperframes-cli`、`hyperframes-registry`、`media-use`、`remotion-to-hyperframes`、`reverse-any-video`、`slideshow`、`style-sampling`、`figma`。透過 `npx skills add heygen-com/hyperframes` 可一鍵擴充。
2. **主題系統合約（`themes/CONTRACT.md`）**：
   官方定義了 `bold`、`editorial`、`neutral` 三種基礎 CSS 變數合約，確保字體、安全距與動態出現順序在任何解析度下不走樣。
3. **確定性捕捉原理（`window.__timelines` 合約）**：
   HyperFrames 拒絕依賴不穩定的即時螢幕錄製（`requestAnimationFrame` 會隨電腦負載掉幀）。它要求 HTML 檔案：
   - 舞台節點設定 `data-composition-id` 與 `data-duration`；
   - 建立暫停的 GSAP 時間軸：`gsap.timeline({ paused: true })`；
   - 註冊到 `window.__timelines[id]`。
   渲染器就能一幀一幀精確 `.seek(t)` 後截圖合成 MP4，保證 30 fps 毫秒級同步。

## 3. CLI 硬體加速與工程調校實測

在我們實測本機 `hyperframes render --help`（`v0.9.26`，見 `NVIDIA RTX A2000 8GB` 環境）確認原生支援以下關鍵旗標：

| CLI 旗標 | 功能 | 本專案整合方式 |
| :--- | :--- | :--- |
| `--gpu` | 啟用 FFmpeg 硬體視訊編碼（如 NVENC）加速輸出 MP4 | 已整合至 `vc/hf_scenes.py` 預設執行參數 |
| `--browser-gpu` | 啟用 Chromium 硬體 GPU / WebGL 合成（取代慢速 CPU SwiftShader） | 已整合至 `vc/hf_scenes.py`（遇驅動異常或 `--no-gpu` 時自動切換純軟體重試） |
| `--workers N` | 平行啟動多個無頭瀏覽器 Worker 逐幀擷取（縮短長動畫算圖時間） | 可視主機核心數與 VRAM 容量額外傳入 |
| `--frames-cache-dir <dir>` | 指定中間影格暫存資料夾位置 | 適合 Windows C 槽空間不足時改導向大空間磁碟 |
| `--experimental-fast-capture` | 實驗性高速幀擷取路徑 | 大批次靜態/低變動畫面可斟酌試用 |
