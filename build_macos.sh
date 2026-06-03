#!/usr/bin/env bash
set -e

python3 -m PyInstaller --onefile --windowed --name 图片文件名检查工具 image_name_checker.py

echo
echo "Build finished. Output is in the dist folder."
