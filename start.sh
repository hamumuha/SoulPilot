#!/bin/bash
cd "$(dirname "$0")"
echo "========================================"
echo "  Hamu Pet - Web Edition"
echo "========================================"

echo "[1] Starting FastAPI backend (port 8000)..."
(cd backend && .venv/bin/python main.py) &
BACKEND_PID=$!
sleep 2

echo "[2] Starting Vue frontend (port 5173)..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
