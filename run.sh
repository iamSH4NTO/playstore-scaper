#!/bin/bash
# Google Play Store Scraper - Auto-Installer & Runner
# This script automatically checks Python, sets up the virtual environment,
# installs all required dependencies (including Playwright and Chromium), and launches the scraper.

# Get current script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "==========================================================="
echo "      Google Play Store Scraper Launcher BY SHANTO         "
echo "==========================================================="

# 1. Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Error: python3 is not installed or not in PATH."
    echo "    Please install Python 3 and try again."
    exit 1
fi

# 2. Setup virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo "[*] Virtual environment (.venv) not found. Creating it..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[!] Failed to create virtual environment."
        exit 1
    fi
fi

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install/Verify dependencies
echo "[*] Verifying and installing dependencies..."
pip install --upgrade pip -q
pip install -r scraper/requirements.txt -q
if [ $? -ne 0 ]; then
    echo "[!] Error: Failed to install python dependencies."
    exit 1
fi

# 5. Install Playwright browser binaries
if [ ! -f ".venv/playwright_installed" ]; then
    echo "[*] Installing Playwright Chromium browser binaries (this happens once)..."
    playwright install chromium
    if [ $? -ne 0 ]; then
        echo "[!] Error: Failed to install Playwright Chromium browser."
        exit 1
    fi
    touch ".venv/playwright_installed"
fi

# 6. Launch the scraper
echo "[+] Setup complete! Launching scraper..."
echo "=================================================="

python scraper/scraper.py "$@"
