@echo off
title AI Content Studio - Chrome Login Setup
cd /d "%~dp0"

echo ================================================================
echo           AI Content Studio - One-Time Browser Login Setup
echo ================================================================
echo.
echo Launching Google Chrome with persistent session and remote debugging...
echo.
echo INSTRUCTIONS:
echo 1. Chrome will open Gemini, DeepSeek, and YouTube.
echo 2. Please log in to your accounts (Gemini, DeepSeek, YouTube Studio).
echo 3. Once logged in, your session is permanently saved in:
echo    "%~dp0storage\chrome_profile"
echo 4. You can keep Chrome open, or close it whenever you want.
echo    The Studio will connect to this session automatically!
echo.
echo ================================================================

set "PROFILE_DIR=%USERPROFILE%\OneDrive\ドキュメント\ai\omnidev\chrome_profile"
if not exist "%PROFILE_DIR%" (
    set "PROFILE_DIR=%~dp0storage\chrome_profile"
)

echo Using persistent Chrome profile at:
echo "%PROFILE_DIR%"
echo.

set "CHROME_PATH="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
) else (
    set "CHROME_PATH=chrome.exe"
)

start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%PROFILE_DIR%" "https://gemini.google.com" "https://chat.deepseek.com" "https://studio.youtube.com"

echo.
echo Chrome has been started. Please log into your accounts in the browser.
echo Press any key to exit this window...
pause >nul
