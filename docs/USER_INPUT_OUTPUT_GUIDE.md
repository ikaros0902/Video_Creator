# Video Creator 使用者操作指南 (USER_INPUT_OUTPUT_GUIDE.md)

本指南遵循 ISO 24495-1 淺白技術寫作原則（Plain Language），以清晰、直覺、任務導向（Task-Oriented）的架構引導使用者準備素材、撰寫設定、執行管線與獲取輸出成果。

---

## 1. 快速導覽 (Quick Start)

### 核心理念

Video Creator 以旁白、分鏡腳本與事實表驅動影片管線。準備所需素材與設定後，可依序執行語音合成、逐字對齊、動畫渲染、背景音樂避讓與影片合成。每個場景只使用一份 `visual` 設定，最後輸出單一影片。

### 3 分鐘快速體驗範例

在專案根目錄開啟終端機（PowerShell），執行下列指令即可驗證既有範例專案：

```powershell
# 1. 執行環境診斷；必要項目需通過，選用項目可能顯示 WARN
.venv\Scripts\python.exe -m vc doctor

# 2. 驗證內建範例專案之腳本語法與事實真相表
.venv\Scripts\python.exe -m vc validate _sample

# 3. 驗證另一份內建摘要範例
.venv\Scripts\python.exe -m vc validate _sample_exec
```

完整範例腳本位於 [`projects/_sample/script.json`](../projects/_sample/script.json) 與 [`projects/_sample_exec/script.json`](../projects/_sample_exec/script.json)。倉庫未附範例原始簡報與錄影；腳本驗證通過不代表素材已可完整渲染。

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
├── project.yaml            # 專案識別、素材路徑、風格與運鏡設定
├── facts.yaml              # 事實真相表（旁白數字出處、數值與白名單硬門禁）
└── script.json             # 分鏡、旁白、配音與單一畫面設定
```

### 2.1 簡報檔案規範 (`input/slides/`)

- **支援格式**：Microsoft PowerPoint 簡報（`.pptx`）。
- **長寬比與解析度**：強烈建議設定為 16:9 寬螢幕（1920x1080）。
- **投影片備忘稿（Slide Notes）**：`vc ingest-ppt` 會擷取備忘稿文字，可供撰寫初版旁白時參考；不會自動產生完整腳本。
- **命名建議**：使用小寫英數字與底線，如 `presentation_v1.pptx` 或 `ACT-SC_Midsurface_Automation.pptx`。

### 2.2 螢幕錄影規範 (`input/recordings/`)

- **支援格式**：標準 H.264 / AAC 編碼之 `.mp4` 視訊檔。
- **畫面長寬比與幀率**：推薦 1920x1080 或 1920x1200，固定幀率 30 fps 或 60 fps。
- **錄製注意事項**：建議在安靜環境錄製、關閉非必要背景通知，避免滑鼠劇烈晃動或無意義停留。
- **檔名命名規範**：推薦以簡短流水號或功能命名，例如 `rec01.mp4`、`rec02.mp4` 或 `Manual_Work.mp4`、`Automation.mp4`，以利在 `project.yaml` 與 `script.json` 中對應指定。

### 2.3 背景音樂與音訊規範 (`input/audio/`)

- **檔案命名**：若專案需使用專屬背景音樂，請放置於 `input/audio/bgm.mp3`（或 `input/bgm.mp3`）。
- **自動 Ducking 避讓**：管線量測旁白與配樂響度，計算旁白時低於旁白約 20 dB、停頓時低約 14 dB 的配樂增益；實際增益會受上限限制。
- **共用音樂**：`assets/templates/audio/background_music_01.mp3` 與 `background_music_02.mp3` 是共用素材。先複製所選音訊為專案 `input/audio/bgm.mp3` 才會套用。渲染器依序讀取專案 `input/bgm.mp3`、`input/audio/bgm.mp3`、專案根目錄 `bgm.mp3`，不會自動載入全域素材；沒有配樂則略過。

---

## 3. 設定檔欄位規範與標準範本 (Configuration Specifications)

### 3.1 專案設定檔：`project.yaml`

`project.yaml` 定義專案識別、視覺主題、運鏡與素材路徑。影片標題、fps、尺寸及配音設定放在 `script.json` 的 `meta`：

```yaml
name: midsurface                                # 專案唯一標識符（英數字與底線）
style: executive_navy                           # executive_navy | swiss_kinetic | blueprint | cyberpunk_neon
camera_mode: dynamic                            # 運鏡模式：fixed（固定）| dynamic（平滑追焦）| cinematic（電影推拉）
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

`script.json` 包含影片設定、音譯字典、術語、禁詞與場景。以下僅為欄位示意，並非可直接通過段落順序及時長檢查的完整腳本；完整範例請使用上方連結。

```json
{
  "schema_version": 2,
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
      "visual": {
          "kind": "recording",
          "template": "vs_intro",
          "clips": [
            {
              "recording": "rec01",
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
      }
    }
  ]
}
```

`visual.kind` 可為 `recording`、`anim` 或 `manim`。錄影依 `project.yaml.recordings` 順序編為 `rec01`、`rec02` 等。舊 `visuals.internal/public` 格式需先執行 `.venv\Scripts\python.exe -m vc migrate <project>`，原始腳本會備份為 `script.json.bak`。

