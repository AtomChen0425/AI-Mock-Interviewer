# ==========================================
# AI Mock Interviewer - One-click startup script
# ==========================================

echo "🚀 [1/3] Initializing startup process..."

trap 'echo -e "\n🛑 Closing all services..."; kill $FRONTEND_PID $BACKEND_PID 2>/dev/null; wait $FRONTEND_PID $BACKEND_PID 2>/dev/null; echo "✅ All services have been completely shut down!"; exit 0' SIGINT SIGTERM

# ==========================================
# Start Backend (FastAPI)
# ==========================================
echo "📦 [2/3] Starting FastAPI backend..."
if [ -d "backend" ]; then
    cd backend
    
    uvicorn main:app --reload --port 8000 &
    BACKEND_PID=$!
    
    cd ..
else
    echo "❌ Error: cannot find backend folder! Please check the path."
    exit 1
fi

# ==========================================
# Start Frontend (Vue/Vite)
# ==========================================
echo "💻 [3/3] Starting Vue frontend..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    
    npm run dev &
    FRONTEND_PID=$!
    
    cd ..
else
    echo "❌ Error: cannot find frontend folder! Please check the path."
    kill $BACKEND_PID
    exit 1
fi

# ==========================================
# Finish startup
# ==========================================
echo ""
echo "✨ System startup completed successfully!"
echo "👉 Frontend URL: http://localhost:3000"
echo "👉 Backend URL: http://localhost:8000"
echo "=========================================="

wait