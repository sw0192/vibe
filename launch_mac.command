#!/bin/bash
set -euo pipefail

REPO_URL="https://github.com/sw0192/vibe.git"
APP_DIR="$HOME/vibe-file-converter"

echo
echo "FILE CONVERTER launcher"
echo "======================="
echo

if ! command -v git >/dev/null 2>&1; then
  echo "Git was not found."
  echo "Install Xcode Command Line Tools or Git, then run this launcher again."
  read -r -p "Press Enter to exit."
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python was not found."
  echo "Install Python 3 from https://www.python.org/downloads/macos/"
  read -r -p "Press Enter to exit."
  exit 1
fi

if [ -d "$APP_DIR/.git" ]; then
  echo "Updating the latest code..."
  cd "$APP_DIR"
  git pull --ff-only
else
  if [ -e "$APP_DIR" ]; then
    echo "$APP_DIR already exists, but it is not a git repository."
    echo "Rename or delete that folder, then run this launcher again."
    read -r -p "Press Enter to exit."
    exit 1
  fi

  echo "Cloning the app from GitHub..."
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "Preparing the Python virtual environment..."
if [ ! -x ".venv/bin/python" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source ".venv/bin/activate"

echo "Installing required libraries..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Starting the converter. Your browser will open automatically."
python run_converter.py

echo
echo "The converter has stopped."
read -r -p "Press Enter to exit."
