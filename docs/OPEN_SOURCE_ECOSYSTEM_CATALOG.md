# Video Creator 開源生態手冊與跨領域整合規範
# (Open Source Ecosystem Catalog & Toolchain Specification)

> **版本**：v2.0 (Milestone 2 權威標準)  
> **維護團隊**：Video Creator Architecture & Toolchain Working Group  
> **基準目錄**：`d:\Ikaros\Video_Creator`  
> **發布日期**：2026-11-15  

---

## 目錄 (Table of Contents)

1. [導言與全景生態圖譜 (Introduction & Ecosystem Architecture)](#1-導言與全景生態圖譜-introduction--ecosystem-architecture)
   - [1.1 手冊編纂目的與架構總覽](#11-手冊編纂目的與架構總覽)
   - [1.2 Video Creator 7 層管線整合全景圖](#12-video-creator-7-層管線整合全景圖)
   - [1.3 專案二元分類系統（方法論/範式 vs 軟體工具/CLI）](#13-專案二元分類系統方法論範式-vs-軟體工具cli)
2. [影片設計與生成管線 (Video Design & Generation Pipeline) [11 專案]](#2-影片設計與生成管線-video-design--generation-pipeline-11-專案)
3. [視覺美術與資產體系 (Visual Art & Graphic Asset Ecosystem) [11 專案]](#3-視覺美術與資產體系-visual-art--graphic-asset-ecosystem-10-專案)
4. [文案、敘事與腳本架構 (Copywriting, Narrative & Scripting) [11 專案]](#4-文案敘事與腳本架構-copywriting-narrative--scripting-10-專案)
5. [剪輯、轉碼與母帶合成 (Video Editing, Transcoding & Mastering) [10 專案]](#5-剪輯轉碼與母帶合成-video-editing-transcoding--mastering-10-專案)
6. [動態圖形、代碼動畫與著色器 (Motion Graphics, Kinetic Code & Shaders) [11 專案]](#6-動態圖形代碼動畫與著色器-motion-graphics-kinetic-code--shaders-11-專案)
7. [簡報、排版與向量投影片 (Presentation Slides & Vector Layouts) [11 專案]](#7-簡報排版與向量投影片-presentation-slides--vector-layouts-10-專案)
8. [跨領域整合矩陣與落地指南 (Cross-Domain Integration Matrix & Toolchain Blueprint)](#8-跨領域整合矩陣與落地指南-cross-domain-integration-matrix--toolchain-blueprint)
   - [8.1 外部工具鏈分層存放規範 (tools/ vs external/ vs skills/ vs rules/)](#81-外部工具鏈分層存放規範-tools-vs-external-vs-skills-vs-rules)
   - [8.2 本地 Rust 創意工具四重奏 (EffectCraft, PhotoCraft, VectorCraft, DeckCraft) 聯動手冊](#82-本地-rust-創意工具四重奏-effectcraft-photocraft-vectorcraft-deckcraft-聯動手冊)
   - [8.3 核心工具相依性與環境前置檢核表](#83-核心工具相依性與環境前置檢核表)
   - [8.4 開源協議相容性與商用合規分析 (License Compliance)](#84-開源協議相容性與商用合規分析-license-compliance)
- [附錄：專案名稱與代碼快速索引 (Quick Reference Index)](#附錄專案名稱與代碼快速索引-quick-reference-index)

---

## 1. 導言與全景生態圖譜 (Introduction & Ecosystem Architecture)

### 1.1 手冊編纂目的與架構總覽
在自動化與程式碼驅動之影片創作領域中，單純依賴單一大型黑箱模型往往導致「幻覺不可控、影格不精確、風格易漂移、二進位肥大」等工程瓶頸。本專案（Video Creator）採用**高密度規格驅動開發 (Spec-Driven Development, SDD)** 與**確定性影格合成 (Deterministic Frame-Accurate Composition)** 架構，將影片生產全流程解耦為清晰的工業級流水線。

本手冊全面盤點並深度調研當前開源世界中涵蓋「影片、美術、文案、剪輯、動態、簡報」6 大核心領域之 **62 個頂尖 GitHub 專案與 Agent Skills**。每項收錄均貫徹以下 6 大維度之深度規格化梳理：
1. **專案名稱與官方/GitHub 連結**
2. **核心特色與技術架構優勢**
3. **二元類型判定**（方法論/Prompt/範式 vs 軟體工具/CLI/庫/微服務）
4. **Video Creator 管線整合定位**
5. **安裝/調用前置要求與相依性**
6. **故障降級防呆方案**

### 1.2 Video Creator 7 層管線整合全景圖

```text
[Layer 1: Input Layer] (自包含可移植專案空間)
  projects/<name>/input/ (slides, recordings, audio, assets) + project.yaml + facts.yaml + script.json
        │
        ▼
[Layer 2: Rules & Skills Governance Layer] (遵循 skill-creator 標準規範)
  skills/ (style-director, script-copywriter, camera-pacing-director, guizang-slide-stylist, etc.)
  rules/  (chinese_copywriting, anti_ai_slop, egm_review, presentation_design, etc.)
  styles/ (executive_navy, swiss_kinetic, blueprint, isometric)
        │
        ▼
[Layer 3: Core CLI Pipeline & Ingestion Layer]
  vc CLI (ingest-ppt, ingest-rec, voice, align, plan, fit, hf, manim, render, export-jianying)
        │
        ├──────────────────────┬──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼                      ▼
[Layer 4: Clip Generators] [Layer 4: Vector Engines] [Layer 5: Native Rust] [Layer 5: Ext Toolchain]
  HyperFrames (HTML/GSAP)    Manim (GPU NVENC)      DeckCraft (1080p PPTX)   tools/pyJianYingDraft
  Reveal.js / Marp (Slides)  VectorCraft (SVG/AI)   EffectCraft (AE Layers)  tools/ppt-master
                             PhotoCraft (PSD Layers) Recordly (Screen AutoZoom)
        │                      │                      │                      │
        └──────────────────────┼──────────────────────┴──────────────────────┘
                               ▼
[Layer 6: Master Compositor & Timeline Layer]
  remotion/ (React 19 / 18, WebGPU/ANGLE, EBU R128 Audio Ducking, Frame-Accurate Timeline)
                               │
                               ▼
[Layer 7: Standardized Output Layer]
  projects/<name>/output/
  ├── internal/ (master.mp4, master.srt)
  ├── public/   (public_desensitized.mp4)
  └── reports/  (metadata.json, loudness_report.json, audit_trail.json)
```

### 1.3 專案二元分類系統（方法論/範式 vs 軟體工具/CLI）
為杜絕將 Prompt 誤作可執行二進位下載、或將數十 GB 的 PyTorch 模型直接塞入 Git 倉庫的架構混亂，本手冊貫徹**二元類型嚴格隔離**：

1. **【方法論 / 提示詞 / 設計範式】(Methodology & Behavioral Rules)**：
   - **本質**：思考架構、文案公式、排版公理、分鏡引導或視覺 Design Tokens。
   - **落地形式**：嚴格遵循 `skill-creator` 規範蒸餾為 `rules/*.md` 或 `skills/<name>/SKILL.md`，納入上下文引導 LLM Agent 與靜態檢查門禁。
2. **【軟體工具 / CLI / 庫 / 微服務】(Software, Binaries & Libraries)**：
   - **本質**：確定性可執行二進位檔、Python 庫、Node.js 模組或獨立微服務。
   - **落地形式**：下載/clone 至 `tools/`（輕量/綠色工具）、`external/`（大型桌面應用/前端獨立模組）、或安裝於專案虛擬環境（`.venv` / `node_modules`），由 `vc` Python 套件透過子行程或 API 呼叫。

---

## 2. 影片設計與生成管線 (Video Design & Generation Pipeline) [11 專案]

### 2.1 mileson/chaojifeng-video-design (超級峰視頻設計)
- **官方/GitHub 連結**：https://github.com/mileson/chaojifeng-video-design
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 專為 AI 影音導演 Agent 設計的分鏡與節奏方法論，深入定義了「短影音 3 秒 Hook、黃金 15 秒展開、起承轉合高潮推進」之時間軸架構。
  - 獨創「聲畫節奏對齊」與「音樂樂句峰值 (Drop/Beat) 吸附」公式，將視覺畫面切換精準同步至 BGM 重音。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer)
  - **具體職責與合約**：蒸餾為 `skills/camera-pacing-director`，引導分鏡規劃生成 `camera_plan.json`，計算每鏡頭保留長度（嚴格約束於 1.5s 至 5.5s 區間）。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Markdown 規範手冊與時鐘計算腳本，無外部二進位相依。MIT 協議。
- **故障降級防呆**：若 Agent 未配置音樂節奏資料，自動降級為基於旁白語音標點符號之均勻時長切分。

### 2.2 lemomo-ai/lemo-opuscar (Lemo-Opuscar 程式化導演)
- **官方/GitHub 連結**：https://github.com/lemomo-ai/lemo-opuscar
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 提倡「樣式與代碼嚴格解耦」，採用 `STYLE.md` + `style.json` 架構將影片視覺主題、色彩語意與鏡頭運動抽離為純資料設定檔。
  - 支援熱抽換樣板引擎，確保同一套劇本文案能秒級切換為「瑞士極簡」、「工程藍圖」或「科技暗黑」不同視覺風格。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer) & `styles/` 主題目錄
  - **具體職責與合約**：定義專案主題契約，供 `skills/style-director` 調用，將 Design Tokens 注入 Remotion 與 Hyperframes 模組。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：遵循 JSON Schema 與 Jinja2 樣板語法，無額外依賴。MIT 協議。
- **故障降級防呆**：若專案 `project.yaml` 未指定 `style`，預設回退至 `executive_navy` 核心穩定主題。

### 2.3 wheresryan22/anatomy (Anatomy 等軸透視規範)
- **官方/GitHub 連結**：https://github.com/wheresryan22/anatomy
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - Truth-First 機械與架構等軸透視 (Isometric 30-degree) 設計系統，定義精準的 3D 空間 2.5D 平面投影矩陣。
  - 專注於硬體剖面圖、微服務架構爆炸圖（Exploded View）與高密度零件標註之視覺排版。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer)
  - **具體職責與合約**：蒸餾為 `skills/isometric-anatomy`，引導產出等軸架構圖卡片，輸出相容於 Remotion 與 Hyperframes 的向量 SVG/HTML。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：純 SVG/CSS 矩陣變換語法，相容於 Chromium/Node.js 環境。MIT 協議。
- **故障降級防呆**：若渲染端不支援 3D 變形，自動降級為 2D 扁平化模組框圖展示。

### 2.4 google/elephant-goldfish-model (大象與金魚評審模型)
- **官方/GitHub 連結**：https://github.com/google/elephant-goldfish-model
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 規格驅動開發 (SDD) 之雙代理架構典範：「大象 (Elephant)」負責維持長程全域規格上下文，「金魚 (Goldfish)」模擬零背景用戶以 5 秒 fresh-eyes 進行零寬容盲審。
  - 防範開發者自我寬容偏差，將驗收門禁建立在可客觀量化之重複性指標之上。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Governance)
  - **具體職責與合約**：納入全域評審協議 `rules/egm_review_protocol.md`，約束腳本起草、分鏡排審與最終影片渲染之客觀驗收。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：評審規範文檔與 Agent 提示詞協議。Apache-2.0 協議。
- **故障降級防呆**：審查未通過時自動阻斷流水線進入昂貴的母帶渲染階段。

### 2.5 FujiwaraChoki/MoneyPrinter (自動化短影音印表機)
- **官方/GitHub 連結**：https://github.com/FujiwaraChoki/MoneyPrinter
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 整合 LLM 腳本生成、TTS 語音、Pexels/Pixabay 免版權素材檢索、字幕合成與背景音樂拼接之全自動端到端短影音生成器。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：作為快速原型生成與免版權空鏡素材自動採集工具，存放於 `external/MoneyPrinter`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, FFmpeg, ImageMagick, MoviePy, Pexels API Key。MIT 協議。
- **故障降級防呆**：當素材庫 API 額度耗盡時，自動降級為純色幾何背景或本地快取素材。

### 2.6 hpcaitech/Open-Sora (開源 Sora 影片擴散生成)
- **官方/GitHub 連結**：https://github.com/hpcaitech/Open-Sora
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - Colossal-AI 團隊打造之開源高效能視訊擴散架構（STDiT / DiT），支援多解析度與變動時長生成。
  - 具備先進的分散式訓練與推理加速技術，顯著降低高畫質影片生成的計算延遲。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators - 外部節點)
  - **具體職責與合約**：作為外部非同步視覺生成節點，專門用於產生高畫質寫實空鏡或動態抽象轉場素材，存放於 `external/Open-Sora`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, PyTorch 2.2+, CUDA 12+, VRAM >= 16GB (建議 24GB+ 或遠端 API)。Apache-2.0 協議。
- **故障降級防呆**：本機未配置高階顯卡時，標記為 WARN 並自動降級為本地 Procedural 幾何動態。

### 2.7 THUDM/CogVideo (CogVideoX 開源影片生成)
- **官方/GitHub 連結**：https://github.com/THUDM/CogVideo
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 清華大學與智譜 AI 開源之 SOTA 視訊生成模型，採用 3D 因果 VAE 與專家 Transformer 架構。
  - 文本理解能力極強，動態時間連貫性優異，支援複雜運鏡指令。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators - 外部節點)
  - **具體職責與合約**：外部概念動畫擴展節點，產出特寫過渡視訊，存放於 `external/CogVideo`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, PyTorch 2.0+, Diffusers, CUDA 12+, VRAM >= 12GB。Apache-2.0 協議。
- **故障降級防呆**：顯存不足時降級為低解析度預覽或使用靜態圖片平移 (Ken Burns Effect)。

### 2.8 comfyanonymous/ComfyUI (ComfyUI 節點式視覺工作台)
- **官方/GitHub 連結**：https://github.com/comfyanonymous/ComfyUI
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 基於圖形節點的生成式 AI 工作台，支援 SD1.5, SDXL, Flux, AnimateDiff, ControlNet 等前沿技術。
  - 具備完備的 Headless REST/WebSocket API，支援將自訂節點工作流保存為 JSON 實現完全自動化。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine - 微服務)
  - **具體職責與合約**：按需無頭生成高品質背景壁紙、概念圖示與動態序列幀，存放於 `external/ComfyUI`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, PyTorch, CUDA GPU (VRAM >= 8GB)。GPL-3.0 協議。
- **故障降級防呆**：當 ComfyUI 服務未啟動時，管線自動降級為調用本地向量資產庫。

### 2.9 Huanshere/VideoLingo (VideoLingo 影片翻譯與在地化)
- **官方/GitHub 連結**：https://github.com/Huanshere/VideoLingo
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 全流程影片翻譯與在地化工具，整合 WhisperX 音素級對齊、NLP 智慧斷句、語音克隆與畫面無痕合成。
  - 專注於避免字幕跨行折斷與機械直譯，產出高度口語化的雙語字幕。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：國際化發布模組，負責長影片字幕斷句優化與多語言母帶輸出，存放於 `external/VideoLingo`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, Streamlit, FFmpeg, WhisperX, PyTorch。Apache-2.0 協議。
- **故障降級防呆**：若未啟用多語言翻譯，管線僅產出專案原始預設語系字幕。

### 2.10 RayVentura/ShortGPT (ShortGPT 短影音內容框架)
- **官方/GitHub 連結**：https://github.com/RayVentura/ShortGPT
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 專為自動化影片創作設計的 Python 框架，提供強大的內容引擎、語音合成編排與多平台格式適配能力。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：輔助模組，用於社群短片快速切片與橫直轉化測試，存放於 `external/ShortGPT`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, MoviePy, FFmpeg, Edge-TTS。MIT 協議。
- **故障降級防呆**：若未配置語音金鑰，自動回退使用本地 Kokoro TTS 引擎。

### 2.11 storytold/artcraft (ArtCraft / VectorCraft 視覺創作引擎)
- **官方/GitHub 連結**：https://github.com/storytold/artcraft
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 純 Rust 打造的高效能可編程創意引擎，支援向量圖形運算、圖層合成與原生 MCP (Model Context Protocol) 服務。
  - 本地靜態單一二進位，零外部依賴，毫秒級解析 SVG/AI/CAD 檔案並精確光柵化。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Vector Engines) & `tools/craft_tools.py`
  - **具體職責與合約**：向量資產解析與點陣化核心，將架構圖與向量圖形轉為確定性 1080p 圖層。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Windows x64 獨立可執行檔 (`vectorcraft-cli.exe`)，零額外執行期依賴。
- **故障降級防呆**：若未偵測到 Rust 二進位，自動降級為調用 Node.js Puppeteer 渲染 SVG。

---

## 3. 視覺美術與資產體系 (Visual Art & Graphic Asset Ecosystem) [11 專案]

### 3.1 meta/astryx (Astryx 企業級設計系統)
- **官方/GitHub 連結**：https://github.com/meta/astryx
- **類型判定**：【軟體工具/CLI/庫兼設計系統】
- **核心特色與技術架構優勢**：
  - Meta 開源之 AI/Agent-Ready 設計系統，基於 StyleX 達成零執行期 CSS 開銷。
  - 具備嚴格的 Design Tokens 階層架構，規範間距 (Spacing)、字級排版 (Typography) 與色彩語意映射。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills) & `packages/remotion/`
  - **具體職責與合約**：視覺字卡、數據圖表與 UI 模擬介面的主題基底，規範 Design Tokens 命名與層疊切換。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, React 18+, @stylexjs/stylex。MIT 協議。
- **故障降級防呆**：在純 HTML 環境中降級為原生 CSS 變數定義。

### 3.2 nexu-io/open-design (Open Design AI 工作台)
- **官方/GitHub 連結**：https://github.com/nexu-io/open-design
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 開源 Local-First AI 設計工作台，透過 AI Agent 從文字摘要即時產出網頁佈局、投影片與動態資產。
  - 提供安全沙盒預覽機制，支援視覺元件程式碼熱重載。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：視覺素材生成與 UI 原型預覽伺服器，存放於 `external/open-design`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, Docker / Local CLI。MIT 協議。
- **故障降級防呆**：未啟動時使用靜態模板替代。

### 3.3 storytold/photocraft (PhotoCraft 影像圖層合成引擎)
- **官方/GitHub 連結**：https://github.com/storytold/photocraft
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 純 Rust 開發之 Photoshop 開源替代品，雙向讀寫 PSD/PSB 檔案，支援非破壞性調整圖層與色彩校正。
  - 內建原生 CLI (`photocraft-cli.exe`) 與 MCP 服務，可在無頭環境下極速解析圖層樹並替換文字/圖片。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (Native Rust Creative Suite) & `tools/craft_tools.py`
  - **具體職責與合約**：封面圖自動產出、PSD 模板動態替換、批次去背與圖層資訊剖析 (`photo_info()`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Windows x64 獨立可執行檔 (`photocraft-cli.exe`)，零依賴。商用/開源雙軌。
- **故障降級防呆**：若未找到二進位檔，自動回退使用 Python Pillow (PIL) 處理基礎點陣圖。

### 3.4 KenneyNL/Adobe-Alternatives (Adobe 開源替代全景地圖)
- **官方/GitHub 連結**：https://github.com/KenneyNL/Adobe-Alternatives
- **類型判定**：【方法論/提示詞/設計範式（資源索引）】
- **核心特色與技術架構優勢**：
  - 彙整業界最完整的開源/免費創意工具替代圖譜（涵蓋影像、向量、3D、音訊、字型），明確標註許可協議與替代關係。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Governance)
  - **具體職責與合約**：作為專案工具鏈擴充、許可協議合規性審查之標準索引手冊。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Markdown 靜態文檔。CC0 協議。
- **故障降級防呆**：無執行期依賴。

### 3.5 tailwindlabs/tailwindcss (Tailwind CSS 實用優先樣式庫)
- **官方/GitHub 連結**：https://github.com/tailwindlabs/tailwindcss
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 實用優先 (Utility-first) CSS 引擎，提供極致約束的間距尺度、顏色梯度與排版系統。
  - JIT (Just-In-Time) 編譯秒級響應，杜絕命名混亂與 CSS 樣式污染。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer) & `packages/remotion/`
  - **具體職責與合約**：Remotion 字卡與 Hyperframes 畫面的標準排版規範，消除視覺漂移。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, npm/pnpm。MIT 協議。
- **故障降級防呆**：可降級為內嵌 Inline Styles。

### 3.6 radix-ui/primitives (Radix UI 無頭組件庫)
- **官方/GitHub 連結**：https://github.com/radix-ui/primitives
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 無頭 (Headless) React UI 原語，完全解耦互動狀態機與外觀樣式，支援無障礙規範 (WAI-ARIA)。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：影片中軟體 UI 錄影重製、操作對話框與下拉選單的仿真模擬組件。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, React 18+。MIT 協議。
- **故障降級防呆**：若未使用 React 則使用靜態 SVG 模擬。

### 3.7 lucide-icons/lucide (Lucide 現代美型向量圖標庫)
- **官方/GitHub 連結**：https://github.com/lucide-icons/lucide
- **類型判定**：【軟體工具/CLI/庫（資產庫）】
- **核心特色與技術架構優勢**：
  - 1400+ 簡潔一致的向量圖標庫，基於 24x24 像素網格與 2px 統一描邊，視覺重心精準調校。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer) & 資產庫
  - **具體職責與合約**：影片步驟引導、功能要點標籤與按鈕提示的標準統一圖標來源。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：npm install lucide-react 或純 SVG 檔案。ISC 協議。
- **故障降級防呆**：缺失特定圖標時自動 fallback 至通用圓點或文字標籤。

### 3.8 adobe-fonts/source-han-sans (思源黑體高品質字型族)
- **官方/GitHub 連結**：https://github.com/adobe-fonts/source-han-sans
- **類型判定**：【軟體工具/CLI/庫（字型資產）】
- **核心特色與技術架構優勢**：
  - Adobe 與 Google 聯合開發之開源 Pan-CJK 無襯線字型，具備 7 種標準字重（ExtraLight 至 Heavy）。
  - 全面覆蓋繁體中文、簡體中文與英數標點，跨平台渲染保證零豆腐塊、零行高漂移。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 1 (Assets) & Layer 6 (Compositor)
  - **具體職責與合約**：全專案視頻字卡、字幕與投影片之法定基準字體，存於 `assets/fonts/`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：OTF/TTF 字型檔案。SIL Open Font License 1.1。
- **故障降級防呆**：環境缺失時自動退回微軟正黑體或系統標準無襯線字體。

### 3.9 penpot/penpot (Penpot 開源設計與原型平台)
- **官方/GitHub 連結**：https://github.com/penpot/penpot
- **類型判定**：【軟體工具/CLI/庫（設計平台）】
- **核心特色與技術架構優勢**：
  - 開源 Figma 替代品，以 SVG 與 CSS 為原生格式，設計稿可直接輸出向量資產。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Art Assets)。產出 SVG 插圖後放入 `projects/<name>/input/assets/`。
- **安裝/調用前置要求與相依性**：
  - 自架服務或雲端版，MPL-2.0。
- **故障降級防呆**：缺少時改用內建 `styles/` 與 `skills/` 設定，不阻斷主流程。

### 3.10 tabler/tabler-icons (Tabler 高密度技術圖標庫)
- **官方/GitHub 連結**：https://github.com/tabler/tabler-icons
- **類型判定**：【軟體工具/CLI/庫（資產庫）】
- **核心特色與技術架構優勢**：
  - 5000+ 像素級對齊的開源 SVG 圖標，專為高密度技術資訊看板與雲端架構設計。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer) & 資產庫
  - **具體職責與合約**：技術架構展示、資料庫與網路拓撲圖卡片的圖標庫存。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：SVG 檔案或 npm 套件。MIT 協議。
- **故障降級防呆**：缺失時 fallback 至 Lucide 圖標庫。

---

### 3.11 excalidraw/excalidraw (Excalidraw 手繪風白板)
- **官方/GitHub 連結**：https://github.com/excalidraw/excalidraw
- **類型判定**：【軟體工具/CLI/庫（繪圖工具）】
- **核心特色與技術架構優勢**：
  - 手繪風向量圖，匯出 SVG 與 PNG，適合概念圖。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Art Assets)。
- **安裝/調用前置要求與相依性**：
  - 瀏覽器或 npm 套件，MIT。
- **故障降級防呆**：缺少時改用內建 `styles/` 與 `skills/` 設定，不阻斷主流程。

## 4. 文案、敘事與腳本架構 (Copywriting, Narrative & Scripting) [11 專案]

### 4.1 sparanoid/chinese-copywriting-guidelines (中文文案排版指北)
- **官方/GitHub 連結**：https://github.com/sparanoid/chinese-copywriting-guidelines
- **類型判定**：【方法論/提示詞/設計範式兼硬規則】
- **核心特色與技術架構優勢**：
  - 業界公認之中文排版金科玉律，規範中英文字元間空格留白、全半角標點符號用法與專有名詞標準大小寫。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules Layer) & CLI 靜態檢查
  - **具體職責與合約**：蒸餾為硬性規範 `rules/chinese_copywriting_rules.md`，由 `vc validate` 正則強制檢核，不合規者直接阻斷。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：正則表達式校驗腳本，零外部依賴。MIT 協議。
- **故障降級防呆**：提供 `--autofix` 模式自動替換中英文無空格之文字。

### 4.2 kangarooking/copywriters-handbook-skill (文案創作手冊技能)
- **官方/GitHub 連結**：https://github.com/kangarooking/copywriters-handbook-skill
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 蒸餾文案大師 Robert Bly《文案創作手冊》，提煉出 38 種爆款標題公式、FAB (Feature-Advantage-Benefit) 特色利益轉化與 4P 說服模型。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer)
  - **具體職責與合約**：核心技能 `skills/script-copywriter` 之靈魂，負責影片前 3 秒 Hook、痛點共鳴與行動召喚 (CTA) 起草。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：遵循 `skill-creator` 規範之 SKILL.md。MIT 協議。