---

## 4. 專案輸出規格 (Output Standards)

所有由管線渲染生成的影片成品、字幕檔與稽核診斷報告均存放於 `projects/<project_name>/output/`：

```text
projects/<name>/output/
├── <name>.mp4                          # 單一影片，由 render --name 指定
├── final.srt                           # 由 plan 產生的影片時間軸字幕
└── reports/
    ├── metadata.json                   # 檔名、影格數、時長、解析度與檔案大小
    └── loudness_report.json            # 目標與實測響度、峰值及檢查結果
```

### 輸出命名規範

- **視訊檔案**：未指定 `--name` 時為 `draft.mp4`；可指定英數字、底線或連字號，例如 `20261125_midsurface_v1`。
- **SRT 字幕檔案**：由 Whisper 逐字對齊產生，採用 UTF-8 編碼，時間戳精確至毫秒（`00:00:01,250 --> 00:00:03,400`）。
- **預設音訊目標**：整合響度 **-14.0 LUFS（容許 ±1.0 LUFS）**、True Peak 目標 **-1.5 dBTP**。可在 `project.yaml` 設定 `loudness.target_lufs` 與 `loudness.true_peak`；輸出檢查對峰值保留 0.1 dB 容差。

---

## 5. 端到端 CLI 操作指南 (Step-by-Step Pipeline)

製作一部新影片的標準 10 步驟生產流程：

```powershell
# 步驟 1：依賴檢查 — 確認本機工具與 GPU 正常就緒
.venv\Scripts\python.exe -m vc doctor

# 步驟 2：素材攝取 — 解析簡報結構與匯出投影片圖片
.venv\Scripts\python.exe -m vc ingest-ppt midsurface

# 步驟 3：錄影攝取 — 探測錄影時長、解析度並建立特徵索引
.venv\Scripts\python.exe -m vc ingest-rec midsurface

# 步驟 4：分鏡驗證 — 檢查旁白字數、易讀度、事實表與畫面引用
.venv\Scripts\python.exe -m vc validate midsurface

# 步驟 5：配音合成 — 透過本機 Kokoro TTS 批次產生各分鏡旁白音訊
.venv\Scripts\python.exe -m vc voice midsurface

# 步驟 6：逐字對齊 — 透過 OpenAI Whisper 提取單詞時間戳並生成字幕
.venv\Scripts\python.exe -m vc align midsurface

# 步驟 7：時間軸規劃 — 進行零累積捨入誤差的影格級時間軸排程
.venv\Scripts\python.exe -m vc plan midsurface

# 步驟 8：動態卡片與數學動畫渲染 — 透過 Manim 與 Hyperframes 產出中間片段
.venv\Scripts\python.exe -m vc manim midsurface
.venv\Scripts\python.exe -m vc hf midsurface

# 步驟 9：錄影自動剪裁與智慧變速 — 依據旁白長度自動微調錄影動作
.venv\Scripts\python.exe -m vc fit midsurface

# 步驟 10：總合成渲染 — 呼叫 Remotion 合成單一影片並調整響度
.venv\Scripts\python.exe -m vc render midsurface --name v1
```

---

## 6. 常見錯誤與排障問答 (Troubleshooting FAQ)

### Q1: `vc validate` 出現「旁白中的數字 X 不在已確認的事實表」報錯？
- **原因**：在 `script.json` 的 `narration` 旁白中出現了未經確認的數字（例如 `"saves 4 hours"` 中的 4）。
- **排查對策**：
  1. 開啟該專案的 `facts.yaml`。
  2. 新增或確認包含該數字的事實條目，將數字放入 `spoken: ["4"]` 清單中。
  3. 將該事實條目的 `confirmed: true` 設為 true。
  4. 重新執行 `.venv\Scripts\python.exe -m vc validate <project>` 即可通過。

### Q2: 舊腳本仍使用 `visuals.internal/public`，或指令帶有 `--variant`？
- **對策**：先執行 `.venv\Scripts\python.exe -m vc migrate <project>`，再重建素材匯入、語音、對齊、時間軸與片段。轉換以原 `internal` 畫面作為單一 `visual`，原始腳本會保留備份。新指令不再使用 `--variant`。

### Q3: 執行渲染時出現 GPU 記憶體不足（CUDA Out of Memory）或無顯示卡環境？
- **對策**：渲染命令可加上 `--no-gpu`。語音與對齊若要使用 CPU，另外設定 `VC_DEVICE=cpu`：
  ```powershell
  # 停用渲染 GPU 參數，並指定語音與對齊使用 CPU
  $env:VC_GPU = "off"
  $env:VC_DEVICE = "cpu"
  .venv\Scripts\python.exe -m vc render <project> --no-gpu
  ```

### Q4: 如何預覽或微調 Remotion 合成畫面？
- **對策**：在根目錄執行：
  ```powershell
  npm run remotion:studio
  ```
  開啟終端機顯示的網址，使用實際產生的 `work/remotion/props.json` 與專案工作素材檢查合成。未提供專案 props 時，Studio 預設內容不代表目前影片。
