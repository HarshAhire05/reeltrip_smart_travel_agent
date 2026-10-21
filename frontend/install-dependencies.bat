@echo off
echo ========================================
echo Installing Missing Dependencies
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Installing sonner (toast notifications)...
call npm install sonner
if %errorlevel% neq 0 (
    echo ERROR: Failed to install sonner
    pause
    exit /b 1
)
echo ✓ sonner installed
echo.

echo [2/2] Installing @radix-ui/react-alert-dialog...
call npm install @radix-ui/react-alert-dialog
if %errorlevel% neq 0 (
    echo ERROR: Failed to install @radix-ui/react-alert-dialog
    pause
    exit /b 1
)
echo ✓ @radix-ui/react-alert-dialog installed
echo.

echo ========================================
echo ✓ All dependencies installed!
echo ========================================
echo.
echo You can now run: npm run dev
echo.
pause
