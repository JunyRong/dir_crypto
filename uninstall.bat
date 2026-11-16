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

echo ============================================
echo   Folder Encryption - One-click Uninstall
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH. Cannot remove context menu automatically.
    goto :end
)

python scripts\install_context_menu.py uninstall
if %errorlevel% neq 0 (
    echo [ERROR] Failed to uninstall context menu.
    goto :end
)

echo.
echo [OK] Uninstall completed.

:end
echo.
pause
endlocal
