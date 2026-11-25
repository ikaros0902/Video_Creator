# GPU 加速實作與調優手冊

管線可使用 PyTorch CUDA、FFmpeg NVENC 與 Chromium ANGLE。各階段的偵測和失敗處理不同；請先用 `vc doctor` 檢查目前環境。

## 1. 全管線 GPU 加速矩陣

| 管線階段 | 負責模組 | GPU 加速方案 | 自動回退機制 | 手動關閉方式 |
| :--- | :--- | :--- | :--- | :--- |
| **Kokoro TTS 配音** | `vc/voice.py` | PyTorch `cuda`（裝置偵測也支援 `mps`） | 未偵測到可用 GPU 時選擇 `cpu`；執行失敗不保證自動重試 | `VC_DEVICE=cpu` |
| **Whisper 逐字對齊** | `vc/align.py` | PyTorch `cuda` + `fp16=True` | `cpu` 自動切為 `fp16=False` | `VC_DEVICE=cpu` |
| **Manim 轉檔裁幀** | `vc/manim_render.py` | FFmpeg `h264_nvenc`（`-preset p4 -cq 14`） | 無 GPU 時用 `libx264` | `--no-gpu` 或 `VC_GPU=off` |
| **錄影裁切與變速** | `vc/fit.py` | FFmpeg `h264_nvenc`（`-preset p4 -cq 16`） | 無 GPU 時用 `libx264` | `--no-gpu` 或 `VC_GPU=off` |
| **HyperFrames SVG 算圖** | `vc/hf_scenes.py` | CLI `--gpu --browser-gpu` | GPU 嘗試失敗後，改用不含這兩個旗標的命令重試 | `--no-gpu` 或 `VC_GPU=off` |
| **Remotion 總裝合流** | `vc/render.py` | CLI `--gl=angle --hardware-acceleration=if-possible` | 失敗會回傳錯誤並保留舊成品；可手動以 `--no-gpu` 重跑 | `--no-gpu` 或 `VC_GPU=off` |

## 2. 環境變數全域開關

| 變數名稱 | 允許值 | 預設值 | 作用說明 |
| :--- | :--- | :--- | :--- |
| **`VC_GPU`** | `auto` / `on` / `off` | `auto` | 使用 `off` 停用本管線加入的 GPU 編碼與算圖參數；不影響 PyTorch 裝置選擇 |
| **`VC_DEVICE`** | `cuda` / `mps` / `cpu` | 自動偵測 | 覆寫 PyTorch 在 `vc voice` 與 `vc align` 使用的計算裝置 |

> [!TIP]
> `vc doctor` 會列出目前 PyTorch 的裝置名稱與 FFmpeg 提供的編碼器。列出某個編碼器不代表該硬體一定可用，NVENC 另有實際開流檢查。

## 3. 技術細節與重要注意事項

1. **FFmpeg NVENC 與畫質控制**：
   - `vc/media.py` 的 `h264_encode_args(quality, cpu_preset, use_gpu)` 在使用 NVENC 時加入 `-c:v h264_nvenc -preset p4 -cq <quality>`；否則使用 `libx264`。
   - `_probe_nvenc()` 以 64×64 黑色測試畫面編碼 1 幀，檢查 NVENC 是否可開流並快取結果。
2. **Remotion 與 Chromium GPU 注意事項**：
   - `vc/render.py` 預設加入 `--gl=angle --hardware-acceleration=if-possible`。
   - 若渲染失敗，檢查錯誤訊息後可用 `.venv\Scripts\python.exe -m vc render <project> --no-gpu` 重跑。目前沒有自動第二次 CPU 重試。
3. **HyperFrames 多工與暫存調校**：
   - 當製作含 WebGL shader 或多層複雜 CSS blur 的 HyperFrames 場景時，`--browser-gpu` 能避免純軟體 SwiftShader 卡死，搭配 `--gpu` 可直接硬編輸出段落 MP4。
   - 若要客製額外 Worker 數，可在 HyperFrames 場景目錄執行專案根目錄的 `node_modules\.bin\hyperframes.cmd render --workers 4 --gpu --browser-gpu`；請依場景目錄位置指定該執行檔的正確路徑。
4. **確定性 vs 編碼速度取捨**：
   - 若要減少硬體差異，請以固定版本工具、字型與輸入素材測試，並使用 `$env:VC_GPU="off"` 或 `--no-gpu`。停用 GPU 不保證不同平台的 MP4 位元完全相同；可另比對影格數、解析度、響度與指定影格。