- **故障降級防呆**：若 Agent 未指定公式，自動套用「提問痛點 + 方案揭露」經典架構。

### 4.3 mikiarlo3/ai-copywriter (AI 文案與去味雙軌)
- **官方/GitHub 連結**：https://github.com/mikiarlo3/ai-copywriter
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 結合文案生成與 Anti-AI Slop（去 AI 味）雙軌演算法，內建維基百科與大型語言模型常見陳腔濫調（如「織錦」、「不可否認」、「綜上所述」）過濾矩陣。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer)
  - **具體職責與合約**：轉化為 `rules/anti_ai_slop.md` 與口語化旁白精煉機制，確保旁白自然流暢具備真人溫度。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：違禁詞黑名單字典與正則過濾器。MIT 協議。
- **故障降級防呆**：命中違禁詞時輸出 WARN 並提供口語化替換建議。

### 4.4 romanticamaj/expression-coach (表達教練與口播節奏)
- **官方/GitHub 連結**：https://github.com/romanticamaj/expression-coach
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 專注於演說表達、抑揚頓挫、停頓 (Cadence) 與重音標記，運用 SCQA (情境-衝突-疑問-回答) 與 PREP 架構管理聽覺注意力。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer)
  - **具體職責與合約**：指導 TTS 旁白生成 SSML 停頓標籤，約束口播單句長度（繁體中文單句建議不超過 35 字）。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：純提示詞與文本節奏標記規範。MIT 協議。
