# 新影片專案端到端實戰 SOP

依序準備素材、驗證腳本並執行以下命令，產生單一版本的影片。範例未附帶簡報和錄影，請自行準備。

## 步驟 0：檢查環境與 GPU 就緒狀態

```powershell
.venv\Scripts\python.exe -m vc doctor
```
確認必要項目通過。CUDA 和硬體編碼為選用項目；不可用時可使用 CPU。

## 步驟 1：建立專屬專案資料夾

```powershell
Copy-Item -Recurse projects/_sample projects/my_demo
```
將原始 `.pptx` 與 `.mp4` 錄影放入 `projects/my_demo/input/`（此資料夾會自動被 Git 忽略），並更新 `project.yaml`。

## 步驟 2：提取素材特徵（不複製大檔）

```powershell
.venv\Scripts\python.exe -m vc ingest-ppt my_demo
.venv\Scripts\python.exe -m vc ingest-rec my_demo
```
產物會寫入 `work/slides/`（投影片 png）與 `work/recordings.json`（每支錄影精確解析度、幀率、總長與縮圖接觸表），方便挑選時間點。

## 步驟 3：填寫事實表並驗證腳本門禁

編輯 `facts.yaml` 與 `script.json` 後執行：
```powershell
.venv\Scripts\python.exe -m vc validate my_demo
```
直到出現零錯誤為止。

## 步驟 4：產生高品質配音（Kokoro / Edge）

```powershell
.venv\Scripts\python.exe -m vc voice my_demo --preview
```
會自動略過未更動的段落並產出串接試聽檔，先聽語速與發音（難字可在 `lexicon` 補音標替換）。

## 步驟 5：Whisper 逐字對齊與字幕切分

```powershell
.venv\Scripts\python.exe -m vc align my_demo
```
產生 `work/align/words.json` 與 `work/align/preview.srt`。動畫 `at_word` 觸發點依據對齊結果計算。

## 步驟 6：建置零漂移影格時間軸

```powershell
.venv\Scripts\python.exe -m vc plan my_demo
```
將所有秒數轉換為 30 fps 精確影格，並檢查錄影片段是否超過 2.5 倍速限制。

## 步驟 7：算圖三大視覺軌道（可平行執行）

```powershell
.venv\Scripts\python.exe -m vc manim my_demo
.venv\Scripts\python.exe -m vc hf my_demo
.venv\Scripts\python.exe -m vc fit my_demo
```
- `manim` 與 `fit` 預設啟用 `h264_nvenc` GPU 壓縮；`hf` 預設啟用 `--gpu --browser-gpu`。若要關閉硬體加速可加上 `--no-gpu`。

## 步驟 8：總裝算圖與響度標準化

```powershell
.venv\Scripts\python.exe -m vc render my_demo --name v1
```
輸出位於 `projects/my_demo/output/v1.mp4`。預設目標響度為 -14 LUFS，可在專案設定中調整。

## 步驟 9：（選配）匯出剪映 / CapCut 草稿做手動精修

```powershell
.venv\Scripts\python.exe -m vc capcut-draft my_demo
```
