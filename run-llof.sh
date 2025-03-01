#!/bin/bash

# Check if python3 is installed.
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is not installed. Attempting to install via brew..."
    if command -v brew >/dev/null 2>&1; then
        brew install python3 || { echo "Failed to install python3 via brew. Please install it manually."; exit 1; }
    else
        echo "Homebrew is not installed. Please install python3 manually."
        exit 1
    fi
fi

# Check if python3 has the venv module.
python3 -c "import venv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "The venv module is not available in your python3 installation. Please install a version of python that includes venv."
    exit 1
fi

# Check if pip3 is installed.
if ! command -v pip3 >/dev/null 2>&1; then
    echo "pip3 is not installed. Attempting to install pip3..."
    python3 -m ensurepip --upgrade || { echo "Failed to install pip3. Please install it manually."; exit 1; }
fi

# Name of the virtual environment directory.
VENV_DIR="venv"

# Check if virtual environment exists; if not, create it.
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR" || { echo "Failed to create virtual environment"; exit 1; }
fi

# Activate the virtual environment.
source "$VENV_DIR/bin/activate"
echo "Virtual environment activated."

# Upgrade pip (optional, but recommended)
pip install --upgrade pip

# Check if Selenium is installed.
python -c "import selenium" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Selenium not found. Installing..."
    pip install selenium || { echo "Failed to install Selenium"; exit 1; }
else
    echo "Selenium is already installed."
fi

# Start the llof.py script.
echo "Starting llof.py..."
python llof.py