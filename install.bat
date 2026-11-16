@echo off
setlocal EnableExtensions

cd /d "%~dp0"

:: Self-elevate to administrator if needed
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

echo ==========================================
echo   Folder Encryption - One-click Install
echo ==========================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found. Please install Python 3.10+ and add it to PATH.
    goto :end
)

echo [1/2] Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    goto :end
)

echo.
echo [2/2] Installing Explorer context menu...
python scripts\install_context_menu.py install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install context menu.
    goto :end
)

echo.
echo [OK] Installation completed.
echo If using Windows 11, right-click a folder and choose "Show more options" to see Encrypt/Decrypt.

:end
echo.
pause
endlocal
