@echo off
REM Build script for SecurityUnlock.exe

echo ========================================
echo Building SecurityUnlock.exe
echo ========================================

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Building executable...
pyinstaller --onefile --name SecurityUnlock --console SecurityUnlock.py

if errorlevel 1 (
    echo.
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\SecurityUnlock.exe
echo.

REM Test the executable
echo Testing executable...
dist\SecurityUnlock.exe 01020304
if errorlevel 1 (
    echo WARNING: Test failed!
) else (
    echo Test passed!
)

echo.
pause
