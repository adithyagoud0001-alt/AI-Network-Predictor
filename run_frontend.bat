@echo off
echo ===================================================
echo Starting AI-Based Network Connection Predictor Frontend
echo ===================================================

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
)

echo Starting Next.js development dashboard on http://localhost:3000...
npm run dev
pause
