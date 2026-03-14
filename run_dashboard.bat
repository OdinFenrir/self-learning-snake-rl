@echo off
setlocal
cd /d "%~dp0"
call scripts\windows\run_dashboard.bat %*
endlocal
