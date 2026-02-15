@echo off
echo ==========================================
echo Viral TikTok Bot - Windows Quick Start
echo ==========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)
echo Python found!
echo.

REM Install Python packages
echo Installing Python packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)
echo Python packages installed!
echo.

REM Install Playwright
echo Installing Playwright browsers...
playwright install chromium
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Playwright
    pause
    exit /b 1
)
echo Playwright installed!
echo.

REM Check FFmpeg
echo Checking FFmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: FFmpeg not found!
    echo.
    echo Please install FFmpeg manually:
    echo 1. Download from: https://ffmpeg.org/download.html
    echo 2. Extract to C:\ffmpeg
    echo 3. Add C:\ffmpeg\bin to PATH
    echo.
    echo Press any key to continue anyway...
    pause >nul
) else (
    echo FFmpeg found!
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo To start the bot, run:
echo   python viral_bot.py
echo.
echo Next steps:
echo   1. Add your TikTok accounts
echo   2. Test login for each account
echo   3. Find viral videos
echo   4. Start processing!
echo.
pause
