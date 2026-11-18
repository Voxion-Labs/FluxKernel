@echo off
setlocal enabledelayedexpansion

title FluxKernel Sovereign Autonomous Operating System

echo ==============================================================================
echo  Voxion Labs - FluxKernel Autonomous Operating System
echo  Tri-Stack Sovereign Architecture (Go + C++20 + Python)
echo ==============================================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10+ is required but not found in PATH.
    echo Please install Python from https://python.org and add it to PATH.
    pause
    exit /b 1
)

:: 2. Check Go
where go >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Go 1.22+ is required but not found in PATH.
    echo Please install Go from https://golang.org and add it to PATH.
    pause
    exit /b 1
)

:: 3. Optional C++ Native Acceleration Check
where g++ >nul 2>&1
if %errorlevel% equ 0 (
    if not exist "native\build\flux_core.dll" (
        echo [INFO] C++ compiler detected (g++). Compiling native accelerator shared library...
        if not exist "native\build" mkdir native\build
        g++ -O3 -fPIC -shared -std=c++20 native\src\flux_core.cpp -I native\include -o native\build\flux_core.dll 2>nul
        if exist "native\build\flux_core.dll" (
            echo [OK] Native C++ accelerator compiled successfully (native\build\flux_core.dll).
        ) else (
            echo [INFO] Pre-compilation skipped; Python transparent C ABI fallback will be used.
        )
    ) else (
        echo [OK] Native C++ accelerator found (native\build\flux_core.dll).
    )
) else (
    echo [INFO] C++ compiler not detected; Python transparent native fallback will be used.
)

echo.
echo [1/3] Starting FluxKernel Python Cognitive Brain on port 8000...
start /b "" python -m uvicorn app.main:app --app-dir engine --host 127.0.0.1 --port 8000 --log-level warning >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Starting FluxKernel Go Gateway & Sovereign Console on port 8080...
cd gateway
start /b "" go run ./cmd/server >nul 2>&1
cd ..
timeout /t 2 /nobreak >nul

echo [3/3] Opening Sovereign Web Console in your default browser...
start http://localhost:8080/dashboard

echo.
echo ==============================================================================
echo  FluxKernel is LIVE and operational!
echo  Web Console: http://localhost:8080/dashboard
echo  API Gateway: http://localhost:8080
echo  Brain Engine: http://localhost:8000
echo.
echo  Press Ctrl+C or close this window to terminate all FluxKernel services.
echo ==============================================================================
echo.

:: Wait loop to keep window open and trap shutdown
:loop
timeout /t 5 /nobreak >nul
goto loop
