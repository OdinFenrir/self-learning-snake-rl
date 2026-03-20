@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  set "PY_EXE=.venv\Scripts\python.exe"
) else (
  set "PY_EXE=python"
)

echo Running quick reliability gate...
"%PY_EXE%" scripts\quick_gate.py --cycles 5
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo.
  echo quick_gate FAILED with exit code %RC%.
  pause
  exit /b %RC%
)

echo.
echo quick_gate PASSED.
pause
exit /b 0
