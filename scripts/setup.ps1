# 在專案資料夾內重建整個環境（虛擬環境、FFmpeg、Node 工具、模型）。
# 用法：在 Video_Creator 目錄執行  powershell -ExecutionPolicy Bypass -File 09_scripts\setup.ps1 [-CpuOnly]
# 所有檔案都裝在專案內：.venv\、tools\ffmpeg\、node_modules\、remotion\node_modules\、models\
param([switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host '[1/6] Python 3.11 虛擬環境'
if (-not (Test-Path .venv\Scripts\python.exe)) { py -3.11 -m venv .venv }
$py = Join-Path $root '.venv\Scripts\python.exe'
& $py -m pip install --upgrade pip --quiet

$hasNvidia = $false
if (-not $CpuOnly -and (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
    nvidia-smi | Out-Null
    if ($LASTEXITCODE -eq 0) { $hasNvidia = $true }
}
if ($hasNvidia) {
    Write-Host '[2/6] CUDA 版 PyTorch（cu126，驅動需 >= 525）'
    & $py -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cu126
} else {
    Write-Host '[2/6] CPU 版 PyTorch（未偵測到 NVIDIA GPU 或指定 -CpuOnly）'
    & $py -m pip install torch==2.14.1
}

Write-Host '[3/6] 其他 Python 套件'
& $py -m pip install -r requirements.txt

Write-Host '[4/6] FFmpeg（gyan.dev essentials，解壓到 tools\ffmpeg）'
if (-not (Test-Path tools\ffmpeg\bin\ffmpeg.exe)) {
    New-Item -ItemType Directory -Force tools | Out-Null
    curl.exe -L --fail -o tools\ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    Expand-Archive tools\ffmpeg.zip -DestinationPath tools\_ffx -Force
    Move-Item (Get-ChildItem tools\_ffx -Directory | Select-Object -First 1).FullName tools\ffmpeg
    Remove-Item tools\_ffx, tools\ffmpeg.zip -Recurse -Force
}

Write-Host '[5/6] Node 工具（HyperFrames、capcut-cli、Remotion）'
cmd /c "npm install --no-fund --no-audit"
Push-Location remotion
cmd /c "npm install --no-fund --no-audit"
Pop-Location
cmd /c "node_modules\.bin\hyperframes.cmd telemetry disable"

Write-Host '[6/6] 下載模型並做冒煙測試'
& $py 09_scripts\smoke_models.py
& $py -m vc doctor --deep
