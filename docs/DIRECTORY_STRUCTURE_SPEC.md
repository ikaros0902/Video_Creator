# Video Creator 目錄結構規範與架構手冊 (DIRECTORY_STRUCTURE_SPEC.md)

---

## 1. 架構全景視圖 (Architecture Overview)

Video Creator 是一套採用「高密度規格驅動（Spec-Driven Development）」與「確定性影格合成」的自動化影片生產管線。系統架構分為 7 大核心分層，各分層邊界清晰、資料流向單向確定：

```text
[Input Layer]
  projects/<name>/input/ (slides, recordings, audio, assets) + project.yaml + facts.yaml + script.json
        │
        ▼
[Rules & Skills Layer (skill-creator compliant)]
  skills/ (style-director, script-copywriter, camera-pacing-director, etc.)
  rules/  (chinese_copywriting, anti_ai_slop, egm_review, etc.)
  styles/ (executive_navy, swiss_kinetic, blueprint, isometric)
        │
        ▼
[Core CLI Pipeline Layer]
  vc (ingest-ppt, ingest-rec, voice, align, plan, fit, hf, manim, render)
        │
        ├──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼
[Clip Generators]       [Clip Generators]       [External Tools Engine]
  HyperFrames (HTML/GSAP) Manim (GPU NVENC)      tools/ (Recordly, pyJianYingDraft,
                                                        Marp, PhotoCraft, EffectCraft)
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                                ▼
[Master Compositor Layer]
  remotion/ (React 19, ANGLE GPU, EBU R128 Ducking, Frame-Accurate Timeline)
                                │
                                ▼
[Standardized Output Layer]
  projects/<name>/output/ (internal/, public/, reports/)
```

### 目錄設計核心原則

1. **高內聚性（High Cohesion）**：相同功能維度之代碼、規則、技能與樣板集中存放於專屬領域目錄中，邊界嚴格封裝。
2. **自包含可移植（Self-Contained & Portable）**：每個影片專案（`projects/<name>/`）皆具備獨立且完整的 `input/`、`work/` 與 `output/` 結構，嚴禁向外逃逸引用上層相對路徑。任何專案目錄均可完整打包移植至其他工作環境運行。
3. **單一真值來源（Single Source of Truth, SSOT）**：分鏡腳本 `script.json` 與事實真相表 `facts.yaml` 為全管線渲染與斷言的唯一真值來源，禁止散落硬編碼數據。
4. **零跨目錄逃逸（Zero Directory Escapes）**：徹底廢棄歷史根目錄 `Videos/` 跨目錄相對路徑依賴（如 `../../Videos/...`），全面消滅代碼與配置檔中的越界參照。

---

## 2. 目錄架構完整清單與職責定義 (Directory Responsibilities)

重構後的標準專案結構如下：