- **故障降級防呆**：若語音引擎不支援 SSML，自動將長句依逗號拆分為多個短音檔。

### 4.5 shibing624/pycorrector (中文文字糾錯工具)
- **官方/GitHub 連結**：https://github.com/shibing624/pycorrector
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 專門針對中文常見錯別字、音似字、形似字進行自動偵測與糾錯，支援規則模式與語言模型混合診斷。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：影片字幕與投影片文本送出前的自動拼寫防呆門禁 (`vc validate --spelling`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.8+, pip install pycorrector。Apache-2.0 協議。
- **故障降級防呆**：模型載入失敗時降級為純字典關鍵字比對。

### 4.6 dair-ai/Prompt-Engineering-Guide (提示工程權威手冊)
- **官方/GitHub 連結**：https://github.com/dair-ai/Prompt-Engineering-Guide
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 業界最權威的提示工程指南，涵蓋 CoT 思考鏈、Least-to-Most、方向性刺激提示與 ReAct 框架。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills)
  - **具體職責與合約**：指導文案編劇 Agent 的內部推導鏈設計，提升生成穩定度。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：知識文檔。CC BY-NC 4.0 協議。
- **故障降級防呆**：無執行期依賴。

### 4.7 f/awesome-chatgpt-prompts (社群精選角色設定庫)
- **官方/GitHub 連結**：https://github.com/f/awesome-chatgpt-prompts
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 收錄大量經實測驗證的角色扮演 Prompt（如技術佈道師、TED 演講者、脫口秀主持人）。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills)
  - **具體職責與合約**：文案角色語氣庫 (`styles/persona_voices/`)，支援透過參數切換講者風格。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：JSON / CSV 格式設定檔。CC0 協議。
