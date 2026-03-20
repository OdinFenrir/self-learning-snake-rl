@echo off
setlocal
cd /d "%~dp0\..\.."

if exist ".venv\Scripts\python.exe" (
  set "PY_EXE=.venv\Scripts\python.exe"
) else (
  set "PY_EXE=python"
)

"%PY_EXE%" scripts\quick_gate.py --cycles 5
set RC=%ERRORLEVEL%
if not "%RC%"=="0" exit /b %RC%
exit /b 0
