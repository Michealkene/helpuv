@echo off
title XAUBOT Pro - Installer
color 0E
cls

echo.
echo  ========================================================
echo  =                                                      =
echo  =              XAUBOT Pro  -  INSTALLER                =
echo  =           Professional Gold Trading Bot              =
echo  =                                                      =
echo  ========================================================
echo.
echo  This installer will set up everything you need:
echo    [1] Python 3.11 (if not installed)
echo    [2] MetaTrader 5 Terminal
echo    [3] All required dependencies
echo    [4] Guided configuration wizard
echo    [5] Desktop shortcuts
echo.
echo  Press any key to begin installation...
pause >nul

:: ---- Check Admin Rights ----
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  [!] This installer needs Administrator rights.
    echo  [!] Right-click install.bat and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: ---- Set install directory ----
set "INSTALL_DIR=%USERPROFILE%\XAUBOT_Pro"
echo.
echo  [*] Install directory: %INSTALL_DIR%

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo  [OK] Created install directory
) else (
    echo  [OK] Install directory exists
)

:: ---- Check Python ----
echo.
echo  [*] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Python not found. Downloading Python 3.11...
    echo.

    :: Download Python installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

    if not exist "%TEMP%\python_installer.exe" (
        echo  [ERROR] Failed to download Python. Please install Python 3.11 manually.
        echo  [ERROR] Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    )

    echo  [*] Installing Python 3.11 (this may take a minute)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

    :: Refresh PATH
    set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"

    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo  [ERROR] Python installation failed. Please install manually.
        pause
        exit /b 1
    )
    echo  [OK] Python installed successfully
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  [OK] Found %%i
)

:: ---- Check MetaTrader 5 ----
echo.
echo  [*] Checking MetaTrader 5...
set "MT5_FOUND=0"
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    set "MT5_FOUND=1"
    set "MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe"
)
if exist "%APPDATA%\MetaQuotes\Terminal\*" (
    set "MT5_FOUND=1"
)

if "%MT5_FOUND%"=="0" (
    echo  [!] MetaTrader 5 not found.
    echo  [*] Downloading MetaTrader 5...
    powershell -Command "Invoke-WebRequest -Uri 'https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe' -OutFile '%TEMP%\mt5setup.exe'"

    if exist "%TEMP%\mt5setup.exe" (
        echo  [*] Launching MetaTrader 5 installer...
        echo  [!] Please complete the MT5 installation, then press any key to continue.
        start "" "%TEMP%\mt5setup.exe"
        pause >nul
    ) else (
        echo  [!] Could not download MT5. Please install it manually from:
        echo  [!] https://www.metatrader5.com/en/download
        echo  [!] Press any key after installing MT5...
        pause >nul
    )
) else (
    echo  [OK] MetaTrader 5 found
)

:: ---- Copy bot files ----
echo.
echo  [*] Copying XAUBOT Pro files...

:: Copy main files
copy /Y "%~dp0\..\live_bot.py" "%INSTALL_DIR%\live_bot.py" >nul 2>&1
copy /Y "%~dp0\..\app.py" "%INSTALL_DIR%\app.py" >nul 2>&1
copy /Y "%~dp0\..\config.json" "%INSTALL_DIR%\config.json" >nul 2>&1
copy /Y "%~dp0\..\requirements.txt" "%INSTALL_DIR%\requirements.txt" >nul 2>&1
copy /Y "%~dp0\..\trade.py" "%INSTALL_DIR%\trade.py" >nul 2>&1

:: Copy .streamlit config
if not exist "%INSTALL_DIR%\.streamlit" mkdir "%INSTALL_DIR%\.streamlit"
copy /Y "%~dp0\..\.streamlit\config.toml" "%INSTALL_DIR%\.streamlit\config.toml" >nul 2>&1

echo  [OK] Files copied

:: ---- Create virtual environment ----
echo.
echo  [*] Creating Python virtual environment...
if not exist "%INSTALL_DIR%\.venv" (
    python -m venv "%INSTALL_DIR%\.venv"
    echo  [OK] Virtual environment created
) else (
    echo  [OK] Virtual environment exists
)