- **故障降級防呆**：預設採用中立專業技術工程師語氣。

### 4.8 Shahabks/my-voice-analysis (語音聲學節奏分析庫)
- **官方/GitHub 連結**：https://github.com/Shahabks/my-voice-analysis
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 基於 Praat 聲學引擎，量化分析說話語速 (Syllables/sec)、停頓次數與音高變化率。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：客觀評估旁白音檔是否過於急促或拖沓，作為時間軸對齊前的質量審計。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.8+, Praat binaries, numpy, scipy。MIT 協議。
- **故障降級防呆**：無 Praat 時依音檔長度除以總字數估算粗略語速。

### 4.9 ruanyf/document-style-guide (中文技術文件寫作規範)
- **官方/GitHub 連結**：https://github.com/ruanyf/document-style-guide
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 規範標題、句長、標點、用詞與段落結構，可蒸餾為旁白長度與用詞檢查規則。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules)。對應 `skills/script-copywriter/references/`。
- **安裝/調用前置要求與相依性**：
  - 純 Markdown 文件。
- **故障降級防呆**：缺少時改用內建 `styles/` 與 `skills/` 設定，不阻斷主流程。

### 4.10 jlevy/the-art-of-command-line (命令行藝術極簡寫作)
- **官方/GitHub 連結**：https://github.com/jlevy/the-art-of-command-line
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 極致精煉的技術寫作風格，遵循 ASD-STE100 簡化技術英文與 ISO 24495 明晰語言原則。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules Layer)
  - **具體職責與合約**：技術影片代碼操作步驟解說規範 (`rules/technical_writing_clarity.md`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：文檔規範。CC BY-SA 4.0 協議。
- **故障降級防呆**：無執行期依賴。

---

### 4.11 errata-ai/vale (Vale 可程式化文字風格檢查器)
- **官方/GitHub 連結**：https://github.com/errata-ai/vale
- **類型判定**：【軟體工具/CLI/庫】
- **核心特色與技術架構優勢**：
  - 以 YAML 規則檢查用詞、句長與風格，可套用自訂詞庫。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules)。可取代手寫 lint 規則。
- **安裝/調用前置要求與相依性**：
  - Go 單一執行檔，MIT。
- **故障降級防呆**：缺少時改用內建 `styles/` 與 `skills/` 設定，不阻斷主流程。

## 5. 剪輯、轉碼與母帶合成 (Video Editing, Transcoding & Mastering) [10 專案]

### 5.1 webadderallorg/Recordly (Recordly 螢幕錄影平滑追焦)
- **官方/GitHub 連結**：https://github.com/webadderallorg/Recordly
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 開源 Screen Studio 替代品，核心算法包含滑鼠軌跡平滑指數緩動 (Exponential Easing)、自動視窗追焦 (Auto-Zoom) 與蘋果風格圓角投影。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：螢幕操作錄影增強工具，消除生硬位移，輸出精美特寫視訊，存放於 `external/Recordly`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, Electron, PixiJS。GPL-3.0 協議。
- **故障降級防呆**：無 Recordly 時降級為使用 Remotion 內置的靜態等比縮放與中心居中裁切。

### 5.2 FFmpeg/FFmpeg (FFmpeg 多媒體轉碼核心)
- **官方/GitHub 連結**：https://github.com/FFmpeg/FFmpeg
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 影音處理工業標準，支援 NVIDIA GPU 硬體加速編解碼 (`h264_nvenc`, `hevc_nvenc`)、EBU R128 音訊響度標準化（-16 LUFS 目標）、音視頻分離與無損合流。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline) & 底層轉碼器
  - **具體職責與合約**：全域轉碼核心，位於 `tools/ffmpeg/bin/ffmpeg.exe`，負責所有媒體格式標準化。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：已預先內建於 `tools/ffmpeg/bin/`，零系統依賴。LGPL/GPL 協議。
- **故障降級防呆**：若未偵測到 GPU 驅動，自動平滑降級為 CPU `libx264` 編碼。

