@echo off
setlocal

cd /d "%~dp0"

set "PY_CMD=.venv\Scripts\python.exe"
if not exist "%PY_CMD%" (
  call setup_env.bat
  if errorlevel 1 (
    echo Failed to set up the environment.
    pause
    exit /b 1
  )
)

set "VENV_VER="
"%PY_CMD%" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" > .venv_version.tmp
if exist .venv_version.tmp (
  set /p VENV_VER=<.venv_version.tmp
  del /q .venv_version.tmp >nul 2>nul
)
if not "%VENV_VER%"=="3.12" (
  echo .venv uses Python %VENV_VER%, expected 3.12. Rebuilding...
  call setup_env.bat
  if errorlevel 1 (
    echo Failed to rebuild environment with Python 3.12.
    pause
    exit /b 1
  )
)

"%PY_CMD%" -c "import pygame, numpy, gymnasium, stable_baselines3, torch" >nul 2>nul
if errorlevel 1 (
  echo Dependencies missing or corrupted. Reinstalling...
  call setup_env.bat
  if errorlevel 1 (
    echo Environment repair failed.
    pause
    exit /b 1
  )
  "%PY_CMD%" -c "import pygame, numpy, gymnasium, stable_baselines3, torch" >nul 2>nul
  if errorlevel 1 (
    echo Dependencies still unavailable after repair.
    pause
    exit /b 1
  )
)

"%PY_CMD%" -c "import sys, importlib.metadata as m; print('Python', sys.version.split()[0], 'pygame', m.version('pygame'))"
if errorlevel 1 (
  echo Could not print runtime versions.
  pause
  exit /b 1
)

"%PY_CMD%" main.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Snake frame exited with code %EXIT_CODE%.
  pause
)

exit /b %EXIT_CODE%
