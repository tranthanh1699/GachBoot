@echo off
echo ========================================
echo Building GachBoot ConfigTool.exe
echo ========================================
echo.

cd /d "%~dp0"

echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist GachBootConfigTool.spec del /q GachBootConfigTool.spec

echo.
echo Building executable...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name GachBootConfigTool ^
    --icon=icon.ico ^
    config_editor.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build SUCCESSFUL!
    echo Output: dist\GachBootConfigTool.exe
    echo ========================================
    echo.
    echo Testing executable...
    cd dist
    start GachBootConfigTool.exe
) else (
    echo.
    echo ========================================
    echo Build FAILED!
    echo Check Python and PyInstaller installation:
    echo   pip install pyinstaller
    echo ========================================
)

echo.
pause