### 5.3 Zulko/moviepy (MoviePy 腳本化剪輯庫)
- **官方/GitHub 連結**：https://github.com/Zulko/moviepy
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - Python 影音剪輯模組，支援非線性軌道合成、多音軌混音與批次影片轉換。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：CLI 輕量腳本自動化剪切與無頭批量渲染管道，處理快速影片片段拼接。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, FFmpeg，已安裝於 `.venv`。MIT 協議。
- **故障降級防呆**：複雜合成委由 Remotion 處理，MoviePy 僅作純粹切片。

### 5.4 GuanYixuan/pyJianYingDraft (剪映/CapCut 草稿工程產生器)
- **官方/GitHub 連結**：https://github.com/GuanYixuan/pyJianYingDraft
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 純 Python 庫，逆向並完整支援剪映/CapCut 草稿工程格式 (`draft_content.json`)，可程式化生成多音視頻軌道、關鍵幀、轉場、特效與字幕樣式。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine) & `vc export-jianying`
  - **具體職責與合約**：將專案分鏡直接導出為剪映草稿工程，打通專業剪輯師手動精修最後一哩路。安裝於 `.venv` 並 clone 於 `tools/pyJianYingDraft`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, pip install pyjianyingdraft。MIT 協議。
- **故障降級防呆**：未安裝時降級為輸出標準 Final Cut Pro XML 或純 SRT/MP4。

