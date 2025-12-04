@echo off
echo ========================================
echo Building MinTool.exe
echo ========================================
echo.

cd /d "%~dp0"

echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist MinTool.spec del /q MinTool.spec

echo.
echo Building executable...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name MinTool ^
    --icon=icon.ico ^
    MinTool_modular.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build SUCCESSFUL!
    echo Output: dist\MinTool.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
)

echo.
pause
