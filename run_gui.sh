#!/bin/bash
# AEO Analyzer ERA — GUI Launcher (Linux)

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/venv"

if [ ! -d "$VENV" ]; then
    echo "[!] venv not found. Run: bash install.sh first"
    exit 1
fi

source "$VENV/bin/activate"
echo "[✓] Launching AEO Analyzer ERA — GUI..."
python3 "$PROJECT_DIR/aeo_analyzer_gui.py"
