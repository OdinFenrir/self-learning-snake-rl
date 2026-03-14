param(
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Python)) {
    throw "Python interpreter not found at $Python"
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --name SnakeFrame `
  --windowed `
  --collect-submodules stable_baselines3 `
  --collect-submodules gymnasium `
  --collect-submodules torch `
  main.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

Write-Host "Build complete: dist\SnakeFrame\SnakeFrame.exe"
