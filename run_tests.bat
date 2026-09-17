@echo off
title AI Content Repurposing Studio - Run Tests
cd /d "%~dp0"

echo ===================================================
echo     Running Automated Test Suite (pytest)...
echo ===================================================
echo.

python -m pytest -v

echo.
pause