```text
d:\Ikaros\Video_Creator/
├── docs/                     # 專案規範、架構設計、使用者操作手冊與外部參考索引
├── rules/                    # 全域硬性規範（中文文案排版、反 AI 空洞詞彙、EGM 評審門禁）
├── workflows/                # BMAD + BDD 開發生命週期與影片製作 SOP 指引
├── skills/                   # 核心技能庫（遵循 skill-creator 規範，三層漸進揭露）
│   ├── style-director/       # 視覺美術風格技能
│   ├── script-copywriter/    # 文案腳本創作技能
│   ├── camera-pacing-director/# 鏡頭運鏡節奏技能
│   ├── guizang-slide-stylist/# 簡報排版技能
│   ├── remotion-engineering/ # Remotion 程式碼工程技能
│   └── isometric-anatomy/    # 等軸幾何剖析技能
├── styles/                   # 視覺主題包與 Design Tokens（executive_navy, swiss_kinetic, blueprint 等）
├── assets/                   # 全域共用資產庫（不可變唯讀素材）
│   ├── brand/                # 企業、合作夥伴與開源專案向量/高清 Logo
│   └── templates/            # 共用視覺底圖、網格紋理與通用免版稅配樂 (BGM)
│       ├── backgrounds/      # 共用背景圖 (bg_navy_glow.jpg, bg_navy_grid.jpg)
│       └── audio/            # 共用音訊素材 (bgm_midsurface.mp3, bgm.mp3)
├── packages/                 # 整合式單元包
│   └── remotion/             # Remotion React 19 合成母時間軸專案 (npm workspaces 管理)
├── tools/                    # 免安裝綠色二進位與專案工具鏈 (FFmpeg, Recordly, pyJianYingDraft 等)
├── external/                 # 大型外部輔助微服務 (ComfyUI, VideoLingo 等)
├── models/                   # 本機 AI 模型快取 (Kokoro 82M, Whisper small.en.pt)，隔離於系統路徑外
├── projects/                 # 自包含影片創作專案實例
│   ├── _sample/              # 標準公開測試示範專案
│   ├── _sample_exec/         # 執行期測試示範專案
│   └── <project_name>/       # 自訂影片專案 (自包含 input, work, output)
├── tests/                    # BDD feature 規格、單元測試與測試夾具
│   └── fixtures/             # 整合測試夾具 (含 hyperframes_smoke 等)
├── scripts/                  # 自動化環境配置 (setup.ps1)、模型檢驗與維護腳本
├── archive/                  # 歷史專案與大型素材封存庫 (受 .gitignore 保護)
│   └── Videos/               # 封存之歷史大型影片素材目錄 (歷史專案成品與原始錄影)
├── vc/                       # 核心 Python CLI 工具庫 (python -m vc <subcommand>)
├── package.json              # Monorepo 根目錄 package.json (npm workspaces 整合管理)
└── .gitignore                # 完整版本庫排除規則
```

### 各目錄核心職責說明

- **`docs/`**：收錄專案架構手冊、目錄規範、使用者操作指南以及各領域調研索引。本目錄為團隊協同與外部交付之官方文件專區。
- **`rules/`**：存放不可踰越的靜態文字與代碼約束規則，如繁體中文排版規則（Sparanoid）、AI 語氣過濾清單、ASD-STE100 淺白英文與 EGM 審核門禁。
- **`workflows/`**：規範影片生產的端到端 SOP（從 Brief、Ingest、Scripting 到 Master Render）以及 BMAD + BDD 軟體工程工作流程。
- **`skills/`**：遵循 `skill-creator` 規範打造的標準 Agent 技能庫。每個 Skill 均具備合規的 YAML frontmatter、三層漸進揭露架構（SKILL.md、scripts/、references/），可獨立被 AI Agent 調度。
- **`styles/`**：管理跨場景的視覺風格主題包。包含配色變數（Design Tokens）、Jinja2 動態 HTML 模板、字體定義與卡片視覺規範。
- **`assets/`**：集中存放全專案通用的品牌標誌（`assets/brand/`）、背景圖庫（`assets/templates/backgrounds/`）與配樂庫（`assets/templates/audio/`）。所有專案均可唯讀參照，避免重複儲存大檔。
- **`packages/`**：以 Monorepo 形式管理前端與 Node 服務。包含 `packages/remotion`（React 19 母時間軸合成器），透過根目錄 npm workspaces 達成統一一鍵安裝與指令轉發。
- **`tools/`**：存放免安裝的獨立工具二進位或獨立腳本，例如專用版 FFmpeg 套件、Recordly 運鏡追焦工具、pyJianYingDraft 剪映草稿匯出介面與 Marp CLI 簡報轉換工具。
- **`external/`**：收納大型外部工具或微服務整合模組，如 ComfyUI 擴充、VideoLingo 語音管線等。
- **`models/`**：封裝本機 AI 推論所需的模型權重檔（如 Kokoro 語音合成模型、Whisper 逐字對齊模型），確保執行環境隔離且支援完全離線運算。
- **`projects/`**：自包含影片創作的實例目錄。每個專案資料夾獨立管理其 `input/`、`work/` 與 `output/`，專案內部設定檔（`project.yaml`、`facts.yaml`、`script.json`）均遵循標準規範。
- **`tests/`**：管理所有自動化測試，包含 BDD Gherkin 特徵檔、pytest 測試腳本與整合測試夾具（`tests/fixtures/`）。
- **`scripts/`**：存放開發維護、環境自動建置（如 Windows 憑證設定、依賴下載）與發布打包腳本。
- **`archive/`**：封存不再直接參與生產管線之歷史大型專案與素材（如前期專案輸出之十餘 GB 視訊檔案），排除於 Git 版本庫之外以維持倉庫輕量。
- **`vc/`**：Video Creator 的核心 CLI Python 套件，提供 `python -m vc <subcommand>` 完整命令列介面。

