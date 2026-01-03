@echo off
echo ========================================
echo   ACE Elite Leaderboard - Quick Start
echo ========================================
echo.

echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [2/3] Initializing database...
python init_db.py

echo.
echo [3/3] Starting Flask application...
echo.
echo ========================================
echo   Server running at: http://localhost:5000
echo   Press Ctrl+C to stop
echo ========================================
echo.
echo Default Admin Login:
echo   Username: admin
echo   Password: admin123
echo.

python app.py