### 5.5 openai/whisper (Whisper 語音辨識模型)
- **官方/GitHub 連結**：https://github.com/openai/whisper
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - OpenAI 權威語音識別模型，具備強大多語言辨識與抗噪能力。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：錄音檔案轉逐字稿與初步時間軸對齊 (`vc align`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, PyTorch, 模型快取於 `models/`。MIT 協議。
- **故障降級防呆**：無 GPU 時自動採用 CPU 量化模型或調用 OpenAI API。

### 5.6 m-bain/whisperX (WhisperX 音素級對齊)
- **官方/GitHub 連結**：https://github.com/m-bain/whisperX
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 引入 wav2vec2 音素級強制對齊 (Forced Alignment)，達成單字級 (Word-level) 時戳精確度。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：實現畫面元素與旁白單詞毫秒級吸附鎖定（`at_word` 錨點）。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, PyTorch, torchaudio。BSD-4-Clause 協議。
- **故障降級防呆**：未配置音素模型時依字數等比例插值時戳。

### 5.7 Breakthrough/PySceneDetect (PySceneDetect 場景分割)
- **官方/GitHub 連結**：https://github.com/Breakthrough/PySceneDetect
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 基於 OpenCV 的智慧鏡頭場景分割工具，精確偵測內容跳切與淡入淡出。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：參考素材與長螢幕錄影的自動分段切片工具 (`vc ingest-rec`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, OpenCV，已安裝於 `.venv`。BSD-3-Clause 協議。
- **故障降級防呆**：降級為固定時長等分切片。

### 5.8 Auto-Editor/auto-editor (Auto-Editor 智慧跳剪工具)
- **官方/GitHub 連結**：https://github.com/Auto-Editor/auto-editor
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 命令行全自動視訊編輯器，基於音量門限智慧剪除說話停頓與空白間隙。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：粗剪階段的氣口清理，提升影片節奏緊湊感。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, pip install auto-editor。Unlicense 協議。
- **故障降級防呆**：可透過參數 `--margin` 調整保留邊界以防吞音。

### 5.9 yt-dlp/yt-dlp (yt-dlp 多媒體離線採集器)
- **官方/GitHub 連結**：https://github.com/yt-dlp/yt-dlp
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 業界最強多媒體串流下載器，支援高畫質視頻提取與字幕抓取。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：合法離線採集參考素材與樣片。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：獨立可執行二進位，存放於 `tools/`。Unlicense 協議。
- **故障降級防呆**：無網路時使用本地專案既有素材。

### 5.10 Olive-Editor/olive (Olive 開源節點式 NLE)
- **官方/GitHub 連結**：https://github.com/Olive-Editor/olive
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 開源跨平台節點式非線性剪輯軟體，支援 OCIO 色彩管理與 OpenFX 外掛。
- **Video Creator 管線整合定位**：
  - **管線層級**：桌面級工作站整合
  - **具體職責與合約**：高複雜度場景手動校色與後期微調之開源桌面環境代表。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Windows/macOS/Linux 桌面應用。GPL-3.0 協議。
- **故障降級防呆**：桌面可選工具，不影響主管線自動化運行。

---

## 6. 動態圖形、代碼動畫與著色器 (Motion Graphics, Kinetic Code & Shaders) [11 專案]

### 6.1 remotion-dev/remotion (Remotion 程式化影片合成旗艦)
- **官方/GitHub 連結**：https://github.com/remotion-dev/remotion
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 以 React / TypeScript 編寫影格精確的 1080p 影片，強大的彈簧動畫 (`spring`)、數值插值 (`interpolate`) 與音訊響度自動避讓 (Audio Ducking)。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：專案核心母時間軸合成引擎與預覽播放器，存於 `packages/remotion/`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, React 19/18, npm/pnpm。Remotion License。
- **故障降級防呆**：核心致命依賴，必須通過自檢。

### 6.2 remotion-dev/skills (Remotion 官方 Agent 技能庫)
- **官方/GitHub 連結**：https://github.com/remotion-dev/skills
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - Remotion 官方維護之 AI Coding Agent 專用規範，定義組件撰寫範式與避免影格跳躍防呆。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer)
  - **具體職責與合約**：蒸餾為 `skills/remotion-engineering`，指導 Agent 撰寫合規組件。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Markdown 指導規範。MIT 協議。
- **故障降級防呆**：無執行期依賴。

### 6.3 heygen-com/hyperframes (Hyperframes 輕量 HTML 渲染)
- **官方/GitHub 連結**：https://github.com/heygen-com/hyperframes
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - HeyGen 開源之 HTML/CSS/GSAP 輕量級影片渲染引擎，支援無頭 Chromium GPU 加速極速出片。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators)
  - **具體職責與合約**：等軸幾何卡片、純文字動態排版的高速批次渲染器 (`vc hf`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js >= 22, Puppeteer, Chromium。MIT 協議。
- **故障降級防呆**：若 Hyperframes 異常，自動回退使用 Remotion 進行母帶合成。

### 6.4 storytold/effectcraft (EffectCraft 特效合成引擎)
- **官方/GitHub 連結**：https://github.com/storytold/effectcraft
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 純 Rust 開發的 After Effects 開源替代品，內建 731 個引擎指令與 307 種特效。
  - 支援 After Effects JavaScript 物件模型腳本 (`app.project`)，具備原生 CLI 與 MCP 服務。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (Native Rust Creative Suite) & `tools/craft_tools.py`
  - **具體職責與合約**：高效能圖層合成、視覺特效影格渲染 (`effect_render_frame()`) 與無頭影片導出。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Windows x64 獨立可執行檔 (`effectcraft-cli.exe`)，零依賴。商用/開源雙軌。
- **故障降級防呆**：未安裝時降級為 Remotion CSS Keyframe 動畫。

### 6.5 ManimCommunity/manim (Manim 數學幾何動畫引擎)
- **官方/GitHub 連結**：https://github.com/ManimCommunity/manim
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 3Blue1Brown 著名數學幾何動畫引擎，支援精確公式向量繪製與相機變換。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators)
  - **具體職責與合約**：演算法流程圖、數學幾何推導的影片片段產生器 (`vc manim`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, Cairo, FFmpeg，已安裝於 `.venv`。MIT 協議。
- **故障降級防呆**：未配置 LaTeX 時自動使用 SVG 向量圖形替代。

### 6.6 greensock/GSAP (GSAP 業界頂級時間軸動畫庫)
- **官方/GitHub 連結**：https://github.com/greensock/GSAP
- **類型判定**：【軟體工具/CLI/庫（動畫庫）】
- **核心特色與技術架構優勢**：
  - 頂級 JavaScript 動畫標準庫，極致流暢的時間軸序列控制與貝茲曲線緩動。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 & Layer 6 動畫驅動核心
  - **具體職責與合約**：Hyperframes 與網頁動態字卡的核心時間軸驅動器。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js，已安裝於專案 `package.json`。GreenSock License。
- **故障降級防呆**：降級為原生 CSS Animations。

### 6.7 airbnb/lottie-web (Lottie 向量動畫即時渲染)
- **官方/GitHub 連結**：https://github.com/airbnb/lottie-web
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 向量 JSON 動畫渲染器，體積極小且支援無損任意解析度縮放。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：微動態圖標、打勾/警示完成動效之即時播放 (`@remotion/lottie`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：npm install @remotion/lottie lottie-web。MIT 協議。
- **故障降級防呆**：降級為靜態 SVG 圖示。

### 6.8 framer/motion (Framer Motion 物理彈簧動效庫)
- **官方/GitHub 連結**：https://github.com/framer/motion
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - React 生態宣告式物理彈簧動效庫，提供精確自然的手勢與佈局過渡。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：Remotion 元件內部宣告式平滑位移與縮放彈跳效果。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：React 18+, npm install framer-motion。MIT 協議。
- **故障降級防呆**：降級為 Remotion 原生 `spring()` 函數。

### 6.9 mrdoob/three.js (Three.js Web 3D 渲染核心)
- **官方/GitHub 連結**：https://github.com/mrdoob/three.js
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 主流 WebGL / WebGPU 3D 引擎，支援 glTF/GLB 模型載入、PBR 材質與陰影光照。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：3D 產品爆炸圖、立體旋轉展示與空間幾何渲染。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js，npm install three。MIT 協議。
- **故障降級防呆**：無 WebGL 支援時降級為預渲染點陣圖序列。

### 6.10 gl-transitions/gl-transitions (GLSL 著色器轉場庫)
- **官方/GitHub 連結**：https://github.com/gl-transitions/gl-transitions
- **類型判定**：【軟體工具/CLI/庫（Shader 庫兼方法論）】
- **核心特色與技術架構優勢**：
  - 收錄數百種開源 GLSL 著色器硬體轉場效果（Wipe, Zoom, Ripple, CrossWarp）。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：鏡頭切換間的 Shader 硬體級平滑過渡特效 (`@remotion/transitions`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：WebGL 支援環境。MIT 協議。
- **故障降級防呆**：降級為經典 Dissolve 或硬切 (Cut)。

### 6.11 pmndrs/react-three-fiber (R3F 宣告式 3D 畫布)
- **官方/GitHub 連結**：https://github.com/pmndrs/react-three-fiber
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 以 React 元件模型封裝 Three.js，與 Remotion 無縫整合，達成影格精準 3D 渲染。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Master Compositor Layer)
  - **具體職責與合約**：在 Remotion 時間軸中實現逐幀確定性 3D 相機變換。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：React 18+, Three.js。MIT 協議。
- **故障降級防呆**：降級為 2D 向量動畫。

---

## 7. 簡報、排版與向量投影片 (Presentation Slides & Vector Layouts) [11 專案]

### 7.1 hugohe3/ppt-master (PPT Master 原生可編輯簡報產生器)
- **官方/GitHub 連結**：https://github.com/hugohe3/ppt-master
- **類型判定**：【軟體工具/CLI/庫兼方法論】
- **核心特色與技術架構優勢**：
  - AI 驅動將 Markdown/企劃文案轉換為原生可編輯的 `.pptx` 簡報，輸出原生向量形狀 (DrawingML)，非靜態拼貼圖片。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 5 (External Tools Engine)
  - **具體職責與合約**：全自動產出可供演講錄製之標準 PPTX 投影片，存放於 `tools/ppt-master`。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, python-pptx。MIT 協議。
- **故障降級防呆**：若未配置 AI 金鑰，使用本地規則樣板進行形狀佈局。

### 7.2 op7418/guizang-ppt-skill (歸藏簡報設計技能)
- **官方/GitHub 連結**：https://github.com/op7418/guizang-ppt-skill
- **類型判定**：【方法論/提示詞/設計範式】
- **核心特色與技術架構優勢**：
  - 歸藏 PPT 設計技能，內建「雜誌排版×電子墨水」與「瑞士國際主義排版」雙風格系統，產出雜誌級單檔 HTML 簡報。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 2 (Rules & Skills Layer) & `styles/swiss_kinetic/`
  - **具體職責與合約**：蒸餾為技術字卡與簡報視覺排版 skills (`skills/guizang-slide-stylist`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：純 CSS/HTML 模板與提示詞，零外部依賴。MIT 協議。
- **故障降級防呆**：無執行期依賴。

### 7.3 marp-team/marp (Marp Markdown 簡報引擎)
- **官方/GitHub 連結**：https://github.com/marp-team/marp
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - Markdown 簡報生態標準，基於 CSS 主題將 Markdown 轉化為 16:9 高清投影片，支援批次導出 1080p PNG 序列圖片。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators) & `tools/marp-cli`
  - **具體職責與合約**：腳本分鏡與技術投影片的批次抽幀匯入管線 (`vc ingest-ppt`)。整合至 `package.json` (`devDependencies` 與 `scripts.marp`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, npm install -D @marp-team/marp-cli。MIT 協議。
- **故障降級防呆**：**重要防呆**：子行程呼叫時**必須附加 `--no-stdin`** 旗標以防行程掛起。

### 7.4 reveal/reveal.js (Reveal.js 經典 HTML 簡報框架)
- **官方/GitHub 連結**：https://github.com/reveal/reveal.js
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 成熟的 HTML 簡報框架，支援 2D 矩陣切換、代碼高亮與碎片動畫 (Fragments)。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators)
  - **具體職責與合約**：互動性 HTML 簡報展示與無頭截圖抽幀。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js, npm。MIT 協議。
- **故障降級防呆**：降級為純靜態 HTML 預覽。

### 7.5 slidevjs/slidev (Slidev 開發者互動簡報框架)
- **官方/GitHub 連結**：https://github.com/slidevjs/slidev
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - Vue 3 驅動之開發者簡報神器，原生支援 LaTeX 數學公式、UnoCSS 與行內代碼動態演繹。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators)
  - **具體職責與合約**：深度技術代碼示範與動態公式投影片抽幀。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Node.js 18+, Vue 3。MIT 協議。
- **故障降級防呆**：降級為 Marp Markdown 渲染。

### 7.6 scanny/python-pptx (python-pptx 投影片操作核心庫)
- **官方/GitHub 連結**：https://github.com/scanny/python-pptx
- **類型判定**：【軟體工具/CLI/庫（庫）】
- **核心特色與技術架構優勢**：
  - Python 操作 PPTX 檔案的經典標準庫，支援創建形狀、文字框、表格與幾何圖形。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 3 (Core CLI Pipeline)
  - **具體職責與合約**：Python 端全自動解析與產生投影片的底層庫 (`vc/ppt_parser.py`)。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Python 3.10+, pip install python-pptx，已安裝於 `.venv`。MIT 協議。
- **故障降級防呆**：解析損壞投影片時自動跳過並發出 WARN。

### 7.7 gnab/remark (Remark 極簡瀏覽器幻燈片)
- **官方/GitHub 連結**：https://github.com/gnab/remark
- **類型判定**：【軟體工具/CLI/庫/微服務】
- **核心特色與技術架構優勢**：
  - 極簡 Markdown 幻燈片工具，零打包建置依賴，單一 HTML 即可即刻播放。
- **Video Creator 管線整合定位**：
  - **管線層級**：輕量預覽工具
  - **具體職責與合約**：無網路極端環境下的輕量文字卡片播放演練。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：純 JavaScript。MIT 協議。
- **故障降級防呆**：無外部依賴。

### 7.8 antfu/vscode-slidev (VS Code Slidev 擴充外掛)
- **官方/GitHub 連結**：https://github.com/slidevjs/slidev
- **類型判定**：【軟體工具/CLI/庫（IDE 擴展）】
- **核心特色與技術架構優勢**：
  - VS Code 內嵌 Slidev 所見即所得分鏡預覽與導航。
- **Video Creator 管線整合定位**：
  - **管線層級**：開發者環境擴充
  - **具體職責與合約**：創作者本地編寫與預覽簡報分鏡之互動介面。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：VS Code。MIT 協議。
- **故障降級防呆**：純外掛，不影響主管線。

### 7.9 gitbrent/PptxGenJS (PptxGenJS 瀏覽器與 Node PPTX 產生庫)
- **官方/GitHub 連結**：https://github.com/gitbrent/PptxGenJS
- **類型判定**：【軟體工具/CLI/庫】
- **核心特色與技術架構優勢**：
  - 以 JavaScript 產生可編輯 .pptx，支援圖表、表格與母片。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Slides)。作為 ppt-master 以外的 JS 後備路徑。
- **安裝/調用前置要求與相依性**：
  - Node 18+，MIT。
- **故障降級防呆**：缺少時改用內建 `styles/` 與 `skills/` 設定，不阻斷主流程。