---

## 3. 廢棄與整併對照表 (Deprecation & Migration Matrix)

本專案於 Milestone 1 執行 14 項廢棄、重新命名與整併措施，全面淘汰混亂的歷史前綴與逃逸依賴：

| # | 舊目錄 / 歷史路徑 | 新標準目錄 / 路徑 | 處理動作 | 遷移與重構理由 |
|---|---|---|---|---|
| 1 | `00_docs/` | `docs/` | 重新命名與整併 | 消除非標準的數字編號前綴，對齊現代開源軟體專案與文檔結構標準。 |
| 2 | `01_rules/` | `rules/` | 重新命名 | 消除數字編號前綴，確立全域硬性約束規則庫之獨立地位。 |
| 3 | `02_workflows/` | `workflows/` | 重新命名 | 消除數字編號前綴，標準化影片生產生命週期流程與 SOP 指引。 |
| 4 | `03_skills/` | `skills/` | 規範化重構 | 消除數字前綴，全數技能依據 `skill-creator` 規範進行三層式漸進揭露標準化重構。 |
| 5 | `04_styles/` | `styles/` | 重新命名與解耦 | 消除數字前綴，將硬編碼樣板自 Python 代碼中完全解耦為獨立 Jinja2 樣式主題包。 |
| 6 | `05_references/` | `docs/references/` | 整併入文檔專區 | 轉化為架構參考、開源生態調研報告與外部技術評估的專業文檔目錄。 |
| 7 | `06_projects/` | `projects/` | 遷移並設相容層 | 建立自包含目錄標準；歷史路徑由 `vc/project.py` 雙軌向後相容層無痛支持。 |
| 8 | `07_features/` & `08_tests/` | `tests/` | 整併對齊 pytest | 消除分離的前綴結構，整合為標準 `tests/` 目錄，對齊 pytest 慣例。 |
| 9 | `09_scripts/` | `scripts/` | 重新命名 | 消除數字前綴，集中收納環境安裝、快取配置與維護腳本。 |
| 10 | `Videos/Midsuface/` | `projects/midsurface/input/` | 遷移並更正錯字 | 修正歷史錯別字（`Midsuface` → `midsurface`），專案素材自包含歸入 `input/`。 |
| 11 | `Videos/Templates/` | `assets/templates/` & `assets/brand/` | 分類抽離集中化 | 消除根目錄全局雜亂資料夾，建立結構清晰、不可變的集中共用素材庫。 |
| 12 | `Videos/<legacy_projects>/` | `archive/Videos/` | 封存並加入 gitignore | 將逾 12 GB 之歷史獨立成品與錄影移至封存庫，根目錄徹底淨化。 |
| 13 | `remotion/` | `packages/remotion/` | 納入 npm workspaces | 整合至根目錄 `package.json` 的 npm workspaces 管理，實現統一依賴調度與腳本執行。 |
| 14 | `hyperframes/smoke` | `tests/fixtures/hyperframes_smoke/` | 遷移至測試夾具 | 清理根目錄遺留之臨時測試產物，根目錄不再留存非標準殘留資料夾。 |

---

## 4. 核心工具定位與職責分界 (Core Tool Architecture)

Video Creator 在影格渲染層面嚴格劃分 Remotion 與 Hyperframes 的職責邊界，防止職能重疊與架構腐化：

### 4.1 Remotion：Master Compositor（總合成器）

