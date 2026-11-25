# 風格與運鏡示範專案

本範例用同一段文案比較商務藍、瑞士極簡，以及瑞士極簡加電影推鏡三組設定。每次執行只輸出一支影片，不再區分 internal 與 public。

旁白與單一畫面設定位於 [`script.json`](script.json)。倉庫保留文字與運鏡設定，但未附帶 `input/slides/style_demo.pptx`，執行前需準備自己的單頁簡報或更新 `project.yaml` 指向有效素材。

## 輸入

- `project.yaml`：目前選用的風格與運鏡。
- `script.json`：旁白、字卡與素材參照。
- `facts.yaml`：本範例沒有數值事實。
- `input/slides/style_demo.pptx`：需自行提供的單頁簡報。
- `input/camera_plans/cinematic_dolly.json`：5.5 秒推鏡設定。
- `variants/`：三組可直接複製到 `project.yaml` 的設定。

## 執行

在專案根目錄執行以下命令。每個變體都使用同一份輸入。

```powershell
$project = 'projects/_sample_exec/style_demo'
.venv\Scripts\python.exe -m vc doctor
.venv\Scripts\python.exe -m vc ingest-ppt $project
.venv\Scripts\python.exe -m vc validate $project
.venv\Scripts\python.exe -m vc voice $project --preview
.venv\Scripts\python.exe -m vc align $project

Copy-Item "$project/variants/executive_navy_fixed.yaml" "$project/project.yaml" -Force
.venv\Scripts\python.exe -m vc plan $project
.venv\Scripts\python.exe -m vc hf $project
.venv\Scripts\python.exe -m vc render $project --name executive_navy_fixed

Copy-Item "$project/variants/swiss_kinetic_fixed.yaml" "$project/project.yaml" -Force
.venv\Scripts\python.exe -m vc plan $project
.venv\Scripts\python.exe -m vc hf $project
.venv\Scripts\python.exe -m vc render $project --name swiss_kinetic_fixed

Copy-Item "$project/variants/swiss_kinetic_cinematic.yaml" "$project/project.yaml" -Force
.venv\Scripts\python.exe -m vc plan $project
.venv\Scripts\python.exe -m vc hf $project
.venv\Scripts\python.exe -m vc render $project --name swiss_kinetic_cinematic
```

影片寫入本範例的 `output/<name>.mp4`，時間軸與預覽寫入 `work/`。每次切換風格後都需重跑 `plan` 與 `hf`，避免沿用舊畫面。可用 `work/hf/main/s01/index.html` 核對生成的場景來源，再檢視實際影片。
