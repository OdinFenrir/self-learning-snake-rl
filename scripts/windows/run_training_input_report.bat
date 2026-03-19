@echo off
setlocal

set "ROOT=%~dp0..\..\"
cd /d "%ROOT%"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "SCRIPT_REPORT=%ROOT%scripts\training_input\build_training_input_report.py"
set "SCRIPT_TIMELINE=%ROOT%scripts\training_input\build_training_input_timeline.py"
set "SCRIPT_VISUALS=%ROOT%scripts\training_input\build_training_input_visuals.py"
set "SCRIPT_HUB=%ROOT%scripts\reporting\build_reports_hub.py"
set "DASH_HTML=%ROOT%artifacts\training_input\training_input_dashboard_latest.html"

if not exist "%PYTHON%" (
  echo Python not found at "%PYTHON%".
  exit /b 1
)
if not exist "%SCRIPT_REPORT%" (
  echo Script not found at "%SCRIPT_REPORT%".
  exit /b 1
)
if not exist "%SCRIPT_TIMELINE%" (
  echo Script not found at "%SCRIPT_TIMELINE%".
  exit /b 1
)
if not exist "%SCRIPT_VISUALS%" (
  echo Script not found at "%SCRIPT_VISUALS%".
  exit /b 1
)
if not exist "%SCRIPT_HUB%" (
  echo Script not found at "%SCRIPT_HUB%".
  exit /b 1
)

echo Building training-input report...
"%PYTHON%" "%SCRIPT_REPORT%" --out-dir artifacts\training_input --tag latest %*
if errorlevel 1 exit /b 1
echo Building training-input timeline...
"%PYTHON%" "%SCRIPT_TIMELINE%" --out-dir artifacts\training_input --tag latest %*
if errorlevel 1 exit /b 1
echo Building training-input dashboard...
"%PYTHON%" "%SCRIPT_VISUALS%" --in-dir artifacts\training_input --out-dir artifacts\training_input --tag latest
if errorlevel 1 exit /b 1
echo Building reports hub...
"%PYTHON%" "%SCRIPT_HUB%" --artifacts-root artifacts --out-dir artifacts\reports
if errorlevel 1 exit /b 1

echo.
echo Done. Outputs:
echo   artifacts\training_input\training_input_latest.json
echo   artifacts\training_input\training_input_latest.md
echo   artifacts\training_input\training_input_checkpoint_vecnorm_latest.csv
echo   artifacts\training_input\training_input_timeline_latest.json
echo   artifacts\training_input\training_input_timeline_latest.md
echo   artifacts\training_input\training_input_timeline_latest.csv
echo   artifacts\training_input\training_input_dashboard_latest.html
echo   artifacts\reports\reports_hub_latest.md
echo   artifacts\reports\reports_hub_latest.txt

if exist "%DASH_HTML%" (
  start "" "%DASH_HTML%"
)

endlocal
