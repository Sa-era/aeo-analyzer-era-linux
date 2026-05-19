#!/bin/bash
# ============================================================
#  AEO Analyzer ERA — Linux / Kali Setup Script
#  Run this ONCE to set up your environment
#  Usage: bash install.sh
# ============================================================

set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/venv"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   AEO Analyzer ERA — Linux Setup                ║"
echo "║   by SA Era                                      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Step 1 — Remove broken venv if owned by root
if [ -d "$VENV" ]; then
    echo "[1/5] Removing old venv..."
    sudo rm -rf "$VENV"
    sudo chown -R "$USER:$USER" "$PROJECT_DIR"
    echo "      Done"
else
    echo "[1/5] No existing venv found, skipping..."
fi

# Step 2 — Create fresh venv
echo "[2/5] Creating virtual environment..."
python3 -m venv "$VENV"
echo "      Created at $VENV"

# Step 3 — Activate
echo "[3/5] Activating venv..."
source "$VENV/bin/activate"
echo "      Active: $(which python3)"

# Step 4 — Install packages
echo "[4/5] Installing packages..."
pip install --upgrade pip --quiet

packages=("requests" "beautifulsoup4" "lxml" "rich" "textstat" "flet" "flet-desktop")
for pkg in "${packages[@]}"; do
    echo -n "      $pkg ... "
    pip install "$pkg" --quiet && echo "OK" || echo "FAILED"
done

# Step 5 — Verify
echo "[5/5] Verifying..."
python3 -c "import requests; print('      requests     OK')"
python3 -c "import bs4;      print('      bs4          OK')"
python3 -c "import flet;     print('      flet         OK')"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Setup complete!                                ║"
echo "║                                                  ║"
echo "║   Launch GUI:  bash run_gui.sh                   ║"
echo "║   Launch CLI:  bash run_cli.sh                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
