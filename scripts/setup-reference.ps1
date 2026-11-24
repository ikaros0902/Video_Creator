# 將參考影片工具固定在獨立環境，避免 OpenCV 相依套件互相覆蓋。
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$root = Split-Path -Parent $PSScriptRoot
$toolRoot = Join-Path $root 'tools\rea-video'
$source = Join-Path $toolRoot 'source'
$revision = 'bc97f214ebedfdc6510a9b2241cd8f8222f63517'
$basePython = Join-Path $root '.venv\Scripts\python.exe'
$toolPython = Join-Path $toolRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $basePython)) { throw 'Run scripts/setup.ps1 first.' }
New-Item -ItemType Directory -Force $toolRoot | Out-Null
if (-not (Test-Path -LiteralPath $source)) {
    git clone --no-checkout https://github.com/JuneYaooo/rea-video.git $source
    if ($LASTEXITCODE -ne 0) { throw 'Cannot download rea-video.' }
}
git -C $source checkout --detach $revision
if ($LASTEXITCODE -ne 0) { throw 'Cannot select the pinned rea-video revision.' }
if (-not (Test-Path -LiteralPath $toolPython)) {
    & $basePython -m venv (Join-Path $toolRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create the isolated tool environment.' }
}
& $toolPython -m pip install $source
if ($LASTEXITCODE -ne 0) { throw 'Cannot install rea-video dependencies.' }
& (Join-Path $toolRoot '.venv\Scripts\rea-video.exe') --help
if ($LASTEXITCODE -ne 0) { throw 'The rea-video command failed.' }
Write-Host 'Local analysis is ready. Models download on the first analysis.'
