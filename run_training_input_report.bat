@echo off
setlocal
cd /d "%~dp0"
call scripts\windows\run_training_input_report.bat %*
endlocal

