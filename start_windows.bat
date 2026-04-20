@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python launcher not found. Install Python 3.10 or newer first.
  pause
  exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo [ERROR] Python 3.10 or newer is required.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 goto :failed
)

echo [2/3] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo [3/3] Starting MaskSource at http://127.0.0.1:8080
start "" /b cmd /c "timeout /t 2 /nobreak ^>nul ^& start http://127.0.0.1:8080"
".venv\Scripts\python.exe" -m src.client.app
exit /b 0

:failed
echo [ERROR] Startup failed. Review the message above.
pause
exit /b 1
