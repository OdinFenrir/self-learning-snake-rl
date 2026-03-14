@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE="
set "PYTHON_VERSION=3.12"

where py >nul 2>nul
if not errorlevel 1 (
  for /f "delims=" %%i in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%i"
)

if "%PYTHON_EXE%"=="" (
  echo Python 3.12 is required but was not found via the py launcher.
  echo Install Python 3.12, then run setup_env.bat again.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating .venv with Python %PYTHON_VERSION%...
  "%PYTHON_EXE%" -m venv .venv
  if errorlevel 1 exit /b 1
)

set "VENV_PY=.venv\Scripts\python.exe"

set "VENV_VER="
"%VENV_PY%" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" > .venv_version.tmp
if exist .venv_version.tmp (
  set /p VENV_VER=<.venv_version.tmp
  del /q .venv_version.tmp >nul 2>nul
)
if not "%VENV_VER%"=="3.12" (
  echo Existing .venv uses Python %VENV_VER%, recreating with Python 3.12...
  rmdir /s /q .venv
  "%PYTHON_EXE%" -m venv .venv
  if errorlevel 1 exit /b 1
  set "VENV_PY=.venv\Scripts\python.exe"
)

echo Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo Installing runtime dependencies...
if exist "requirements-lock.txt" (
  "%VENV_PY%" -m pip install -r requirements-lock.txt
) else (
  "%VENV_PY%" -m pip install -r requirements.txt
)
if errorlevel 1 exit /b 1

if exist "requirements-dev.txt" (
  echo Installing dev dependencies...
  "%VENV_PY%" -m pip install -r requirements-dev.txt
  if errorlevel 1 exit /b 1
)

echo Environment setup complete.
echo Quick start: run.bat
exit /b 0
