@echo off
title Voltix TechStore Backend
cd /d "%~dp0"

echo ===================================================
echo   Voltix TechStore FastAPI Backend
echo ===================================================

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [INFO] Backend is ALREADY RUNNING on http://127.0.0.1:8000
    echo You can open Swagger UI: http://127.0.0.1:8000/docs
    echo.
    pause
    exit /b 0
)

echo Starting server on http://127.0.0.1:8000...
.\.venv\Scripts\python.exe main.py

pause
