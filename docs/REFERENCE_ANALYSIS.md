# 本機參考影片分析

這個功能以 rea-video 拆解本機影片，輸出逐鏡分析、圖片總覽與報告。結果中的製作方法與來源判斷仍需人工確認，不會自動寫入 `facts.yaml`。

先執行一次獨立安裝：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-reference.ps1
```

工具固定在上游版本 `bc97f214ebedfdc6510a9b2241cd8f8222f63517`，安裝至 `tools/rea-video/.venv`，不與主環境共用 OpenCV。程式碼來源：[rea-video](https://github.com/JuneYaooo/rea-video)。

分析已取得的本機影片：

```powershell
.venv\Scripts\python.exe -m vc.reference my_video C:\Videos\reference.mp4 --name reference_01
```

結果保存在 `projects/my_video/work/references/reference_01/`。開啟 `report.html` 查看報告，或讀取 `VIDEO.md` 逐層查閱。`analysis.json` 記錄原始檔案指紋、固定工具版本與待人工確認狀態。

分析明確停用雲端視覺模型，並使用獨立偏好目錄。模型首次下載需要網路，推論在本機執行。沒有安裝工具、影片損毀或報告不完整時，命令回傳非零狀態；失敗產物保留供診斷。相同名稱不會被覆寫，請使用另一個 `--name`。

本功能不會下載 YouTube 影片或複製他人影片素材。請提供你可使用的本機檔案，依據分鏡與節奏建立自己的內容。
