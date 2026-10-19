@echo off
echo ========================================
echo   Hamu Pet - Web Edition
echo ========================================
echo.
echo [0] Checking required ports...
powershell -NoProfile -Command "$ports = @(8000, 5173); $busy = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort } | Select-Object -ExpandProperty LocalPort -Unique; if ($busy) { Write-Error ('Ports already in use: ' + ($busy -join ', ')); exit 1 }"
if errorlevel 1 (
    echo.
    echo Please close the existing service using port 8000 or 5173, then run start.bat again.
    pause
    exit /b 1
)
echo [1] Starting FastAPI backend (port 8000)...
start "Hamu Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe main.py"
timeout /t 3 /nobreak >nul
echo [2] Starting Vue frontend (port 5173)...
start "Hamu Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
echo.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo API Docs: http://127.0.0.1:8000/docs
echo.
pause
