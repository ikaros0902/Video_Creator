# GPU 加速實作與調優手冊（`00_docs/03_gpu_acceleration.md`）

本專案已整合全管線「**智慧自動偵測 + 安全回退 CPU**」GPU 加速架構，無需修改專案檔即可享受 NVIDIA NVENC / CUDA 與 Chromium ANGLE 硬體加速。

## 1. 全管線 GPU 加速矩陣

| 管線階段 | 負責模組 | GPU 加速方案 | 自動回退機制 | 手動關閉方式 |
| :--- | :--- | :--- | :--- | :--- |
| **Kokoro TTS 配音** | `vc/voice.py` | PyTorch `cuda`（支援 macOS `mps`） | 自動降至 `cpu` | `VC_DEVICE=cpu` |
| **Whisper 逐字對齊** | `vc/align.py` | PyTorch `cuda` + `fp16=True` | `cpu` 自動切為 `fp16=False` | `VC_DEVICE=cpu` |
| **Manim 轉檔裁幀** | `vc/manim_render.py` | FFmpeg `h264_nvenc`（`-preset p4 -cq 14`） | 無 GPU 時用 `libx264` | `--no-gpu` 或 `VC_GPU=off` |
| **錄影裁切與變速** | `vc/fit.py` | FFmpeg `h264_nvenc`（`-preset p4 -cq 16`） | 無 GPU 時用 `libx264` | `--no-gpu` 或 `VC_GPU=off` |
| **HyperFrames SVG 算圖** | `vc/hf_scenes.py` | CLI `--gpu --browser-gpu` | 失敗或停用時重試純 CPU 參數 | `--no-gpu` 或 `VC_GPU=off` |
| **Remotion 總裝合流** | `vc/render.py` | CLI `--gl=angle --hardware-acceleration=if-possible` | 第 1 次失敗第 2 次自動改用 CPU 重試 | `--no-gpu` 或 `VC_GPU=off` |

## 2. 環境變數全域開關

| 變數名稱 | 允許值 | 預設值 | 作用說明 |
| :--- | :--- | :--- | :--- |
| **`VC_GPU`** | `auto` / `on` / `off` | `auto` | `off`（或 `0`、`false`、`cpu`）會強制關閉所有 FFmpeg NVENC、HyperFrames 與 Remotion 硬體算圖 |
| **`VC_DEVICE`** | `cuda` / `mps` / `cpu` | 自動偵測 | 覆寫 PyTorch 在 `vc voice` 與 `vc align` 使用的計算裝置 |

> [!TIP]
> 在本機實機驗證環境（`NVIDIA RTX A2000 8GB`）中，`vc doctor` 會列出 `cuda` 裝置名稱與 `ffmpeg:gpu` 偵測到的編碼器（`h264_nvenc`、`h264_qsv`、`h264_amf` 依本機實測為準）。

## 3. 技術細節與重要注意事項

1. **FFmpeg NVENC 與畫質控制**：
   - `vc/media.py` 採用 `h264_encode_args(quality, cpu_preset, use_gpu)`：使用 NVENC 時對應 `-c:v h264_nvenc -preset p4 -rc vbr -cq <quality>`，兼顧 1080p 高文字銳利度與編碼速度。
   - 為避免雲端容器或無驅動主機出現偽陽性，`_probe_nvenc()` 會實際對 `testsrc` 壓縮 2 幀驗證 `h264_nvenc` 可真實開流後才快取啟用。
2. **Remotion 與 Chromium GPU 注意事項**：
   - `vc/render.py` 預設加入 `--gl=angle --hardware-acceleration=if-possible`。
   - 當環境遭遇虛擬機顯示卡異常或 `ERR_NETWORK_CHANGED` 等暫時性錯誤時，`render.py` 內建重試邏輯會在第 2 次嘗試自動切換為 `use_gpu=False`，確保長影片渲染不中斷。
3. **HyperFrames 多工與暫存調校**：
   - 當製作含 WebGL shader 或多層複雜 CSS blur 的 HyperFrames 場景時，`--browser-gpu` 能避免純軟體 SwiftShader 卡死，搭配 `--gpu` 可直接硬編輸出段落 MP4。
   - 若要客製額外 Worker 數，可在外部直接執行 `.bin\hyperframes render --workers 4 --gpu --browser-gpu`。
4. **確定性 vs 編碼速度取捨**：
   - 若您在做畫素級自動化比對測試（Golden Frame Diff）且嚴格要求不同顯卡驅動產生 100% 位元一致的 MP4，請在驗證前執行 `$env:VC_GPU="off"` 或帶入 `--no-gpu` 改用 `libx264`。
