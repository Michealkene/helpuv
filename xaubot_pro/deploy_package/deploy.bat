@echo off
title XAUBOT Pro - VPS Deployment
color 0E
cls

echo.
echo  ========================================================
echo  =                                                      =
echo  =        XAUBOT Pro - VPS DEPLOYMENT SCRIPT            =
echo  =                                                      =
echo  ========================================================
echo.
echo  This will set up XAUBOT Pro on this VPS server.
echo  Press any key to begin...
pause >nul

set "DEPLOY_DIR=C:\XAUBOT_Pro"
set "SCRIPT_DIR=%~dp0"

:: ---- Create directories ----
echo.
echo  [1/8] Creating directories...
if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"
if not exist "%DEPLOY_DIR%\.streamlit" mkdir "%DEPLOY_DIR%\.streamlit"
if not exist "%DEPLOY_DIR%\landing" mkdir "%DEPLOY_DIR%\landing"
echo  [OK] Directories ready

:: ---- Copy files ----
echo.
echo  [2/8] Copying XAUBOT Pro files...
copy /Y "%SCRIPT_DIR%app.py" "%DEPLOY_DIR%\app.py" >nul
copy /Y "%SCRIPT_DIR%live_bot.py" "%DEPLOY_DIR%\live_bot.py" >nul
copy /Y "%SCRIPT_DIR%trade.py" "%DEPLOY_DIR%\trade.py" >nul
copy /Y "%SCRIPT_DIR%config.json" "%DEPLOY_DIR%\config.json" >nul
copy /Y "%SCRIPT_DIR%requirements.txt" "%DEPLOY_DIR%\requirements.txt" >nul
copy /Y "%SCRIPT_DIR%config.toml" "%DEPLOY_DIR%\.streamlit\config.toml" >nul
copy /Y "%SCRIPT_DIR%index.html" "%DEPLOY_DIR%\landing\index.html" >nul
copy /Y "%SCRIPT_DIR%server.py" "%DEPLOY_DIR%\landing\server.py" >nul
echo  [OK] Files copied

:: ---- Check Python ----
echo.
echo  [3/8] Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Python not found. Downloading Python 3.11...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    if exist "%TEMP%\python_installer.exe" (
        echo  [*] Installing Python 3.11...
        "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
        set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
        timeout /t 5 /nobreak >nul
    ) else (
        echo  [ERROR] Failed to download Python.
        echo  [ERROR] Please install Python 3.11 from https://www.python.org/downloads/
        echo  [ERROR] Make sure to check "Add Python to PATH"
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  [OK] %%i

:: ---- Create venv ----
echo.
echo  [4/8] Setting up virtual environment...
if not exist "%DEPLOY_DIR%\.venv\Scripts\python.exe" (
    python -m venv "%DEPLOY_DIR%\.venv"
    echo  [OK] Virtual environment created
) else (
    echo  [OK] Virtual environment exists
)

:: ---- Install dependencies ----
echo.
echo  [5/8] Installing dependencies (this takes a few minutes)...
"%DEPLOY_DIR%\.venv\Scripts\pip.exe" install --upgrade pip -q 2>nul
"%DEPLOY_DIR%\.venv\Scripts\pip.exe" install streamlit plotly pandas numpy -q
echo  [OK] Dependencies installed

:: ---- Create startup scripts ----
echo.
echo  [6/8] Creating startup scripts...

:: Landing page (port 80)
(
echo @echo off
echo cd /d "%DEPLOY_DIR%\landing"
echo "%DEPLOY_DIR%\.venv\Scripts\python.exe" server.py 80
) > "%DEPLOY_DIR%\start_landing.bat"

:: Dashboard (port 8501)
(
echo @echo off
echo cd /d "%DEPLOY_DIR%"
echo "%DEPLOY_DIR%\.venv\Scripts\streamlit.exe" run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
) > "%DEPLOY_DIR%\start_dashboard.bat"

:: Master start
(
echo @echo off
echo echo Starting XAUBOT Pro services...
echo start "XAUBOT Landing" /min cmd /c "%DEPLOY_DIR%\start_landing.bat"
echo timeout /t 3 /nobreak ^>nul
echo start "XAUBOT Dashboard" /min cmd /c "%DEPLOY_DIR%\start_dashboard.bat"
echo echo.
echo echo XAUBOT Pro is running:
echo echo   Landing page: http://3.231.147.217
echo echo   Dashboard:    http://3.231.147.217:8501
echo echo.
) > "%DEPLOY_DIR%\start_all.bat"

:: Stop all
(
echo @echo off
echo echo Stopping XAUBOT Pro services...
echo taskkill /f /fi "WINDOWTITLE eq XAUBOT Landing*" 2^>nul
echo taskkill /f /fi "WINDOWTITLE eq XAUBOT Dashboard*" 2^>nul
echo for /f "tokens=2" %%%%a in ('tasklist /fi "imagename eq streamlit.exe" /nh 2^^^>nul') do taskkill /f /pid %%%%a 2^>nul
echo echo [OK] All services stopped.
echo pause
) > "%DEPLOY_DIR%\stop_all.bat"

echo  [OK] Startup scripts created

:: ---- Open firewall ----
echo.
echo  [7/8] Configuring firewall...
netsh advfirewall firewall add rule name="XAUBOT HTTP 80" dir=in action=allow protocol=tcp localport=80 >nul 2>&1
netsh advfirewall firewall add rule name="XAUBOT Dashboard 8501" dir=in action=allow protocol=tcp localport=8501 >nul 2>&1
echo  [OK] Firewall rules added (ports 80, 8501)

:: ---- Auto-start on boot ----
echo.
echo  [8/8] Setting up auto-start on boot...
schtasks /create /tn "XAUBOT_Pro_Autostart" /tr "%DEPLOY_DIR%\start_all.bat" /sc onstart /ru SYSTEM /rl highest /f >nul 2>&1
echo  [OK] Auto-start task created

:: ---- Start services now ----
echo.
echo  Starting services now...
start "XAUBOT Landing" /min cmd /c "%DEPLOY_DIR%\start_landing.bat"
timeout /t 3 /nobreak >nul
start "XAUBOT Dashboard" /min cmd /c "%DEPLOY_DIR%\start_dashboard.bat"
timeout /t 5 /nobreak >nul

echo.
echo  ========================================================
echo  =                                                      =
echo  =        DEPLOYMENT COMPLETE!                          =
echo  =                                                      =
echo  ========================================================
echo.
echo  Landing Page: http://3.231.147.217
echo  Dashboard:    http://3.231.147.217:8501
echo.
echo  Files installed to: %DEPLOY_DIR%
echo.
echo  Useful scripts in %DEPLOY_DIR%:
echo    start_all.bat    - Start all services
echo    stop_all.bat     - Stop all services
echo    start_landing.bat - Start landing page only
echo    start_dashboard.bat - Start dashboard only
echo.
echo  Services will auto-start on reboot.
echo.
pause
