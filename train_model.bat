@echo off
REM ============================================================
REM  AI Urban Farming Assistant - one-shot model training
REM  Usage:
REM    train_model.bat --data "D:\datasets\plantvillage\color"
REM    train_model.bat --data "D:\my_photos" --any-classes
REM    train_model.bat --data "D:\datasets\plantvillage\color" --realworld-test "D:\my_photos"
REM    train_model.bat --predict-only "D:\my_photos\leaf.jpg"
REM ============================================================
setlocal
cd /d "%~dp0backend"

set "PYGEN=python"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python is not on PATH. Install Python 3.10+ and retry.
    pause
    exit /b 1
  )
  set "PYGEN=py"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment in backend\.venv ...
  %PYGEN% -m venv .venv
  if errorlevel 1 ( echo ERROR: failed to create venv & pause & exit /b 1 )
)

set "PY=.venv\Scripts\python.exe"

echo Installing/updating dependencies (first run can take a while - torch is large) ...
"%PY%" -m pip install --upgrade pip >nul
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 ( echo ERROR installing requirements.txt & pause & exit /b 1 )
"%PY%" -m pip install -r requirements-ml.txt
if errorlevel 1 ( echo ERROR installing requirements-ml.txt & pause & exit /b 1 )

echo.
echo Running pipeline ...
"%PY%" train_pipeline.py %*
if errorlevel 1 (
  echo.
  echo FAILED - read the errors above.
  pause
  exit /b 1
)

echo.
echo Success.
pause
exit /b 0
