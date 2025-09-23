@echo off
echo ========================================
echo  Fantrax Value Hunter - Safe Dashboard Launcher
echo ========================================
echo.
echo This launcher prevents file lock issues during development.
echo Backend runs with auto-reload disabled for stable file editing.
echo.

REM Check if ports are already in use
echo Checking if services are already running...
curl -s http://localhost:5001 >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Backend already running on port 5001
    echo Press any key to continue anyway or Ctrl+C to exit...
    pause >nul
)

curl -s http://localhost:3000 >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Frontend already running on port 3000
    echo Press any key to continue anyway or Ctrl+C to exit...
    pause >nul
)

echo.
echo Starting Flask backend on port 5001 (NO auto-reload)...

REM Set environment for stable file editing
set FLASK_ENV=development
set FLASK_NO_RELOAD=true

start "Flask Backend - Safe Mode" cmd /k "python src/app.py"

echo Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

echo.
echo Starting React frontend on port 3000...
cd frontend
start "React Frontend" cmd /k "npm start"

echo.
echo Waiting for frontend to build...
timeout /t 10 /nobreak >nul

echo.
echo Opening dashboard in browser...
start http://localhost:3000

echo.
echo ========================================
echo  Dashboard Ready! (Safe Mode)
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:5001
echo  Mode: Development with NO auto-reload
echo ========================================
echo.
echo Safe Mode Benefits:
echo - Prevents file lock issues during editing
echo - Stable for Claude Code sessions
echo - Manual restart required after code changes
echo.
echo To restart backend only: Use start_dev_no_reload_corrected.bat
echo For emergency recovery: Use emergency_recovery.bat
echo.
echo Press any key to close this launcher...
pause >nul