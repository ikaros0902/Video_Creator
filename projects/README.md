# projects — 專案資料夾規範與範例

每個獨立影片專案都放在 `projects/<project_name>/` 底下。

## 為什麼正式專案不上傳 GitHub？

依據 `.gitignore` 設定：
- `projects/*` 預設全部忽略，**只保留本說明與 `_sample/`、`_sample_exec/` 兩個去敏化範例專案**。
- 您的實際錄影、簡報投影片、公司 Logo 與機密專案數據留在 `projects/<your_project>/` 本機磁碟，**不會被推上遠端倉庫**。

## 建立新專案的最快方式

1. 複製範例專案：
   ```powershell
   Copy-Item -Recurse projects/_sample projects/my_video
   ```
2. 將您的 `.pptx` 與錄影 `.mp4` 放入 `projects/my_video/input/`。
3. 更新 `project.yaml`、`facts.yaml` 與 `script.json`。
4. 執行前置檢查門禁：
   ```powershell
   .venv\Scripts\python.exe -m vc validate my_video
   ```
