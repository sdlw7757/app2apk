@echo off
title APP2APK Build Server
echo.
echo   ***  APP2APK Build Server  ***
echo.
echo   Starting server on port 8090 ...
echo   Open http://localhost:8090 in your browser.
echo   Press Ctrl+C to stop.
echo.

REM Change the port number below if needed (default 8090)
set APP2APK_PORT=8090

python "%~dp0server.py" %APP2APK_PORT%

if %ERRORLEVEL% neq 0 (
    echo.
    echo   [ERROR] Failed to start server.
    echo   Please make sure Python 3.8+ is installed and in PATH.
    echo.
    pause
)
