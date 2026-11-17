# Video Creator 使用者操作指南 (USER_INPUT_OUTPUT_GUIDE.md)

本指南遵循 ISO 24495-1 淺白技術寫作原則（Plain Language），以清晰、直覺、任務導向（Task-Oriented）的架構引導使用者準備素材、撰寫設定、執行管線與獲取輸出成果。

---

## 1. 快速導覽 (Quick Start)

### 核心理念

Video Creator 是一套「以旁白與分鏡腳本為單一真值來源」的規格驅動自動化影片生產管線。您只需提供簡報、操作錄影與結構化文案，管線即可自動完成語音合成、毫秒級逐字對齊、動態卡片渲染、背景音樂避讓（Ducking）與最終 1080p 影片壓制。

### 3 分鐘快速體驗範例

在專案根目錄開啟終端機（PowerShell），執行下列指令即可驗證既有範例專案：

```powershell
# 1. 執行環境依賴健全度診斷（確保 28 項依賴均顯示 OK）
python -m vc doctor

# 2. 驗證內建範例專案之腳本語法與事實真相表
python -m vc validate _sample

# 3. 驗證正式專案（例如 midsurface）之自包含規格
python -m vc validate midsurface
```

---

## 2. 專案輸入規格 (Input Standards)

在 Video Creator 中，每個影片專案皆自包含於 `projects/<project_name>/` 目錄下。使用者應依循下列目錄結構準備素材：

```text
projects/<project_name>/
├── input/
│   ├── slides/             # 簡報檔案 (*.pptx)
│   ├── recordings/         # 軟體操作螢幕錄影 (*.mp4)
│   ├── audio/              # 自訂音訊或背景音樂 (*.mp3, *.wav)
│   └── assets/             # 專案專屬圖片、SVG 向量圖或示意圖 (*.png, *.jpg, *.svg)
├── project.yaml            # 專案主設定檔（專案識別、風格選擇、配音員指定）
├── facts.yaml              # 事實真相表（旁白數字出處、數值與白名單硬門禁）
└── script.json             # 唯一由人維護的分鏡腳本（旁白、視覺標註、雙軌模式）
```

### 2.1 簡報檔案規範 (`input/slides/`)

- **支援格式**：Microsoft PowerPoint 簡報（`.pptx`）。
- **長寬比與解析度**：強烈建議設定為 16:9 寬螢幕（1920x1080）。
- **投影片備忘稿（Slide Notes）**：管線在執行 `vc ingest-ppt` 時會自動擷取備忘稿文字，可作為初版旁白腳本的自動生成來源。
- **命名建議**：使用小寫英數字與底線，如 `presentation_v1.pptx` 或 `ACT-SC_Midsurface_Automation.pptx`。

### 2.2 螢幕錄影規範 (`input/recordings/`)

- **支援格式**：標準 H.264 / AAC 編碼之 `.mp4` 視訊檔。
- **畫面長寬比與幀率**：推薦 1920x1080 或 1920x1200，固定幀率 30 fps 或 60 fps。
- **錄製注意事項**：建議在安靜環境錄製、關閉非必要背景通知，避免滑鼠劇烈晃動或無意義停留。
- **檔名命名規範**：推薦以簡短流水號或功能命名，例如 `rec01.mp4`、`rec02.mp4` 或 `Manual_Work.mp4`、`Automation.mp4`，以利在 `project.yaml` 與 `script.json` 中對應指定。

### 2.3 背景音樂與音訊規範 (`input/audio/`)

- **檔案命名**：若專案需使用專屬背景音樂，請放置於 `input/audio/bgm.mp3`（或 `input/bgm.mp3`）。
- **自動 Ducking 避讓**：管線在最終合成階段會自動偵測旁白語音區間；當旁白發聲時，背景音樂會自動平滑降音（衰減約 -14 dB），語音間歇時恢復正常響度。
- **全域免版稅音樂**：若專案未提供自訂配樂，系統將自動從 `assets/templates/audio/bgm_midsurface.mp3` 載入預設高質感工程風格背景音樂。

---

## 3. 設定檔欄位規範與標準範本 (Configuration Specifications)

### 3.1 專案設定檔：`project.yaml`

`project.yaml` 定義影片的基本元數據、視覺主題風格、運鏡風格與素材路徑：