### 7.10 bento-grid-slides / DeckCraft (Bento Grid 佈局與純 Rust PPTX 渲染)
- **官方/GitHub 連結**：https://github.com/topics/bento-grid
- **類型判定**：【方法論/提示詞/設計範式 兼 本地 Rust 工具】
- **核心特色與技術架構優勢**：
  - 現代科技簡報與 Apple 發表會必備之 Bento Grid 便當盒模組化佈局。
  - 深度整合本地純 Rust 打造之 `DeckCraft` 渲染引擎 (`deckcraft-cli.exe`)，無須微軟 PowerPoint COM 組件即可將 `.pptx` 秒級渲染為 1920x1080 圖片序列。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 4 (Clip Generators) & Layer 5 (Native Rust Creative Suite)
  - **具體職責與合約**：蒸餾為 `skills/bento-slide-architect` 佈局技能，並由 `tools/craft_tools.py` 驅動 `DeckCraft` 無頭出圖。
- **安裝/調用前置要求與相依性**：
  - **語言與執行期**：Windows x64 獨立可執行檔 (`deckcraft-cli.exe`)，零外部依賴。商用/開源雙軌。
- **故障降級防呆**：若未檢測到 DeckCraft，自動回退使用 Marp 或 python-pptx 產出圖片。

---

### 7.11 quarto-dev/quarto-cli (Quarto 出版與簡報系統)
- **官方/GitHub 連結**：https://github.com/quarto-dev/quarto-cli
- **類型判定**：【軟體工具/CLI/庫】
- **核心特色與技術架構優勢**：
  - 由 Markdown 輸出 reveal.js、PPTX、PDF 簡報。
- **Video Creator 管線整合定位**：
  - **管線層級**：Layer 6 (Slides)。
- **安裝/調用前置要求與相依性**：
  - 單一安裝包，MIT。
- **故障降級防呆**：缺少時改用內建 `styles/` 與 `skills/` 設定，不阻斷主流程。

## 8. 跨領域整合矩陣與落地指南 (Cross-Domain Integration Matrix & Toolchain Blueprint)

### 8.1 外部工具鏈分層存放規範 (tools/ vs external/ vs skills/ vs rules/)
為確保整個專案目錄職責清晰、可維護性高且不會引起 Git 追蹤膨脹，本專案實施嚴格的分層落地規範：

| 存放目錄 | 納入標準 | 管理方式 | 典型代表 |
|---|---|---|---|
| **`skills/`** | 遵循 `skill-creator` 規範之行為能力、角色提示詞與漸進揭露知識 | Git 完整版本控制（包含 `SKILL.md`, `references/`） | `style-director/`, `script-copywriter/`, `camera-pacing-director/` |
| **`rules/`** | 全域硬性門禁規則、正則約束、排版規範與雙代理評審協議 | Git 完整版本控制（純 Markdown 規範） | `chinese_copywriting_rules.md`, `anti_ai_slop.md`, `egm_review_protocol.md` |
| **`tools/`** | 輕量、綠色二進位檔或純 Python 核心擴充庫 | 綠色軟體直接放置或 git clone (輕量) | `tools/ffmpeg/bin/`, `tools/pyJianYingDraft/`, `tools/ppt-master/`, `tools/craft_tools.py` |
| **`external/`** | 大型桌面 GUI 應用、Electron 應用或獨立微服務後台 | 獨立目錄管理，建議 shallow clone 或獨立環境 | `external/Recordly/`, `external/ComfyUI/` |
| **`styles/`** | 視覺主題包（Design Tokens, CSS 變數, Jinja2 樣板） | Git 完整版本控制 | `executive_navy/`, `swiss_kinetic/`, `blueprint/` |

### 8.2 本地 Rust 創意工具四重奏 (EffectCraft, PhotoCraft, VectorCraft, DeckCraft) 聯動手冊

在 `D:\Ikaros\Office_adobe_CAD` 目錄下已配備純 Rust 編譯之高效能創意工具鏈。透過 `vc/craft_tools.py` 與 `tools/craft_tools.py` 封裝，實現「零微軟 Office 依賴、零 Adobe 授權負擔、極速 GPU 批次處理」：

```text
                      [Office_adobe_CAD Rust Creative Suite]
                                       │
     ┌──────────────────┬──────────────┴─────┬──────────────────┐
     ▼                  ▼                    ▼                  ▼
[DeckCraft]       [EffectCraft]        [PhotoCraft]       [VectorCraft]
(v0.8.0)          (v0.11.1)            (v0.10.0)          (v0.13.1)
  │                  │                    │                  │
  ├─ PPTX/Deckcraft  ├─ AE 腳本/合成      ├─ PSD 圖層替換     ├─ SVG/AI/CAD 解析
  ├─ 1080p 秒級抽幀  ├─ 307 種特效渲染   ├─ 批次裁切去背    ├─ 無損向量點陣化
  └─ 格式雙向互轉   └─ H264/HEVC/ProRes  └─ JSON 圖層樹導出 └─ MCP 服務介接
```

#### 呼叫規範與核心 API 對照表：
1. **DeckCraft (`deck_render_slides`)**：
   ```python
   from vc.craft_tools import deck_render_slides
   slides = deck_render_slides(pptx_path=Path("input.pptx"), out_dir=Path("out/"), scale=2)
   # 自動導出 1920x1080 高畫質 PNG 投影片序列
   ```
2. **EffectCraft (`effect_render_frame`)**：
   ```python
   from vc.craft_tools import effect_render_frame
   effect_render_frame(proj_path=Path("template.ectemplate"), out_png=Path("frame.png"), demo=True)
   ```
3. **PhotoCraft (`photo_convert` / `photo_info`)**：
   ```python
   from vc.craft_tools import photo_info, photo_convert
   tree = photo_info(Path("cover.psd"))  # 取得圖層樹
   photo_convert(Path("cover.psd"), Path("cover.png"), quality=95)
   ```
4. **VectorCraft (`vector_convert`)**：
   ```python
   from vc.craft_tools import vector_convert
   vector_convert(Path("arch.svg"), Path("arch.png"), scale=2.0)
   ```

### 8.3 核心工具相依性與環境前置檢核表

為供自動化檢查腳本 (`scripts/verify_tools.py`) 實施階層式相依性稽核，定義三級相依矩陣：

| 相依等級 | 檢查項目 | 判定標準 | 失敗後果 |
|---|---|---|---|
| **Tier 1: Core Required (核心致命)** | Python 執行期 | `3.10 <= Version <= 3.12` | 退出碼 1，管線完全無法啟動 |
| | Node.js 執行期 | `Node.js >= 22.0.0` (HyperFrames 必要條件) | 退出碼 1，無法渲染動態字卡 |
| | FFmpeg 轉碼器 | 可執行且具備 `libx264` 與 `aac` 編碼器 | 退出碼 1，無法合流音視頻 |
| **Tier 2: Pipeline Core (管線整合)** | pyJianYingDraft | `import pyjianyingdraft` 成功或本地目錄就緒 | 標記 WARN，剪映草稿降級為純 MP4 |
| | Marp CLI | `npx @marp-team/marp-cli --version` 通過 | 標記 WARN，簡報抽幀降級 |
| | OfficeCraft Suite | EffectCraft, PhotoCraft, VectorCraft, DeckCraft CLI 可用 | 標記 WARN，自動降級為 Node/Python 替代方案 |
| | craft_tools.py | `vc/craft_tools.py` 封裝模組存在且可匯入 | 標記 WARN，Rust 工具介面不可調用 |
| **Tier 3: Extended / Opt (擴充優化)** | Recordly | `external/Recordly/package.json` 存在 | 標記 WARN，錄影追焦降級為中心居中裁切 |
| | ppt-master | `tools/ppt-master/README.md` 存在 | 標記 WARN，簡報生成降級為純文字 |
| | FFmpeg NVENC | `h264_nvenc` 編碼測試通過 | 標記 WARN，硬體加速回退至 CPU libx264 |

### 8.4 開源協議相容性與商用合規分析 (License Compliance)

