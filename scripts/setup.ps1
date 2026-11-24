# 在專案資料夾內重建整個環境（虛擬環境、FFmpeg、Node 工具、模型）。
# 用法：在 Video_Creator 目錄執行 powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 [-CpuOnly]
# 所有檔案都裝在專案內：.venv\、tools\ffmpeg\、node_modules\、remotion\node_modules\、models\
param([switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host '[1/6] Python 3.11 虛擬環境'
if (-not (Test-Path .venv\Scripts\python.exe)) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 before setup.' }
}
$py = Join-Path $root '.venv\Scripts\python.exe'
& $py -m ensurepip --upgrade
if ($LASTEXITCODE -ne 0) { throw 'Cannot prepare pip.' }
& $py -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) { throw 'Cannot update pip.' }

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
if ($LASTEXITCODE -ne 0) { throw 'Cannot install PyTorch.' }

Write-Host '[3/6] 其他 Python 套件'
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Cannot install Python dependencies.' }
& $py -c "import nltk, sys; sys.exit(0 if nltk.download('cmudict', download_dir='.venv/nltk_data', quiet=True) else 1)"
if ($LASTEXITCODE -ne 0) { throw 'Cannot install the pronunciation dictionary.' }

Write-Host '[4/6] FFmpeg（gyan.dev essentials，解壓到 tools\ffmpeg）'
if (-not (Test-Path tools\ffmpeg\bin\ffmpeg.exe)) {
    New-Item -ItemType Directory -Force tools | Out-Null
    curl.exe -L --fail -o tools\ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    Expand-Archive tools\ffmpeg.zip -DestinationPath tools\_ffx -Force
    Move-Item (Get-ChildItem tools\_ffx -Directory | Select-Object -First 1).FullName tools\ffmpeg
    Remove-Item tools\_ffx, tools\ffmpeg.zip -Recurse -Force
}

Write-Host '[5/6] Node 工具（HyperFrames、capcut-cli、Remotion）'
cmd /c "npm ci --no-fund --no-audit"
if ($LASTEXITCODE -ne 0) { throw 'Cannot install Node dependencies.' }
cmd /c "node_modules\.bin\hyperframes.cmd telemetry disable"

Write-Host '[6/6] 下載模型並做冒煙測試'
& $py scripts\smoke_models.py
if ($LASTEXITCODE -ne 0) { throw 'The model smoke test failed.' }
& $py -m vc doctor --deep
if ($LASTEXITCODE -ne 0) { throw 'The environment check failed.' }
