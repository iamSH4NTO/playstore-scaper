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

# 1. Check if Python 3 is installed and working
if ! python3 --version &> /dev/null; then
    echo "[!] python3 is not installed or not working."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "[*] macOS detected. Checking for Homebrew..."
        
        # Check if brew command exists, or if it is installed in standard locations but not in PATH
        if ! command -v brew &> /dev/null; then
            if [ -f "/opt/homebrew/bin/brew" ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [ -f "/usr/local/bin/brew" ]; then
                eval "$(/usr/local/bin/brew shellenv)"
            fi
        fi

        if command -v brew &> /dev/null; then
            echo "[*] Homebrew found. Installing Python 3..."
            brew install python
        else
            echo "[*] Homebrew not found. Installing Homebrew (this requires sudo/admin password)..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # Setup Homebrew environment after install
            if [ -f "/opt/homebrew/bin/brew" ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [ -f "/usr/local/bin/brew" ]; then
                eval "$(/usr/local/bin/brew shellenv)"
            fi

            if command -v brew &> /dev/null; then
                echo "[*] Homebrew installed successfully. Installing Python 3..."
                brew install python
            else
                echo "[!] Failed to install or load Homebrew. Triggering Xcode Command Line Tools as fallback..."
                xcode-select --install
                echo "==========================================================="
                echo "[!] A popup has appeared on your screen asking to install Command Line Tools."
                echo "    Please click 'Install' to install them (which includes Python 3)."
                echo "    After the installation is complete, run this script again."
                echo "==========================================================="
                exit 1
            fi
        fi
    else
        echo "[!] Error: python3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
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

# 3. Verify/Install dependencies using venv python directly
echo "[*] Verifying and installing dependencies..."
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/python -m pip install -r scraper/requirements.txt -q
if [ $? -ne 0 ]; then
    echo "[!] Error: Failed to install python dependencies."
    exit 1
fi

# 4. Install Playwright browser binaries
if [ ! -f ".venv/playwright_installed" ]; then
    echo "[*] Installing Playwright Chromium browser binaries (this happens once)..."
    .venv/bin/playwright install chromium
    if [ $? -ne 0 ]; then
        echo "[!] Error: Failed to install Playwright Chromium browser."
        exit 1
    fi
    touch ".venv/playwright_installed"
fi

# 5. Launch the scraper
echo "[+] Setup complete! Launching scraper..."
echo "=================================================="

.venv/bin/python scraper/scraper.py "$@"