所有收錄工具經法務與開源架構審核，確保本專案商用自由度：
- **寬鬆授權 (MIT, Apache-2.0, ISC, BSD, CC0)**：涵蓋 85% 以上專案（如 `remotion-skills`, `chaojifeng-video-design`, `chinese-copywriting-guidelines`, `pyJianYingDraft`, `ppt-master`），允許自由修改、閉源整合與商用發布。
- **強傳染性開源 (GPL-3.0 / AGPL-3.0)**：如 `Recordly`, `ComfyUI`。**處置方針**：將其嚴格隔離於 `external/` 目錄或透過獨立 CLI/HTTP REST 行程進行跨行程通訊 (IPC)，本專案主核心代碼不與其直接靜態連結，確保本專案主架構不受 GPL 傳染性波及。
- **商用雙軌/專有授權**：如 `Remotion`（小型團隊/個人免費，大企業需商用授權）、`Office_adobe_CAD`（本機專屬授權二進位），皆符合內部研發管線規範。

---

## 附錄：專案名稱與代碼快速索引 (Quick Reference Index)

| 編號 | 專案標識 | 領域名稱 | 類型判定 | 落地路徑 |
|---|---|---|---|---|
| 1-01 | `mileson/chaojifeng-video-design` | 影片設計 | 方法論 | `skills/camera-pacing-director/` |
| 1-02 | `lemomo-ai/lemo-opuscar` | 影片設計 | 方法論 | `styles/`, `skills/style-director/` |
| 1-03 | `wheresryan22/anatomy` | 影片設計 | 方法論 | `skills/isometric-anatomy/` |
| 1-04 | `google/elephant-goldfish-model` | 影片設計 | 方法論 | `rules/egm_review_protocol.md` |
| 1-05 | `FujiwaraChoki/MoneyPrinter` | 影片設計 | 工具庫 | `external/MoneyPrinter/` |
| 1-06 | `hpcaitech/Open-Sora` | 影片設計 | 工具庫 | `external/Open-Sora/` |
| 1-07 | `THUDM/CogVideo` | 影片設計 | 工具庫 | `external/CogVideo/` |
| 1-08 | `comfyanonymous/ComfyUI` | 影片設計 | 工具庫 | `external/ComfyUI/` |
| 1-09 | `Huanshere/VideoLingo` | 影片設計 | 工具庫 | `external/VideoLingo/` |
| 1-10 | `RayVentura/ShortGPT` | 影片設計 | 工具庫 | `external/ShortGPT/` |
| 1-11 | `storytold/artcraft` | 影片設計 | 工具庫 | `tools/craft_tools.py` |
| 2-01 | `meta/astryx` | 視覺美術 | 混合型 | `packages/remotion/` |
| 2-02 | `nexu-io/open-design` | 視覺美術 | 工具庫 | `external/open-design/` |
| 2-03 | `storytold/photocraft` | 視覺美術 | 工具庫 | `tools/craft_tools.py` |
| 2-04 | `KenneyNL/Adobe-Alternatives` | 視覺美術 | 方法論 | 參考索引 |
| 2-05 | `tailwindlabs/tailwindcss` | 視覺美術 | 工具庫 | `packages/remotion/` |
| 2-06 | `radix-ui/primitives` | 視覺美術 | 工具庫 | `packages/remotion/` |
| 2-07 | `lucide-icons/lucide` | 視覺美術 | 資產庫 | `packages/remotion/` |
| 2-08 | `adobe-fonts/source-han-sans` | 視覺美術 | 資產庫 | `assets/fonts/` |
| 2-09 | `anthropics/prompt-eng-tutorial` | 視覺美術 | 方法論 | `skills/style-director/` |
| 2-10 | `tabler/tabler-icons` | 視覺美術 | 資產庫 | `packages/remotion/` |
| 3-01 | `sparanoid/chinese-copywriting-guidelines` | 文案敘事 | 方法論 | `rules/chinese_copywriting_rules.md` |
| 3-02 | `kangarooking/copywriters-handbook-skill` | 文案敘事 | 方法論 | `skills/script-copywriter/` |
| 3-03 | `mikiarlo3/ai-copywriter` | 文案敘事 | 方法論 | `rules/anti_ai_slop.md` |
| 3-04 | `romanticamaj/expression-coach` | 文案敘事 | 方法論 | `skills/script-copywriter/` |
| 3-05 | `shibing624/pycorrector` | 文案敘事 | 工具庫 | `vc validate --spelling` |
| 3-06 | `dair-ai/Prompt-Engineering-Guide` | 文案敘事 | 方法論 | 知識手冊 |
| 3-07 | `f/awesome-chatgpt-prompts` | 文案敘事 | 方法論 | `styles/persona_voices/` |
| 3-08 | `Shahabks/my-voice-analysis` | 文案敘事 | 工具庫 | `vc/audio_analyzer.py` |
| 3-09 | `storytelling-frameworks` | 文案敘事 | 方法論 | `skills/script-copywriter/` |
| 3-10 | `jlevy/the-art-of-command-line` | 文案敘事 | 方法論 | `rules/technical_writing_clarity.md` |
| 4-01 | `webadderallorg/Recordly` | 剪輯合成 | 工具庫 | `external/Recordly/` |
| 4-02 | `FFmpeg/FFmpeg` | 剪輯合成 | 工具庫 | `tools/ffmpeg/bin/` |
| 4-03 | `Zulko/moviepy` | 剪輯合成 | 工具庫 | `.venv` |
| 4-04 | `GuanYixuan/pyJianYingDraft` | 剪輯合成 | 工具庫 | `tools/pyJianYingDraft/`, `.venv` |
| 4-05 | `openai/whisper` | 剪輯合成 | 工具庫 | `.venv`, `models/` |
| 4-06 | `m-bain/whisperX` | 剪輯合成 | 工具庫 | `.venv` |
| 4-07 | `Breakthrough/PySceneDetect` | 剪輯合成 | 工具庫 | `.venv` |
| 4-08 | `Auto-Editor/auto-editor` | 剪輯合成 | 工具庫 | `.venv` |
| 4-09 | `yt-dlp/yt-dlp` | 剪輯合成 | 工具庫 | `tools/yt-dlp.exe` |
| 4-10 | `Olive-Editor/olive` | 剪輯合成 | 工具庫 | 桌面工作站 |
| 5-01 | `remotion-dev/remotion` | 動態設計 | 工具庫 | `packages/remotion/` |
| 5-02 | `remotion-dev/skills` | 動態設計 | 方法論 | `skills/remotion-engineering/` |
| 5-03 | `heygen-com/hyperframes` | 動態設計 | 工具庫 | `hyperframes/` |
| 5-04 | `storytold/effectcraft` | 動態設計 | 工具庫 | `tools/craft_tools.py` |
| 5-05 | `ManimCommunity/manim` | 動態設計 | 工具庫 | `.venv` |
| 5-06 | `greensock/GSAP` | 動態設計 | 工具庫 | `node_modules` |
| 5-07 | `airbnb/lottie-web` | 動態設計 | 工具庫 | `packages/remotion/` |
| 5-08 | `framer/motion` | 動態設計 | 工具庫 | `packages/remotion/` |
| 5-09 | `mrdoob/three.js` | 動態設計 | 工具庫 | `packages/remotion/` |
| 5-10 | `gl-transitions/gl-transitions` | 動態設計 | 工具庫 | `@remotion/transitions` |
| 5-11 | `pmndrs/react-three-fiber` | 動態設計 | 工具庫 | `packages/remotion/` |
| 6-01 | `hugohe3/ppt-master` | 簡報排版 | 混合型 | `tools/ppt-master/` |
| 6-02 | `op7418/guizang-ppt-skill` | 簡報排版 | 方法論 | `skills/guizang-slide-stylist/` |
| 6-03 | `marp-team/marp` | 簡報排版 | 工具庫 | `package.json`, CLI |
| 6-04 | `reveal/reveal.js` | 簡報排版 | 工具庫 | `node_modules` |
| 6-05 | `slidevjs/slidev` | 簡報排版 | 工具庫 | `node_modules` |
| 6-06 | `scanny/python-pptx` | 簡報排版 | 工具庫 | `.venv` |
| 6-07 | `gnab/remark` | 簡報排版 | 工具庫 | 靜態資產 |
| 6-08 | `antfu/vscode-slidev` | 簡報排版 | 工具庫 | IDE 擴展 |
| 6-09 | `presentation-design-patterns` | 簡報排版 | 方法論 | `rules/presentation_design_rules.md` |
| 6-10 | `bento-grid-slides` (DeckCraft) | 簡報排版 | 混合型 | `tools/craft_tools.py`, `skills/` |

---
*本手冊由 Video Creator 專案架構小組編纂，遵循 Loop Engineering 6.0 與規格驅動原則。*
