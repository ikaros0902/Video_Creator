# Video_Creator — AI-Native 確定性技術影片自動產製管線

> 從簡報與螢幕錄影製作支援 GPU 加速的 1080p 技術教學影片。

`Video_Creator` 使用可驗證的腳本、事實表和旁白時間軸製作單一版本影片。

## 核心設計亮點

- **單一真值來源與嚴格事實門禁（`vc validate`）**：腳本中說出與畫面顯示的每一個數字，都必須追溯自 `facts.yaml` 的已確認出處；主管摘要模式（`strict_facts: true`）還會逐段強制檢查適用範圍 `scope`。
- **旁白驅動無漂移時間軸（`vc voice` → `vc align` → `vc plan`）**：採用 Kokoro / Edge 合成 48kHz 旁白，經 OpenAI Whisper 逐字對齊，所有動畫與錄影裁切直接鎖定口播單字（`at_word`），修改腳本免重剪整條軌道。
- **三引擎協同渲染 + 全管線 GPU 加速**：
  - **Manim**（向量幾何與數學原理，FFmpeg `h264_nvenc`）
  - **HyperFrames**（HTML/GSAP 等軸向量與數據字卡，`--gpu --browser-gpu`）
  - **Remotion**（實機錄影鏡頭推拉、標註框與預設 `-14 LUFS` 響度合流，`--gl=angle`）
  - 全管線支援自動偵測顯卡（NVIDIA CUDA / NVENC、macOS MPS）與 **CPU 確定性自動回退**。
- **單一影片輸出**：舊雙版本專案可使用 `vc migrate` 備份並轉換為單一畫面設定。
- **66 項 BDD 自動化回歸測試**：透過 `pytest-bdd` 守護字詞時間對齊、響度混音比例、錄影變速上限（2.5x）與公開版隱私隔離契約。

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

---

## 倉庫架構總覽

```text
Video_Creator/
├── AGENTS.md / CLAUDE.md       # AI 編碼代理入口規範（ASD-STE100 控制英語）
├── 00_docs/                    # 使用手冊、架構圖、安裝指南、GPU 調校與 Brief 範本（ISO 24495-1）
├── 01_rules/                   # 核心開發紀律、ASD-STE100、ISO 24495-1、影音響度標準
├── 02_workflows/               # BMAD + BDD 生命週期、實戰 SOP、多代理角色矩陣
├── 03_skills/                  # 5 大領域模組化 Skills（同步鏡像至 .agents/skills/）
├── 04_styles/                  # 可複用視覺風格包（STYLE.md + style.json）
├── 05_references/              # lemo-opuscar、anatomy、hyperframes 與 Remotion 生態剖析
├── 06_projects/                # 影片專案目錄（Git 僅保留脫敏示範 _sample 與 _sample_exec）
├── 07_features/                # Gherkin .feature 行為規格書
├── 08_tests/                   # pytest-bdd 自動化測試套件
├── 09_scripts/                 # 環境安裝、模型冒煙測試與抽幀檢查工具
├── vc/                         # 核心 Python CLI 管線套件（python -m vc）
└── remotion/                   # Master 1080p React/Remotion 合成器
```

## 深入文件導航

- **操作指南與架構**：[`00_docs/00_how_to_use.md`](00_docs/00_how_to_use.md)｜[`00_docs/01_architecture.md`](00_docs/01_architecture.md)｜[`00_docs/03_gpu_acceleration.md`](00_docs/03_gpu_acceleration.md)
- **工作流與開發規範**：[`02_workflows/00_bmad_bdd_lifecycle.md`](02_workflows/00_bmad_bdd_lifecycle.md)｜[`01_rules/00_core_rules.md`](01_rules/00_core_rules.md)
- **風格與技能生態**：[`04_styles/`](04_styles/)｜[`05_references/00_ecosystem_overview.md`](05_references/00_ecosystem_overview.md)

## 開源致謝與參考生態

本專案吸收並整合了以下優秀開源專案的設計思想：
- [`lemomo-ai/lemo-opuscar`](https://github.com/lemomo-ai/lemo-opuscar) — `STYLE.md` + `style.json` 主題解耦與程式碼導演語法
- [`wheresryan22/anatomy`](https://github.com/wheresryan22/anatomy) — Truth-First 機械等軸 SVG 投影與特寫視覺稽核
- [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes) — HTML/GSAP 確定性時間軸算圖與 `--gpu --browser-gpu` 加速
- [`remotion-dev/remotion`](https://github.com/remotion-dev/remotion) & [`remotion-dev/skills`](https://github.com/remotion-dev/skills) — React 元件化 1080p 總裝合成與 ANGLE GPU 算圖
