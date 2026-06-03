@echo off
setlocal

python -m PyInstaller --onefile --windowed --name 图片文件名检查工具 image_name_checker.py

if errorlevel 1 (
    echo.
    echo Build failed. Please install PyInstaller first:
    echo pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo.
echo Build finished. Output is in the dist folder.
echo EXE: dist\图片文件名检查工具.exe
echo.
pause
