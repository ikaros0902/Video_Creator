# 測試與驗證

在專案根目錄執行：

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m vc validate _sample
.venv\Scripts\python.exe -m vc validate _sample_exec
```

預設測試排除標記為 `integration` 的案例。執行結果須分別記錄通過、失敗、跳過與未選取的數量；結束碼為零不代表未執行的案例已通過。

整合測試需要實際素材或已建立產物的專案。可設定 `VC_PIPELINE_PROJECT` 指向已準備好的管線專案，或設定 `VC_SHOWCASE_PROJECT` 指向示範專案，再選取適當的整合測試。測試標記與預設選項見 [`pytest.ini`](pytest.ini)。

`projects/_sample` 與 `projects/_sample_exec` 是可驗證的腳本範例；倉庫未提供完整的簡報、錄影或影片成品。完整渲染與音訊模型測試需要另外準備素材和環境。
