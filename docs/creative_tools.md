# 本機設計工作區

使用靈感資料、受眾與設計理由選擇風格。所有資料保存在影片專案內，工具不呼叫雲端模型。

在倉庫根目錄執行以下命令。`my_video` 代表已建立的影片專案。

```powershell
.venv\Scripts\python.exe -m vc.creative brief my_video --audience "工程師" --purpose "理解操作流程" --message "看懂輸入、操作和結果" --avoid "過量裝飾動畫"
.venv\Scripts\python.exe -m vc.creative import my_video "D:\references\layout.png" --title "資訊層級參考" --origin "原始網址或來源說明" --notes "只參考標題和內文比例" --tag 排版
.venv\Scripts\python.exe -m vc.creative preview my_video --scene s01
.venv\Scripts\python.exe -m vc.creative serve my_video --scene s01
```

`preview` 產生 `work/design/preview.html`，可離線開啟。檔案預覽無法儲存專案設定。`serve` 顯示本機網址，開啟後可調整風格並明確儲存。以 Ctrl+C 停止工作區。

可用 `--styles executive_navy swiss_kinetic blueprint` 指定一至六個方向。自訂風格 JSON 必須位於目前影片專案內。

工作區使用目前場景的標題、副標題與旁白，比較文字排版、色彩與字體。它不是最終影片播放器，動畫、錄影與聲音仍需以實際渲染結果審查。

調整字體、字級、標題比例、行高、字距、內容間距、安全邊界與色彩後，檢查越界、重疊、過小字級和低對比。選擇「預覽邊界修正」只會嘗試縮減間距或字級。內容過長、語意取捨或風格好壞仍需人工判斷。

「儲存並套用風格」需要選擇理由。工具會先備份設定，再儲存 `design/style.json` 並更新 `project.yaml` 的 `style` 路徑。HyperFrames 基礎文字套用行高與字距；標題範本另套用內容間距與字級。其他範本的固定尺寸、Manim 與錄影畫面不一定套用所有控制項，必須檢查實際影片。風格變更後需重新執行 `vc plan` 和相關渲染命令。未按儲存前，控制項只改變預覽。

| 資料 | 路徑 | 用途 |
|---|---|---|
| 設計簡報 | `design/brief.json` | 受眾、目的、主要訊息和避免事項 |
| 靈感來源 | `design/library/<id>/` | 原始資產複本、來源、人工註記、標籤和內容雜湊 |
| 專案風格 | `design/style.json` | 可重用的風格參數 |
| 選擇理由 | `design/selection.json` | 風格選擇與儲存時間 |
| 修改前資料 | `design/backups/<time>_<id>/` | 每次儲存前的設定複本 |

匯入同一個來源兩次會保留兩份獨立紀錄，不會覆寫先前資料。來源檔案只接受明確指定的本機圖片、影片、文字與報告，匯入不會執行 HTML 或分析報告。人工註記不代表事實已確認，影片數據仍須記錄於 `facts.yaml` 並通過驗證。

若要還原設定，先停止工作區，再從選定的備份資料夾取回 `project.yaml`、`style.json` 或 `selection.json`。風格檔回到 `design` 目錄，專案設定回到專案根目錄。
