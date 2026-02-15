@echo off
echo ============================================
echo   XAUBOT Pro - Trading Engine Deployment
echo ============================================
echo.

REM Step 1: Create directories
echo [1/6] Creating directories...
mkdir C:\xaubot_engine 2>nul
echo   Done!

REM Step 2: Copy files
echo [2/6] Copying engine files...
copy /Y "%~dp0engine.py" C:\xaubot_engine\
copy /Y "%~dp0worker.py" C:\xaubot_engine\
copy /Y "%~dp0api_server.py" C:\xaubot_engine\
copy /Y "%~dp0requirements.txt" C:\xaubot_engine\
copy /Y "%~dp0..\web\encryption.py" C:\xaubot_engine\
copy /Y "%~dp0..\web\models.py" C:\xaubot_engine\
echo   Done!

REM Step 3: Check Python
echo [3/6] Checking Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo   ERROR: Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

REM Step 4: Install dependencies
echo [4/6] Installing Python dependencies...
pip install MetaTrader5 flask flask-cors cryptography requests pandas --quiet
echo   Done!

REM Step 5: Set up MT5 terminals
echo [5/6] Setting up MT5 worker terminals...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    for /L %%i in (1,1,8) do (
        if not exist "C:\MT5_Worker_%%i" (
            echo   Copying MT5 to C:\MT5_Worker_%%i...
            xcopy "C:\Program Files\MetaTrader 5" "C:\MT5_Worker_%%i" /E /I /Q
        ) else (
            echo   C:\MT5_Worker_%%i already exists
        )
    )
) else (
    echo   WARNING: MetaTrader 5 not found at default path.
    echo   You may need to install MT5 first or copy terminals manually.
)

REM Step 6: Create startup script
echo [6/6] Creating startup scripts...
(
echo @echo off
echo cd /d C:\xaubot_engine
echo start "XAUBOT API" python api_server.py
echo echo API Server started on port 5001
) > C:\xaubot_engine\start_api.bat

(
echo @echo off
echo cd /d C:\xaubot_engine
echo python engine.py
echo pause
) > C:\xaubot_engine\run_trades.bat

echo.
echo ============================================
echo   DEPLOYMENT COMPLETE!
echo ============================================
echo.
echo Files deployed to: C:\xaubot_engine\
echo.
echo To start:
echo   1. Run C:\xaubot_engine\start_api.bat (starts API server)
echo   2. Run C:\xaubot_engine\run_trades.bat (generates signal + executes trades)
echo.
echo Or schedule run_trades.bat as a Windows Task at 4:05 AM GMT daily.
echo.
pause
