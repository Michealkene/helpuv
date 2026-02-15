@echo off
REM XAUBOT Pro - Emergency Quick Start Script
REM This uses full paths to avoid PATH issues

echo ========================================
echo XAUBOT PRO - QUICK START
echo ========================================
echo.

set PYTHON="C:\Program Files\Python312\python.exe"
set STREAMLIT="C:\Program Files\Python312\Scripts\streamlit.exe"
set PROJECT_DIR=%~dp0

cd /d "%PROJECT_DIR%"

echo [1/4] Checking Python...
%PYTHON% --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found at C:\Program Files\Python312\python.exe
    pause
    exit /b 1
)

echo.
echo [2/4] Checking dependencies...
%PYTHON% -c "import streamlit, flask, MetaTrader5, pandas" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies missing. Installing...
    %PYTHON% -m pip install -r requirements.txt -q
    %PYTHON% -m pip install -r saas\web\requirements.txt -q
)

echo.
echo [3/4] Starting components...
echo.
echo Choose startup mode:
echo   1 - Dashboard Only (Streamlit)
echo   2 - Backend API Only (Flask)
echo   3 - Live Trading Bot
echo   4 - Full System (All Components)
echo   5 - Dry Run Test
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto dashboard
if "%choice%"=="2" goto backend
if "%choice%"=="3" goto livebot
if "%choice%"=="4" goto fullsystem
if "%choice%"=="5" goto dryrun

echo Invalid choice. Exiting.
pause
exit /b 1

:dashboard
echo.
echo Starting Streamlit Dashboard on http://localhost:8501
echo Press Ctrl+C to stop
%STREAMLIT% run app.py --server.port 8501
goto end

:backend
echo.
echo Starting Flask Backend on http://localhost:5000
echo Press Ctrl+C to stop
cd backend
%PYTHON% app.py
goto end

:livebot
echo.
echo Starting Live Trading Bot (LIVE MODE - REAL TRADES)
echo Press Ctrl+C to stop
%PYTHON% live_bot.py
goto end

:fullsystem
echo.
echo Starting all components...
echo.
echo Opening 3 terminal windows:
echo   - Window 1: Streamlit Dashboard (port 8501)
echo   - Window 2: Flask Backend (port 5000)  
echo   - Window 3: Live Trading Bot
echo.
start "XauBot Dashboard" cmd /k "%STREAMLIT% run "%PROJECT_DIR%app.py" --server.port 8501"
timeout /t 3 >nul
start "XauBot Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && %PYTHON% app.py"
timeout /t 3 >nul
start "XauBot Live Bot" cmd /k "cd /d "%PROJECT_DIR%" && %PYTHON% live_bot.py"
echo.
echo All components started in separate windows.
echo Close this window or press any key to exit.
pause >nul
goto end

:dryrun
echo.
echo Starting Live Bot in DRY RUN mode (no real trades)
echo Press Ctrl+C to stop
%PYTHON% live_bot.py --dry-run
goto end

:end
echo.
echo Shutdown complete.
pause
