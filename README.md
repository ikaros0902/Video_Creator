# Video_Creator — AI-Native 確定性技術影片自動產製管線

> 從簡報與螢幕錄影製作支援 GPU 加速的 1080p 技術教學影片。

`Video_Creator` 使用可驗證的腳本、事實表和旁白時間軸製作單一版本影片。

## 核心設計亮點

- **腳本與事實驗證（`vc validate`）**：檢查旁白數字、來源確認狀態、詞彙與時間預算；`strict_facts: true` 另逐段檢查畫面數字與適用範圍 `scope`。
- **旁白驅動無漂移時間軸（`vc voice` → `vc align` → `vc plan`）**：採用 Kokoro / Edge 合成 48kHz 旁白，經 OpenAI Whisper 逐字對齊，所有動畫與錄影裁切直接鎖定口播單字（`at_word`），修改腳本免重剪整條軌道。
- **三引擎協同渲染**：
  - **Manim**（向量幾何與數學原理，FFmpeg `h264_nvenc`）
  - **HyperFrames**（HTML/GSAP 等軸向量與數據字卡，`--gpu --browser-gpu`）
  - **Remotion**（實機錄影鏡頭推拉、標註框與預設 `-14 LUFS` 響度合流，`--gl=angle`）
  - 各階段依環境使用 GPU 或 CPU；可用 `vc doctor` 檢查工具與裝置。
- **單一影片輸出**：舊雙版本專案可使用 `vc migrate` 備份並轉換為單一畫面設定。
- **BDD 與安全門禁**：測試字詞時間對齊、混音、錄影變速上限（2.5x）、素材新鮮度與失敗時保留既有成品。預設測試不執行需要外部素材的整合案例。
- **本機創作工具**：`vc creative` 提供靈感資料、風格比較與排版預覽，`vc reference` 可呼叫隔離環境中的 rea-video 拆解參考影片。

---

## 快速開始（Windows）

### 1. 重建本機封裝環境（一次設定）

```powershell
# 有 NVIDIA 顯卡（自動安裝 CUDA 12.6 PyTorch、FFmpeg 與 Node 依賴）
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# 無 GPU 或純 CPU 測試環境
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -CpuOnly
```

### 2. 環境檢查與測試門禁

```powershell
.venv\Scripts\python.exe -m vc doctor
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m vc validate _sample
.venv\Scripts\python.exe -m vc validate _sample_exec
```

### 3. 建立你的第一支影片

複製 `projects/_sample` 為新專案，再依 [使用指南](docs/00_how_to_use.md) 執行管線。影片輸出至 `projects/<project>/output/`。參考影片分析與風格工作區分別見 [分析指南](docs/REFERENCE_ANALYSIS.md) 和 [設計工作區](docs/creative_tools.md)。

## 範例腳本在哪裡？

| 範例 | 腳本 | 用途 |
| :--- | :--- | :--- |
| 標準教學 | [`projects/_sample/script.json`](projects/_sample/script.json) | 七段教學結構，搭配同目錄的 `facts.yaml` 與 `project.yaml` |
| 主管摘要 | [`projects/_sample_exec/script.json`](projects/_sample_exec/script.json) | 五段摘要，啟用逐段事實驗證 |
| 風格示範 | [`projects/_sample_exec/style_demo/script.json`](projects/_sample_exec/style_demo/script.json) | 比較風格與運鏡設定，執行前需補齊其 README 列出的素材 |

前兩個範例是文字藍圖，可直接執行 `vc validate`。倉庫沒有附帶它們引用的原始簡報、錄影及完整渲染產物；製片前需提供素材並更新設定。建立私人影片專案的方法見 [`projects/README.md`](projects/README.md)。

### 使用共用背景音樂

[`assets/templates/audio/`](assets/templates/audio/) 內有 `background_music_01.mp3` 與 `background_music_02.mp3`，兩者音訊內容相同。若要使用，將其中一個複製至影片專案的 `input/audio/bgm.mp3`；渲染器不會自動讀取共用資料夾。若專案已有 `input/bgm.mp3`，渲染器會優先使用該檔。

```powershell
New-Item -ItemType Directory -Force projects/my_video/input/audio
Copy-Item assets/templates/audio/background_music_01.mp3 projects/my_video/input/audio/bgm.mp3
```

---

## 倉庫架構總覽

```text
Video_Creator/
├── AGENTS.md / CLAUDE.md       # 編碼代理規範入口
├── assets/                    # 共用素材與模板資產
├── docs/                      # 使用、安裝、分析與設計工作區文件
│   └── references/            # 外部影音專案的參考分析
├── rules/                     # 開發、文案與影音規則
├── workflows/                 # 製片 SOP 與開發流程
├── skills/                    # 專案技能與驗證腳本
├── styles/                    # 四套風格參數與 Jinja2 動畫模板
├── projects/                  # 影片專案；Git 保留 _sample 與 _sample_exec
├── tests/                     # 單元、BDD 與整合測試
│   ├── features/              # Gherkin 行為規格
│   └── bdd/                   # 規格步驟實作
├── scripts/                   # 環境安裝、模型測試與檢查工具
├── vc/                        # Python CLI 與影音管線
├── remotion/                  # React / Remotion 合成器
└── external/                  # 外部工具清單；本機下載內容不納入 Git
```

安裝後產生的 `.venv/`、`node_modules/`、`tools/`、`models/`，以及專案內的 `input/`、`work/`、`output/` 屬本機環境或產物，不是下載倉庫時就具備的範例成品。

## 深入文件導航

- **使用與環境**：[操作指南](docs/00_how_to_use.md)｜[環境需求](docs/02_requirements_guide.md)｜[GPU 說明](docs/03_gpu_acceleration.md)
- **創作與分析**：[設計工作區](docs/creative_tools.md)｜[參考影片分析](docs/REFERENCE_ANALYSIS.md)
- **工作流與規則**：[製片 SOP](workflows/01_new_video_sop.md)｜[開發流程](workflows/00_bmad_bdd_lifecycle.md)｜[核心規則](rules/00_core_rules.md)
- **範例與風格**：[專案範例](projects/README.md)｜[風格參數](styles/)｜[外部專案分析](docs/references/00_ecosystem_overview.md)

## 開源致謝與參考生態

本專案吸收並整合了以下優秀開源專案的設計思想：
- [`lemomo-ai/lemo-opuscar`](https://github.com/lemomo-ai/lemo-opuscar) — `STYLE.md` + `style.json` 主題解耦與程式碼導演語法
- [`wheresryan22/anatomy`](https://github.com/wheresryan22/anatomy) — Truth-First 機械等軸 SVG 投影與特寫視覺稽核
- [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes) — HTML/GSAP 確定性時間軸算圖與 `--gpu --browser-gpu` 加速
- [`remotion-dev/remotion`](https://github.com/remotion-dev/remotion) & [`remotion-dev/skills`](https://github.com/remotion-dev/skills) — React 元件化 1080p 總裝合成與 ANGLE GPU 算圖
