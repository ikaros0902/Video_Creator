# 快速上手與 CLI 使用手冊（`00_docs/00_how_to_use.md`）

本指南幫您在 10 分鐘內完成環境檢查、跑通脫敏範例專案，並產出第一支程式驅動的教學影片。

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
   Copy-Item -Recurse projects/_sample projects/my_video
   ```
2. **放入原始素材並設定 `project.yaml`**：把 `.pptx` 與 `.mp4` 錄影放進 `projects/my_video/input/`，並更新 `project.yaml` 的路徑。
3. **提取素材資訊**：
   ```powershell
   .venv\Scripts\python.exe -m vc ingest-ppt my_video
   .venv\Scripts\python.exe -m vc ingest-rec my_video
   ```
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
   輸出成品位於 `projects/my_video/output/v1.mp4`。舊雙版本專案先執行 `python -m vc migrate my_video`；原始腳本會備份為 `script.json.bak`。舊版匯入與中間檔不含來源指紋，請依序重新匯入素材並重跑旁白、對齊、時間軸及所需場景。

## 3. 完整 CLI 指令一覽（12 個子指令）

| 指令 | 說明 | 常用選項 |
| :--- | :--- | :--- |
| `python -m vc doctor` | 檢查 Python、CUDA GPU、FFmpeg NVENC、Node、HyperFrames 與 Remotion | `--deep`（做即時連網與完整環境檢查） |
| `python -m vc ingest-ppt <proj>` | 從簡報抽取出每頁投影片高清截圖與備忘稿文字 | 無 |
| `python -m vc ingest-rec <proj>` | 掃描螢幕錄影解析度、鏡頭切換點與活動接觸表 | 無 |
| `python -m vc validate <proj>` | 檢查數字來源、詞彙順序、句子長度與 FK 易讀等級 | 無（必須通過才可往下做） |
| `python -m vc voice <proj>` | 使用 Kokoro 或 Edge TTS 生成各段 48kHz 旁白 | 支援內容雜湊快取，未修改的段落不重算 |
| `python -m vc align <proj>` | 使用 Whisper 取得逐字時間戳並產生 SRT 字幕 | `--cuda` 自動感測，詳見 GPU 手冊 |
| `python -m vc plan <proj>` | 依旁白字詞時間算出零誤差影格時間軸 `timeline.json` | 檢查錄影變速是否超出 2.5x 上限 |
| `python -m vc manim <proj>` | 算圖 `kind=manim` 的向量教學場景並轉為目標影格數 | `--scene s04` `--no-gpu` |
| `python -m vc hf <proj>` | 生成並算圖 `kind=anim` 的 HTML/GSAP HyperFrames 場景 | `--quality draft` `--no-gpu` |
| `python -m vc fit <proj>` | 依時間軸剪輯、裁切並智慧變速所有錄影片段 | `--no-gpu` |
| `python -m vc render <proj>` | 由 Remotion 總裝並以預設 `-14 LUFS` 標準化，可於專案設定覆寫 | `--name v1` `--no-gpu` |
| `python -m vc capcut-draft <proj>` | 匯出剪映 / CapCut 草稿工程檔供進階人工潤飾 | 無 |
