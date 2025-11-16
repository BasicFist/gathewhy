@echo off
REM Hello Kitty BubbleTea TUI - Windows Run Script
REM ===============================================
REM Windows batch script to run the kawaii bubble tea management system

setlocal EnableDelayedExpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Colors for kawaii output (limited in cmd.exe)
echo.
echo 🌸 Hello Kitty BubbleTea TUI 🌸
echo ========================================
echo Kawaii Bubble Tea Shop Management System
echo ========================================
echo.

REM Check if virtual environment exists
set VENV_DIR=venv
set PYTHON_EXEC=

if exist "%VENV_DIR%" (
    set PYTHON_EXEC=%VENV_DIR%\Scripts\python.exe
    set PIP_EXEC=%VENV_DIR%\Scripts\pip.exe
) else (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv "%VENV_DIR%"
    set PYTHON_EXEC=%VENV_DIR%\Scripts\python.exe
    set PIP_EXEC=%VENV_DIR%\Scripts\pip.exe
    echo ✅ Virtual environment created!
)

REM Check if we're in a virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo 🔧 Activating virtual environment...
    call "%VENV_DIR%\Scripts\activate.bat"
)

REM Install/upgrade dependencies if needed
echo 📦 Checking dependencies...

if not exist "requirements.txt" (
    echo ❌ requirements.txt not found!
    pause
    exit /b 1
)

REM Check if dependencies are installed
"%PYTHON_EXEC%" -c "import textual, yaml" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    "%PIP_EXEC%" install -r requirements.txt
    echo ✅ Dependencies installed!
) else (
    echo ✅ Dependencies up to date!
)

REM Set Python path
set PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%

REM Default arguments
set DEFAULT_ARGS=

REM Check for command line arguments
set ARGS=%DEFAULT_ARGS%
if not "%~1"=="" (
    set ARGS=%*
)

REM Run the application
echo 🍵 Starting Hello Kitty BubbleTea TUI...
echo.

REM Change to the source directory for the run
cd src

REM Run the main module
"%PYTHON_EXEC%" -m hello_kitty_dashboard.main %ARGS%

echo.
echo 👋 Sayonara! Thanks for using Hello Kitty BubbleTea TUI! 🌸
pause