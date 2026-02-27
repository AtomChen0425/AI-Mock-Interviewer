# ==========================================
# AI 模拟面试系统 - 一键启动脚本
# ==========================================

echo "🚀 [1/3] 初始化启动程序..."

# 捕捉 Ctrl+C (SIGINT) 信号，用于优雅退出
trap 'echo -e "\n🛑 正在关闭服务器..."; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; wait $FRONTEND_PID $BACKEND_PID 2>/dev/null; echo "✅ 已完全退出！"; exit 0' SIGINT SIGTERM

# ==========================================
# 启动后端 (FastAPI)
# ==========================================
echo "📦 [2/3] 正在启动 FastAPI 后端..."
if [ -d "backend" ]; then
    cd backend
    
    # 如果你有使用虚拟环境 (venv)，请取消下面这行的注释
    # source venv/bin/activate
    activate NewFlask
    # 在后台运行 Uvicorn
    uvicorn main:app --reload --port 8000 &
    BACKEND_PID=$!
    
    cd ..
else
    echo "❌ 错误: 找不到 'backend' 文件夹！请检查路径。"
    exit 1
fi

# ==========================================
# 启动前端 (Vue/Vite)
# ==========================================
echo "💻 [3/3] 正在启动 Vue 前端..."
if [ -d "frontend" ]; then
    cd frontend
    
    # 在后台运行 Vite
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
else
    echo "❌ 错误: 找不到前端文件夹！请检查路径。"
    # 如果前端启动失败，顺手把刚才启动的后端关掉
    kill $BACKEND_PID
    exit 1
fi

# ==========================================
# 启动完成指示
# ==========================================
echo ""
echo "✨ 系统启动成功！"
echo "👉 前端地址: http://localhost:5173"
echo "👉 后端地址: http://localhost:8000"
echo "⚠️  按 [Ctrl + C] 可一键停止所有服务"
echo "=========================================="

# 挂起脚本，等待用户的 Ctrl+C
wait