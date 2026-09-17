@echo off
title AI Content Repurposing Studio
cd /d "%~dp0"

echo ===================================================
echo     Starting AI Content Repurposing Studio...
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ or add it to PATH.
    pause
    exit /b 1
)

echo Launching Studio backend and desktop interface...
python run_studio.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Studio exited with an error.
    pause
)
