@echo off
echo ===================================================
echo Starting AI-Based Network Connection Predictor Backend
echo ===================================================

cd /d "%~dp0"
set PYTHONPATH=%~dp0backend

if not exist "venv\Scripts\uvicorn.exe" (
    echo Error: Virtual environment not found at %~dp0venv.
    pause
    exit /b 1
)

echo Activating virtual environment and starting Uvicorn server...
venv\Scripts\uvicorn --app-dir backend app.main:app --host 0.0.0.0 --port 8000 --reload
pause
