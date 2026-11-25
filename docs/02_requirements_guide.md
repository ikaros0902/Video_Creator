# 環境需求與安裝指南

安裝腳本將 Python 依賴、Node 依賴、FFmpeg 與模型放在專案內。Python 3.11 與 Node.js 需先安裝；瀏覽器及部分工具仍可能使用使用者快取目錄。

## 1. 基礎系統需求

| 項目 | 最低 / 建議需求 | 說明 |
| :--- | :--- | :--- |
| **作業系統** | Windows 10 / 11 | 安裝腳本、PowerPoint COM 及字型路徑以 Windows 為準；其他平台未由本安裝流程驗證 |
| **Python** | 建議 `3.11` | `vc doctor` 接受 3.10–3.12；安裝腳本以 3.11 建立 `.venv` |
| **Node.js** | `>= 22` | 與 `package.json` 及 `vc doctor` 的檢查一致 |
| **GPU（選配但強烈建議）** | NVIDIA GTX/RTX（驅動 >= 525，支援 CUDA 12 與 NVENC） | 無 NVIDIA GPU 時仍可透過 Apple MPS 或純 CPU 執行 |
| **磁碟空間** | 建議保留 8–10 GB | `.venv`（含 PyTorch CUDA 約 4.5GB）+ Whisper/Kokoro 模型 + `tools/ffmpeg` |

## 2. 一鍵自動安裝（Windows）

```powershell
# 有 NVIDIA 顯卡時（預設安裝 CUDA 12.6 PyTorch）
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# 無 NVIDIA 顯卡、想在純 CPU 筆電或 CI 上測試
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -CpuOnly
```

此腳本會自動完成：
1. 建立 `.venv` 並安裝對應版本的 `torch`。
2. 安裝 `requirements.txt`（含 `openai-whisper`、`kokoro`、`manim`、`pydantic`、`pytest-bdd` 等）。
3. 下載免安裝版 FFmpeg / FFprobe 至 `tools\ffmpeg\`。
4. 在根目錄執行 `npm ci`，安裝根目錄及 Remotion workspace 的鎖定依賴。
5. 執行 `scripts\smoke_models.py` 下載並驗證語音與辨識模型，最後執行 `vc doctor --deep`。Edge TTS 冒煙測試需要連網。

## 3. 常見企業網路與環境問題排障

### 問題 A：企業防毒或內部憑證代理導致 SSL Error
本專案使用 `truststore`（見 `vc/tools.py` 的 `use_system_certs()`），Remotion 也帶入 `NODE_USE_SYSTEM_CA=1`。若仍失敗，請檢查系統憑證、代理設定與目的服務是否允許連線。

### 問題 B：C 槽空間不足（HuggingFace / Chrome Cache 寫爆系統碟）
- `vc/tools.py` 預設將 Hugging Face、Torch 與 Whisper 模型放在 `models/`；已有的 `HF_HOME` 與 `TORCH_HOME` 環境設定會保留。
- HyperFrames 瀏覽器快取可透過 `HYPERFRAMES_CACHE_DIR` 指到有空間的資料夾。若直接使用 HyperFrames CLI，其他快取選項請先查其 `--help`。

### 問題 C：PowerPoint 輸出簡報圖片失敗
確認電腦有安裝桌面版 Microsoft PowerPoint。`vc ingest-ppt --no-preview` 只匯入文字與內嵌圖片；腳本若引用 `work/slides/previews/`，必須由目前簡報成功產生預覽圖，否則來源檢查會拒絕。
