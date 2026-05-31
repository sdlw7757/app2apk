@echo off
chcp 65001 >nul 2>nul
title APP2APK Builder Server
echo.
echo   ***  APP2APK Build Server  ***
echo.
echo   Starting server...
echo   Browser will open automatically.
echo   Press Ctrl+C to stop.
echo.

python "%~dp0server.py"

if %ERRORLEVEL% neq 0 (
    echo.
echo   [ERROR] Failed to start server.
echo   Please make sure Python 3.8+ is installed and in PATH.
    echo.
    pause
)