:: ---- Install dependencies ----
echo.
echo  [*] Installing Python dependencies (this may take a few minutes)...
"%INSTALL_DIR%\.venv\Scripts\pip.exe" install --upgrade pip >nul 2>&1
"%INSTALL_DIR%\.venv\Scripts\pip.exe" install -r "%INSTALL_DIR%\requirements.txt"
if %errorLevel% neq 0 (
    echo  [!] Some packages may have failed. Trying individually...
    "%INSTALL_DIR%\.venv\Scripts\pip.exe" install streamlit plotly pandas numpy MetaTrader5
)
echo  [OK] Dependencies installed

:: ---- Run Setup Wizard ----
echo.
echo  [*] Launching configuration wizard...
echo.
copy /Y "%~dp0\setup_wizard.py" "%INSTALL_DIR%\setup_wizard.py" >nul 2>&1
"%INSTALL_DIR%\.venv\Scripts\python.exe" "%INSTALL_DIR%\setup_wizard.py"

:: ---- Create Desktop Shortcuts ----
echo.
echo  [*] Creating desktop shortcuts...

:: Dashboard shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\XAUBOT Pro Dashboard.lnk'); $s.TargetPath = 'cmd.exe'; $s.Arguments = '/c cd /d \"%INSTALL_DIR%\" && .venv\Scripts\streamlit.exe run app.py'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = 'shell32.dll,21'; $s.Description = 'XAUBOT Pro Trading Dashboard'; $s.Save()"
echo  [OK] Dashboard shortcut created

:: Bot launcher shortcut
(
echo @echo off
echo title XAUBOT Pro - Live Trading
echo color 0E
echo cd /d "%INSTALL_DIR%"
echo echo.
echo echo  ========================================
echo echo  =       XAUBOT Pro - Live Trading      =
echo echo  ========================================
echo echo.
echo echo  Starting live trading bot...
echo echo  Press Ctrl+C to stop.
echo echo.
echo .venv\Scripts\python.exe live_bot.py
echo pause
) > "%INSTALL_DIR%\start_bot.bat"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\XAUBOT Pro Bot.lnk'); $s.TargetPath = '%INSTALL_DIR%\start_bot.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = 'shell32.dll,176'; $s.Description = 'XAUBOT Pro Live Trading Bot'; $s.Save()"
echo  [OK] Bot launcher shortcut created

:: ---- Create uninstaller ----
(
echo @echo off
echo title XAUBOT Pro - Uninstaller
echo color 0C
echo echo.
echo echo  This will remove XAUBOT Pro from your system.
echo echo  Press any key to continue or close this window to cancel.
echo pause ^>nul
echo rmdir /s /q "%INSTALL_DIR%"
echo del "%USERPROFILE%\Desktop\XAUBOT Pro Dashboard.lnk" 2^>nul
echo del "%USERPROFILE%\Desktop\XAUBOT Pro Bot.lnk" 2^>nul
echo echo.
echo echo  [OK] XAUBOT Pro has been uninstalled.
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

:: ---- Done ----
echo.
echo  ========================================================
echo  =                                                      =
echo  =         XAUBOT Pro INSTALLED SUCCESSFULLY!           =
echo  =                                                      =
echo  ========================================================
echo.
echo  Install location: %INSTALL_DIR%
echo.
echo  Desktop shortcuts created:
echo    - XAUBOT Pro Dashboard  (opens the trading dashboard)
echo    - XAUBOT Pro Bot        (starts live trading)
echo.
echo  QUICK START:
echo    1. Open MetaTrader 5 and log into your account
echo    2. Double-click "XAUBOT Pro Dashboard" on your desktop
echo    3. Go to Settings to verify your MT5 credentials
echo    4. Click "Start Bot" in the Live Trading page
echo.
echo  For help, refer to the Quick Start Guide included.
echo.
echo  Press any key to exit...
pause >nul
