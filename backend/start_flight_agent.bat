@echo off
echo ╔══════════════════════════════════════════════════╗
echo ║   ReelTrip — Flight Agent Server (Port 8001)    ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: Check if venv exists; if so use it
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

:: Install selenium if missing
python -c "import selenium" 2>nul
if errorlevel 1 (
    echo [INFO] Installing Selenium + webdriver-manager...
    pip install selenium webdriver-manager fastapi uvicorn
)

echo [INFO] Starting Flight Agent Server on http://localhost:8001
echo [INFO] Debug screenshots will be saved to: backend\debug_screenshots\
echo.
python flight_agent_server.py
