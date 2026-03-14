@echo off
setlocal

set "ROOT=%~dp0..\..\"
cd /d "%ROOT%"

if exist "%ROOT%.venv\Scripts\python.exe" (
  powershell -ExecutionPolicy Bypass -File "%ROOT%scripts\test_dashboard.ps1" -Python "%ROOT%.venv\Scripts\python.exe" %*
) else (
  powershell -ExecutionPolicy Bypass -File "%ROOT%scripts\test_dashboard.ps1" -Python python %*
)

endlocal
