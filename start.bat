@echo off
title AI Mock Interviewer - Start Script
chcp 65001 >nul

echo ==========================================
echo    AI Mock Interviewer - Windows 
echo ==========================================
echo.

echo 🚀 [1/3] Initializing startup process...

:: ==========================================
:: Start backend (FastAPI)
:: ==========================================
echo 📦 [2/3] Starting FastAPI backend...
if exist "backend\" (
    cd backend
    start  cmd /k "title FastAPI Backend && uvicorn main:app --reload --port 8000"
    cd ..
) else (
    echo ❌ Error: cannot find backend folder!
    pause
    exit /b
)

:: ==========================================
:: Start Frontend (Vue/Vite)
:: ==========================================
echo 💻 [3/3] Starting Vue frontend...
if exist "frontend\" (
    cd frontend

    start cmd /k "title Vue Frontend && npm install && npm run dev"
    cd ..
) else (
    echo ❌ Error: cannot find frontend folder!
    pause
    exit /b
)

:: ==========================================
:: All services started
:: ==========================================
echo.
echo 👉 Frontend: http://localhost:3000
echo 👉 Backend: http://localhost:8000
echo ==========================================
echo.
pause
