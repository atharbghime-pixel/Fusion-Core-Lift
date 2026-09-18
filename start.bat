@echo off
setlocal
title Fusion Core Lift

REM One-click Windows launcher: no manual database setup is ever required.
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Python 3 was not found. Install it from https://www.python.org/downloads/
        echo During installation, select "Add Python to PATH", then run this file again.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

if not exist "venv\Scripts\python.exe" (
    echo Creating a local Python environment...
    %PYTHON_CMD% -m venv venv
    if %ERRORLEVEL% NEQ 0 goto :error
)

echo Installing required packages...
venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 goto :error

echo Starting Fusion Core Lift at http://127.0.0.1:5000
start "" http://127.0.0.1:5000
venv\Scripts\python.exe app.py
exit /b 0

:error
echo.
echo Setup could not be completed. Check your internet connection and Python installation.
pause
exit /b 1
