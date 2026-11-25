# 快速上手與 CLI 使用手冊

本指南說明環境檢查、範例腳本與單一影片輸出流程。所有命令都在倉庫根目錄執行。

## 範例腳本位置

| 用途 | 可編輯腳本 | 相關設定 |
| :--- | :--- | :--- |
| 七段標準教學 | [`projects/_sample/script.json`](../projects/_sample/script.json) | 同目錄的 `facts.yaml`、`project.yaml` |
| 五段主管摘要 | [`projects/_sample_exec/script.json`](../projects/_sample_exec/script.json) | 同目錄的 `facts.yaml`、`project.yaml` |
| 風格與運鏡示範 | [`projects/_sample_exec/style_demo/script.json`](../projects/_sample_exec/style_demo/script.json) | 執行方式見[範例說明](../projects/_sample_exec/style_demo/README.md) |

`_sample` 與 `_sample_exec` 保留文字設定，未附帶原始簡報與錄影。它們可直接驗證腳本；若要渲染，請先補齊素材或改寫對應場景。

## 1. 環境確認（第一次使用先執行）

```powershell
# 若尚未安裝依賴，先執行一次自動化安裝（會自動偵測 NVIDIA GPU）
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

# 檢查所有核心工具與 GPU 是否就緒
.venv\Scripts\python.exe -m vc doctor
```

常見問題與解決方式見 [`02_requirements_guide.md`](02_requirements_guide.md)。

## 2. 一條龍製作新影片（5 步驟）

1. **複製範例專案**：
   ```powershell
   Copy-Item -Recurse projects\_sample projects\my_video
   ```
2. **放入原始素材並設定 `project.yaml`**：把 `.pptx` 與 `.mp4` 錄影放進 `projects/my_video/input/`，並更新 `project.yaml` 的路徑。
3. **提取素材資訊**：
   ```powershell
   .venv\Scripts\python.exe -m vc ingest-ppt my_video
   .venv\Scripts\python.exe -m vc ingest-rec my_video
   ```
   只執行有設定來源的匯入命令。沒有簡報的專案可略過 `ingest-ppt`；沒有錄影可略過 `ingest-rec`。
4. **填寫 `facts.yaml` 與 `script.json` 並通過驗證門禁**：
   ```powershell
   .venv\Scripts\python.exe -m vc validate my_video
   ```
5. **執行確定性合成管線**：
   ```powershell
   .venv\Scripts\python.exe -m vc voice my_video
   .venv\Scripts\python.exe -m vc align my_video
   .venv\Scripts\python.exe -m vc plan my_video
   .venv\Scripts\python.exe -m vc manim my_video
   .venv\Scripts\python.exe -m vc hf my_video
   .venv\Scripts\python.exe -m vc fit my_video
   .venv\Scripts\python.exe -m vc render my_video --name v1
   ```
   只需執行腳本實際使用的場景步驟：`kind=manim` 使用 `manim`，`kind=anim` 使用 `hf`，錄影片段使用 `fit`。
   輸出成品位於 `projects/my_video/output/v1.mp4`。舊雙版本專案先執行 `python -m vc migrate my_video`；原始腳本會備份為 `script.json.bak`。舊版匯入與中間檔不含來源指紋，請依序重新匯入素材並重跑旁白、對齊、時間軸及所需場景。

## 3. CLI 指令一覽

| 指令 | 說明 | 常用選項 |
| :--- | :--- | :--- |
| `python -m vc doctor` | 檢查 Python、CUDA GPU、FFmpeg NVENC、Node、HyperFrames 與 Remotion | `--deep`（做即時連網與完整環境檢查） |
| `python -m vc ingest-ppt <proj>` | 抽取簡報文字、圖片與備忘稿；有 PowerPoint 時可匯出整頁預覽 | `--no-preview` |
| `python -m vc ingest-rec <proj>` | 掃描錄影解析度、鏡頭切換點與活動接觸表 | `--every 2` |
| `python -m vc validate <proj>` | 檢查數字來源、詞彙順序、句子長度與 FK 易讀等級 | 無（必須通過才可往下做） |
| `python -m vc voice <proj>` | 使用 Kokoro 或 Edge TTS 生成各段 48kHz 旁白 | 支援內容雜湊快取，未修改的段落不重算 |
| `python -m vc align <proj>` | 使用 Whisper 取得逐字時間戳並產生 SRT 字幕 | 自動選擇推論裝置 |
| `python -m vc plan <proj>` | 依旁白字詞時間算出零誤差影格時間軸 `timeline.json` | 檢查錄影變速是否超出 2.5x 上限 |
| `python -m vc manim <proj>` | 算圖 `kind=manim` 的向量教學場景並轉為目標影格數 | `--scene s04` `--no-gpu` |
| `python -m vc hf <proj>` | 生成並算圖 `kind=anim` 的 HTML/GSAP HyperFrames 場景 | `--quality draft` `--no-gpu` |
| `python -m vc fit <proj>` | 依時間軸剪輯、裁切並智慧變速所有錄影片段 | `--no-gpu` |
| `python -m vc render <proj>` | 由 Remotion 總裝並以預設 `-14 LUFS` 標準化，可於專案設定覆寫 | `--name v1` `--no-gpu` |
| `python -m vc capcut-draft <proj>` | 匯出剪映 / CapCut 草稿工程檔供進階人工潤飾 | 無 |
| `python -m vc migrate <proj>` | 備份舊雙版本腳本，轉為單一 `visual` 格式 | 不覆寫既有 `.bak` |
| `python -m vc creative …` | 記錄設計簡報、匯入靈感、比較風格與調整排版 | 見[設計工作區](creative_tools.md) |
| `python -m vc reference <proj> <video>` | 在隔離工具環境拆解本機參考影片 | 見[分析指南](REFERENCE_ANALYSIS.md) |
