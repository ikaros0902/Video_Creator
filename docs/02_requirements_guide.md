# 環境需求與安裝指南（`00_docs/02_requirements_guide.md`）

本專案把所有工具與 AI 模型都封裝在倉庫目錄內（`.venv\`、`tools\`、`node_modules\`、`models\`），不會污染系統全域環境。

## 1. 基礎系統需求

| 項目 | 最低 / 建議需求 | 說明 |
| :--- | :--- | :--- |
| **作業系統** | Windows 10 / 11（主要測試平台）、macOS、Linux | 簡報 COM 轉圖功能僅在 Windows 安裝 PowerPoint 時可用；其餘皆跨平台 |
| **Python** | `3.11`（不支援 3.9 或 3.15+） | 執行 `.venv\Scripts\python.exe -m vc doctor` 驗證版本區間 |
| **Node.js** | `>= 18`（建議 20 LTS 以上） | 驅動 HyperFrames、Remotion 與 CapCut CLI |
| **GPU（選配但強烈建議）** | NVIDIA GTX/RTX（驅動 >= 525，支援 CUDA 12 與 NVENC） | 無 NVIDIA GPU 時仍可透過 Apple MPS 或純 CPU 執行 |
| **磁碟空間** | 建議保留 8–10 GB | `.venv`（含 PyTorch CUDA 約 4.5GB）+ Whisper/Kokoro 模型 + `tools/ffmpeg` |

## 2. 一鍵自動安裝（Windows）

```powershell
# 有 NVIDIA 顯卡時（預設安裝 CUDA 12.6 PyTorch）
powershell -ExecutionPolicy Bypass -File 09_scripts\setup.ps1

# 無 NVIDIA 顯卡、想在純 CPU 筆電或 CI 上測試
powershell -ExecutionPolicy Bypass -File 09_scripts\setup.ps1 -CpuOnly
```

此腳本會自動完成：
1. 建立 `.venv` 並安裝對應版本的 `torch`。
2. 安裝 `requirements.txt`（含 `openai-whisper`、`kokoro`、`manim`、`pydantic`、`pytest-bdd` 等）。
3. 下載免安裝版 FFmpeg / FFprobe 至 `tools\ffmpeg\`。
4. 在根目錄與 `remotion\` 執行 `npm install`。
5. 執行 `09_scripts\smoke_models.py` 預先下載並驗證語音與辨識模型，最後執行 `vc doctor --deep`。

## 3. 常見企業網路與環境問題排障

### 問題 A：企業防毒或內部憑證代理導致 SSL Error
本專案已內建 `truststore`（見 `vc/tools.py` 的 `use_system_certs()`），並且 Remotion 已強制帶入 `NODE_USE_SYSTEM_CA=1`。只要企業電腦系統憑證庫正常，Node 與 Python 皆可自動通過代理下載模型與套件。

### 問題 B：C 槽空間不足（HuggingFace / Chrome Cache 寫爆系統碟）
- `vc/tools.py` 會將 HuggingFace、Torch 與 Whisper 模型快取集中鎖定於倉庫內的 `models/` 資料夾，不寫入 `%USERPROFILE%\.cache`。
- 若使用 HyperFrames 算圖長影片時 C 槽吃緊，可指定 `--frames-cache-dir D:\tmp\hf_frames`。

### 問題 C：PowerPoint 輸出簡報圖片失敗
確認電腦有安裝桌面版 Microsoft PowerPoint；若沒有（或跑在 Linux/CI），可改用手動把簡報匯出為 PNG 並放進 `06_projects/<proj>/work/slides/`。
