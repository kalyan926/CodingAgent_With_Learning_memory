@echo off
echo Starting Deep Agent with Learning Memory...
echo.

:: Start the backend server in a new window
echo Starting Backend Server...
start "Backend Server" cmd /k "python server.py"

:: Wait a moment for the server to initialize
timeout /t 2 /nobreak >nul

:: Start the frontend dev server in a new window
echo Starting Frontend UI...
start "Frontend UI" cmd /k "cd ui && npm run dev"

echo.
echo Both servers are starting in separate windows.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
