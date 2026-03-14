@echo off
setlocal
cd /d "%~dp0"
call scripts\windows\run_policy_3d.bat %*
endlocal
