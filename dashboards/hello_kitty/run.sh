#!/bin/bash
# Hello Kitty BubbleTea TUI - Run Script
# ======================================
# Simple script to run the kawaii bubble tea management system

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for kawaii output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PINK='\033[1;35m'
RESET='\033[0m'

# Kawaii banner
echo -e "${PINK}"
echo "🌸 Hello Kitty BubbleTea TUI 🌸"
echo "=" * 50
echo "Kawaii Bubble Tea Shop Management System"
echo "======================================="
echo -e "${RESET}"

# Check if virtual environment exists
VENV_DIR="venv"
PYTHON_EXEC=""

if [ -d "$VENV_DIR" ]; then
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        PYTHON_EXEC="$VENV_DIR/Scripts/python.exe"
        PIP_EXEC="$VENV_DIR/Scripts/pip.exe"
    else
        # Unix-like systems
        PYTHON_EXEC="$VENV_DIR/bin/python"
        PIP_EXEC="$VENV_DIR/bin/pip"
    fi
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${RESET}"
    python3 -m venv "$VENV_DIR"
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        PYTHON_EXEC="$VENV_DIR/Scripts/python.exe"
        PIP_EXEC="$VENV_DIR/Scripts/pip.exe"
    else
        PYTHON_EXEC="$VENV_DIR/bin/python"
        PIP_EXEC="$VENV_DIR/bin/pip"
    fi
    
    echo -e "${GREEN}✅ Virtual environment created!${RESET}"
fi

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}🔧 Activating virtual environment...${RESET}"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        source "$VENV_DIR/Scripts/activate"
    else
        source "$VENV_DIR/bin/activate"
    fi
fi

# Install/upgrade dependencies if needed
echo -e "${BLUE}📦 Checking dependencies...${RESET}"

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found!${RESET}"
    exit 1
fi

# Check if dependencies are installed
if ! "$PYTHON_EXEC" -c "import textual, yaml" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing dependencies...${RESET}"
    "$PIP_EXEC" install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed!${RESET}"
else
    echo -e "${GREEN}✅ Dependencies up to date!${RESET}"
fi

# Set Python path
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Default arguments
DEFAULT_ARGS=""

# Check for command line arguments
if [ $# -eq 0 ]; then
    # No arguments, run the main application
    ARGS="$DEFAULT_ARGS"
else
    # Pass through command line arguments
    ARGS="$@"
fi

# Run the application
echo -e "${PINK}🍵 Starting Hello Kitty BubbleTea TUI...${RESET}"
echo ""

# Change to the source directory for the run
cd src

# Run the main module
"$PYTHON_EXEC" -m hello_kitty_dashboard.main $ARGS

echo ""
echo -e "${PINK}👋 Sayonara! Thanks for using Hello Kitty BubbleTea TUI! 🌸${RESET}"