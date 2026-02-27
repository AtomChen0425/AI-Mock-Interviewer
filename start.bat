@echo off
title AI Mock Interviewer - Start Script
chcp 65001 >nul

echo ==========================================
echo    AI 模拟面试系统 - Windows 一键启动
echo ==========================================
echo.

echo 🚀 [1/3] 初始化启动程序...

:: ==========================================
:: 启动后端 (FastAPI)
:: ==========================================
echo 📦 [2/3] 正在启动 FastAPI 后端...
if exist "backend\" (
    cd backend
    
    
    :: 打开一个新窗口运行后端，/k 表示运行完保留窗口以便看日志
    start  cmd /k "title FastAPI Backend && activate NewFlask && uvicorn main:app --reload --port 8000"
    cd ..
) else (
    echo ❌ 错误: 找不到 'backend' 文件夹！
    pause
    exit /b
)

:: ==========================================
:: 启动前端 (Vue/Vite)
:: ==========================================
echo 💻 [3/3] 正在启动 Vue 前端...
if exist "frontend\" (
    cd frontend
    
    :: 打开一个新窗口运行前端
    start cmd /k "title Vue Frontend && npm run dev"
    cd ..
) else (
    echo ❌ 错误: 找不到前端文件夹！
    pause
    exit /b
)

:: ==========================================
:: 启动完成指示
:: ==========================================
echo.
echo ✨ 系统启动请求已发送！
echo 👉 前端地址: http://localhost:5173
echo 👉 后端地址: http://localhost:8000
echo ==========================================
echo.
pause