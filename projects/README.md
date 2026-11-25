# projects — 專案資料夾規範與範例

每個獨立影片專案都放在 `projects/<project_name>/` 底下。

## 範例腳本在哪裡？

| 範例 | 腳本 | 說明 |
| :--- | :--- | :--- |
| 七段標準教學 | [`_sample/script.json`](_sample/script.json) | 旁白、單一畫面與素材參照 |
| 五段主管摘要 | [`_sample_exec/script.json`](_sample_exec/script.json) | 開啟逐段事實與數字驗證 |
| 風格與運鏡示範 | [`_sample_exec/style_demo/script.json`](_sample_exec/style_demo/script.json) | 配合 `variants/` 比較風格設定 |

各腳本同目錄的 `facts.yaml` 記錄數據來源，`project.yaml` 指定素材與風格。範例未附帶完整原始簡報、錄影或成品。先閱讀各範例 README，再準備自己的素材。

## 為什麼正式專案不上傳 GitHub？

依據 `.gitignore` 設定：

- `projects/*` 預設全部忽略，**只保留本說明與 `_sample/`、`_sample_exec/` 兩個去敏化範例專案**。
- 您的實際錄影、簡報投影片、公司 Logo 與機密專案數據留在 `projects/<your_project>/` 本機磁碟，**不會被推上遠端倉庫**。

## 建立新專案的最快方式

1. 複製範例專案：
   ```powershell
   Copy-Item -Recurse projects\_sample projects\my_video
   ```
2. 將您的 `.pptx` 與錄影 `.mp4` 放入 `projects/my_video/input/`。
3. 更新 `project.yaml`、`facts.yaml` 與 `script.json`。
4. 執行前置檢查門禁：
   ```powershell
   .venv\Scripts\python.exe -m vc validate my_video
   ```

完整製作步驟見[使用指南](../docs/00_how_to_use.md)。單一影片成品位於 `projects/my_video/output/<name>.mp4`。`work/` 保存旁白、時間軸與中間素材；`design/` 保存靈感與風格調整資料。
