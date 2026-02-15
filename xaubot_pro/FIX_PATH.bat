@echo off
REM XAUBOT Pro - Fix Python PATH
REM Run as Administrator

echo ========================================
echo XAUBOT PRO - PATH FIX UTILITY
echo ========================================
echo.
echo This script adds Python to system PATH
echo REQUIRES: Administrator privileges
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Checking current PATH...
echo %PATH% | findstr /i "Python312" >nul
if %errorlevel% equ 0 (
    echo Python312 already in PATH
) else (
    echo Adding Python to PATH...
    setx /M PATH "%PATH%;C:\Program Files\Python312;C:\Program Files\Python312\Scripts"
    echo SUCCESS: Python added to PATH
)

echo.
echo Verification:
where python 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Python not found in PATH
    echo You may need to restart your terminal or computer
) else (
    echo Python found in PATH!
)

echo.
echo ========================================
echo NEXT STEPS:
echo 1. Close and reopen all terminal windows
echo 2. Run QUICK_START.bat to start XauBot Pro
echo 3. If issues persist, restart computer
echo ========================================
echo.
pause
