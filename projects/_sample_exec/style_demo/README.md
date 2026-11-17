# 風格與運鏡示範專案

本範例用同一段文案與同一張自製簡報，產生商務藍、瑞士極簡，以及瑞士極簡加電影推鏡三個版本。素材不含真實客戶資料。

## 輸入

- `project.yaml`：目前選用的風格與運鏡。
- `script.json`：旁白、字卡與素材參照。
- `facts.yaml`：本範例沒有數值事實。
- `input/slides/style_demo.pptx`：自製的單頁簡報。
- `input/camera_plans/cinematic_dolly.json`：5.5 秒推鏡設定。
- `variants/`：三組可直接複製到 `project.yaml` 的設定。

## 執行

在專案根目錄執行以下命令。每個變體都使用同一份輸入。

```powershell
$project = 'projects/_sample_exec/style_demo'
$env:NLTK_DATA = Join-Path (Get-Location) '.pytest_cache/nltk_data'
.venv\Scripts\python.exe -m vc doctor
.venv\Scripts\python.exe -m vc validate $project
.venv\Scripts\python.exe -m vc ingest-ppt $project
.venv\Scripts\python.exe -m vc voice $project --preview
.venv\Scripts\python.exe -m vc align $project
.venv\Scripts\python.exe -m vc plan $project

Copy-Item "$project/variants/executive_navy_fixed.yaml" "$project/project.yaml" -Force
.venv\Scripts\python.exe -m vc hf $project
.venv\Scripts\python.exe -m vc render $project --variant all --name executive_navy_fixed

Copy-Item "$project/variants/swiss_kinetic_fixed.yaml" "$project/project.yaml" -Force
.venv\Scripts\python.exe -m vc hf $project
.venv\Scripts\python.exe -m vc render $project --variant public --name swiss_kinetic_fixed

Copy-Item "$project/variants/swiss_kinetic_cinematic.yaml" "$project/project.yaml" -Force
.venv\Scripts\python.exe -m vc hf $project
.venv\Scripts\python.exe -m vc render $project --variant public --name swiss_kinetic_cinematic
```

影片寫入 `output/internal/` 與 `output/public/`。時間軸與預覽寫入 `work/`。請以輸出影片影格和 `work/hf/public/s01/index.html` 核對風格與運鏡差異。