```yaml
name: midsurface                                # 專案唯一標識符（英數字與底線）
title: "ANSYS Midsurface Automated Preparation" # 影片正式標題
style: executive_navy                           # 視覺風格包：executive_navy | swiss_kinetic | blueprint | isometric
camera_mode: dynamic                            # 運鏡模式：fixed（固定）| dynamic（平滑追焦）| cinematic（電影推拉）
fps: 30                                         # 影片畫格率（預設 30）
resolution: [1920, 1080]                        # 畫布尺寸 [寬, 高]
voice:
  engine: kokoro                                # 語音合成引擎：kokoro（本機高效）| edge（雲端擬真）
  name: am_michael                              # 配音角色標識（kokoro: am_michael, am_adam, af_bella; edge: en-US-AndrewNeural）
  rate: 1.05                                    # 語速倍率（標準為 1.0）
pptx: input/slides/ACT-SC_Midsurface_Automation.pptx
recordings:
  - input/recordings/MidsurfaceACT.mp4
  - input/recordings/Manual_Work.mp4
  - input/recordings/Automation.mp4
```

### 3.2 事實真相表：`facts.yaml`

為杜絕 AI 幻覺與杜撰數據，Video Creator 實施嚴格的事實門禁機制。**旁白中所提及的每一個阿拉伯數字，都必須在 `facts.yaml` 中登記且標記為已確認（`confirmed: true`）**：

```yaml
# 事實真相表：數值、出處與朗讀白名單
sheet_metal_parts:
  value: "24"
  spoken: ["24"]                               # 旁白語音中允許出現的字串
  sources: ["Benchmark suite log: Succeeded 24"]
  confirmed: true                              # 必須為 true，否則 vc validate 將嚴格阻斷
  scope: "Full chassis assembly benchmark"
  shown: ["24", "100%"]                        # 畫面字卡與標註允許顯示的數字

manual_time:
  value: "4–8 hrs"
  spoken: ["4", "8"]                           # 拆解朗讀到的數字
  sources: ["Historical workflow timing test"]
  confirmed: true
  scope: "24 parts manual repair baseline"
  shown: ["4-8h", "Manual"]
```

### 3.3 分鏡腳本檔：`script.json`

`script.json` 是全片唯一的劇情與畫面排程核心，包含全域元數據、音譯字典、術語定義、禁詞黑名單與各分鏡場景（Scenes）：

```json
{
  "meta": {
    "title": "ANSYS Midsurface Automated Preparation",
    "fps": 30,
    "size": [1920, 1080],
    "voice": {
      "engine": "kokoro",
      "name": "am_michael",
      "rate": "1.05"
    },
    "target_duration_s": [130.0, 170.0],
    "words_per_minute": [130.0, 165.0],
    "max_sentence_words": 20,
    "max_fk_grade": 8.0,
    "strict_facts": false
  },
  "lexicon": {
    "SpaceClaim": "Space Claim",
    "SCDM": "Space Claim"
  },
  "glossary": [
    {
      "term": "midsurface",
      "defined_in": "s02",
      "plain": "one surface in the middle of a thin solid part"
    }
  ],
  "banned_terms": ["robust", "seamless", "watertight", "leverage"],
  "scenes": [
    {
      "id": "s01",
      "section": "vs_intro",
      "narration": "An engineer prepares thin metal bodies for stress analysis. The built-in CAD tool leaves open seams.",
      "budget_s": [15.0, 19.0],
      "facts": [],
      "visuals": {
        "internal": {
          "kind": "recording",
          "template": "vs_intro",
          "clips": [
            {
              "recording": "MidsurfaceACT",
              "source": [2.0, 8.0],
              "label": "Built-in Tool Seams",
              "camera": "dolly_in"
            }
          ],
          "callouts": [
            {
              "at_word": "seams",
              "box": [1200, 140, 400, 80],
              "text": "Open seams detected",
              "clip": 0
            }
          ]
        },
        "public": {
          "kind": "anim",
          "template": "vs_intro_mock",
          "data": {
            "title": "Thin Shell Defect Comparison",
            "badge": "PROBLEM DEMO"
          }
        }
      }
    }
  ]
}
```

> **重要隱私約束**：
> - `visuals.internal`：允許使用 `recording`（實機操作）、`anim`（向量卡片）與 `manim`（數學幾何）。
> - `visuals.public`：為保護內部商業敏感介面，**強制限制僅能使用 `anim` 或 `manim`**，嚴禁出現 `recording` 或真實投影片截圖。

---

## 4. 專案輸出規格 (Output Standards)

所有由管線渲染生成的影片成品、字幕檔與稽核診斷報告均存放於 `projects/<project_name>/output/`：

