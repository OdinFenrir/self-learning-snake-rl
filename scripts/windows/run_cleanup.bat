@echo off
setlocal

set "ROOT=%~dp0..\..\"
cd /d "%ROOT%"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "SCRIPT=%ROOT%scripts\cleanup_workspace.py"

if not exist "%PYTHON%" (
  echo Python not found at "%PYTHON%".
  exit /b 1
)
if not exist "%SCRIPT%" (
  echo Script not found at "%SCRIPT%".
  exit /b 1
)

set "MODE=%~1"
if /I "%MODE%"=="apply" goto APPLY
if /I "%MODE%"=="aggressive" goto AGGR
if /I "%MODE%"=="last" goto LAST

echo Running safe cleanup dry-run...
"%PYTHON%" "%SCRIPT%" --root "%ROOT%"
echo.
echo To apply safe cleanup: scripts\windows\run_cleanup.bat apply
echo To apply aggressive cleanup: scripts\windows\run_cleanup.bat aggressive
echo To apply cleanup + keep only latest checkpoint: scripts\windows\run_cleanup.bat last
goto END

:APPLY
echo Applying safe cleanup...
"%PYTHON%" "%SCRIPT%" --root "%ROOT%" --apply
goto END

:AGGR
echo Applying aggressive cleanup...
"%PYTHON%" "%SCRIPT%" --root "%ROOT%" --aggressive --apply
goto END

:LAST
echo Applying cleanup and pruning old checkpoints (keep latest only)...
"%PYTHON%" "%SCRIPT%" --root "%ROOT%" --apply --last-run-only
goto END

:END
endlocal