- **架構定位**：全片時間軸裁定者與最終主合成裝配引擎。
- **技術棧**：React 19、`@remotion/cli`、ANGLE 硬體加速（WebGL / Chromium GPU）。
- **核心職責**：
  1. **時間軸精確組裝**：讀取 `work/timeline.json`，精確調度全片音畫同步（Frame-Accurate Alignment）。
  2. **主音軌混音與 Ducking**：依據語音時間戳與 EBU R128 標準，在旁白出現時自動壓低背景音樂（-14 dB 衰減），在語音停頓時間平滑拉升音量。
  3. **動態字幕渲染（Cues）**：依據 Whisper 逐字對齊之毫秒時間戳，即時渲染高對比雙語/英文高亮字幕。
  4. **多軌合成與鏡頭轉場**：將螢幕錄影（Recording）、向量動態字卡（Hyperframes / Manim 輸出之片段）與邊框遮罩合成至最終 1080p 畫面。
  5. **雙軌分流匯出**：依據參數分別渲染內部版（`internal`，保留錄影細節）與公開版（`public`，純向量與動態圖表脫敏）。
- **調用方式**：由 Python 管線 `python -m vc render <project>` 自動調用，或開發階段透過 `npm run remotion:studio` 啟動瀏覽器即時互動除錯。

### 4.2 Hyperframes：Dynamic Card Generator（動態卡片生成器）

- **架構定位**：高精細度、輕量級動態資訊圖表與概念卡片片段產生器。
- **技術棧**：HTML5 Canvas / DOM、GSAP 3（GreenSock）、Node.js CLI。
- **核心職責**：
  1. **獨立動態片段生成**：專門產出核心概念步驟卡（`steps4`）、架構對比卡（`cards3`）、數據指標卡（`chassis_mock`）等精緻動態卡片。
  2. **微觀影格同步**：支援與腳本關鍵字（`at_word` / `at_frames`）精準同步的 CSS/GSAP 動畫效果。
  3. **獨立中間產物交付**：輸出中間 MP4 片段至 `work/hf/<variant>/<scene>.mp4`，不負責全片長度裁定或最終音訊壓制。
- **調用方式**：由 Python 管線 `python -m vc hf <project>` 自動驅動樣板編譯與無頭渲染，渲染完成後交付 Remotion 合成。

---

## 5. 跨目錄依賴消除原則與資產共用標準 (Asset Sharing Standards)

為確保專案庫的可維護性、可移植性與長期架構健康度，全體開發者與 AI 代理人必須嚴格遵循以下三大資產共用原則：

### 原則一：專案邊界不逃逸（Project Sandboxing）

- 專案內部設定檔（`project.yaml`、`script.json` 等）嚴禁出現 `../../` 等向上逃逸路徑。
- 專案所有專屬素材（PPTX、錄影、專用配音、專案截圖）必須放置於該專案的 `input/` 子目錄內（`input/slides/`、`input/recordings/`、`input/audio/`、`input/assets/`）。
- 任何產物（中間轉碼檔、對齊資訊、暫存圖檔）一律僅能寫入該專案的 `work/` 與 `output/` 目錄。

### 原則二：共用資產不可變（Read-Only Shared Assets）

- 全專案通用的品牌標誌、商標圖標、共用背景紋理與全域 BGM 統一收錄於 `assets/` 目錄。
- 專案引用全域資產時採唯讀參照；若專案需對資產進行破壞性修改或特定調色，必須於 Ingest 階段複製一份複本至該專案之 `input/assets/` 中維護，嚴禁直接修改全域 `assets/` 原始檔案。

### 原則三：優雅向後相容（Graceful Backward Compatibility）

- `vc/project.py` 中的專案解析層實施雙軌階梯探測（優先搜尋 `projects/<name>`，fallback 搜尋 `06_projects/<name>`）。
- 素材解析函數 `_resolve(rel)` 實作智能自愈機制：若歷史專案引用了 `../../Videos/Midsuface/...`，解析器能自動提取檔名並在其自包含 `input/`、`input/slides/`、`input/recordings/` 等目錄中自動配對，並容忍底線與空格拼寫差異，確保歷史專案與現行新專案皆能 100% 順暢走通。