```text
projects/<name>/output/
├── internal/                           # 內部培訓版（含實機畫面與操作細節）
│   ├── <YYYYMMDD>_<variant>_<name>.mp4  # 1080p 內部母帶視訊
│   └── <YYYYMMDD>_<variant>_<name>.srt  # 毫秒精準雙語/英文字幕檔
├── public/                             # 外部公開版（純向量動態圖表脫敏版）
│   ├── <YYYYMMDD>_<variant>_<name>.mp4  # 1080p 公開脫敏視訊
│   └── <YYYYMMDD>_<variant>_<name>.srt  # 毫秒精準字幕檔
└── reports/                            # 質檢與合規認證報告
    ├── metadata.json                   # 總影格數、編碼耗時、平均碼率、解析度
    └── loudness_report.json            # EBU R128 (-16 LUFS) 響度合規認證數據
```

### 輸出命名規範

- **視訊檔案**：預設採用 `<name>.mp4`，建議生產環境加上日期與版本，例如 `20261115_internal_midsurface_v1.mp4`。
- **SRT 字幕檔案**：由 Whisper 逐字對齊產生，採用 UTF-8 編碼，時間戳精確至毫秒（`00:00:01,250 --> 00:00:03,400`）。
- **EBU R128 音訊響度標準**：整合響度目標為 **-16.0 LUFS (±1.0 LUFS)**，真實峰值（True Peak）不超過 **-1.0 dBTP**，符合 YouTube、Vimeo 與主流線上教育平台標準。

---

## 5. 端到端 CLI 操作指南 (Step-by-Step Pipeline)

製作一部新影片的標準 10 步驟生產流程：

```powershell
# 步驟 1：依賴檢查 — 確認本機工具與 GPU 正常就緒
python -m vc doctor

# 步驟 2：素材攝取 — 解析簡報結構與匯出投影片圖片
python -m vc ingest-ppt midsurface

# 步驟 3：錄影攝取 — 探測錄影時長、解析度並建立特徵索引
python -m vc ingest-rec midsurface

# 步驟 4：分鏡驗證 — 嚴格稽核旁白字數、易讀度等級、事實真相表與隱私限制
python -m vc validate midsurface

# 步驟 5：配音合成 — 透過本機 Kokoro TTS 批次產生各分鏡旁白音訊
python -m vc voice midsurface

# 步驟 6：逐字對齊 — 透過 OpenAI Whisper 提取單詞時間戳並生成字幕
python -m vc align midsurface

# 步驟 7：時間軸規劃 — 進行零累積捨入誤差的影格級時間軸排程
python -m vc plan midsurface

# 步驟 8：動態卡片與數學動畫渲染 — 透過 Manim 與 Hyperframes 產出中間片段
python -m vc manim midsurface
python -m vc hf midsurface

# 步驟 9：錄影自動剪裁與智慧變速 — 依據旁白長度自動微調錄影動作
python -m vc fit midsurface

# 步驟 10：總合成渲染 — 呼叫 Remotion 進行雙軌分流合成與 EBU R128 響度壓制
python -m vc render midsurface --variant all --name v1
```

---

## 6. 常見錯誤與排障問答 (Troubleshooting FAQ)

### Q1: `vc validate` 出現「旁白中的數字 X 不在已確認的事實表」報錯？
- **原因**：在 `script.json` 的 `narration` 旁白中出現了未經確認的數字（例如 `"saves 4 hours"` 中的 4）。
- **排查對策**：
  1. 開啟該專案的 `facts.yaml`。
  2. 新增或確認包含該數字的事實條目，將數字放入 `spoken: ["4"]` 清單中。
  3. 將該事實條目的 `confirmed: true` 設為 true。
  4. 重新執行 `python -m vc validate <project>` 即可通過。

### Q2: `vc validate` 出現「public 版不能使用 recording」報錯？
- **原因**：系統內建商業機密防洩漏機制，公開版（`visuals.public`）禁止使用 `recording` 類型的素材或引用簡報截圖。
- **排查對策**：將 `script.json` 中對應場景的 `visuals.public.kind` 修改為 `"anim"` 或 `"manim"`，並配置對應的動態卡片樣板。

### Q3: 執行渲染時出現 GPU 記憶體不足（CUDA Out of Memory）或無顯示卡環境？
- **對策**：Video Creator 內建完善的 CPU 優雅降級機制。您可在指令後加上 `--no-gpu` 參數，或於環境中設定變數：
  ```powershell
  # 暫時關閉 GPU 加速，平滑切換至純 CPU 運算
  $env:VC_GPU = "off"
  python -m vc render <project> --no-gpu
  ```

### Q4: 如何預覽或微調 Remotion 合成畫面？
- **對策**：在根目錄執行：
  ```powershell
  npm run remotion:studio
  ```
  系統將在瀏覽器啟動 `http://localhost:3000` 互動播放器，支援拖曳時間軸、即時檢查影格、動態字幕與分軌圖層。
