@echo off
setlocal
cd /d "%~dp0"
call scripts\windows\run_postrun_suite.bat %*
endlocal
