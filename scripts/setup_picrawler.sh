#!/bin/bash
# ==============================================================================
# PiCrawler Setup Script
# ==============================================================================
# Creates a virtual environment and installs all dependencies.
# Run this once on a fresh Raspberry Pi after cloning the repository.
#
# Usage:
#   cd /home/pi/picrawler
#   bash scripts/setup_picrawler.sh
#
# ==============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
PYTHON_CMD="python3"

echo "=============================================="
echo "PiCrawler Setup Script"
echo "=============================================="
echo "Project root: $PROJECT_ROOT"
echo "Virtual env:  $VENV_DIR"
echo ""

# Check if running as pi user
if [ "$(whoami)" != "pi" ]; then
    echo "[WARNING] Not running as 'pi' user. Permissions may need adjustment."
fi

# Check Python version
echo "[1/5] Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "      Found: $PYTHON_VERSION"

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo "      Existing venv found. Removing..."
    rm -rf "$VENV_DIR"
fi
$PYTHON_CMD -m venv "$VENV_DIR"
echo "      Created: $VENV_DIR"

# Activate virtual environment
echo "[3/5] Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "      Active Python: $(which python)"

# Upgrade pip
echo "[4/5] Upgrading pip and installing dependencies..."
pip install --upgrade pip wheel setuptools

# Install requirements
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "      Installing from requirements.txt..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    echo "      [WARNING] requirements.txt not found!"
fi

# Install project in editable mode
echo "[5/5] Installing picrawler package (editable mode)..."
cd "$PROJECT_ROOT"
pip install -e .

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "To activate the virtual environment manually:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To install the systemd service:"
echo "  sudo bash scripts/install_service.sh"
echo ""
echo "To run startup.py manually:"
echo "  $VENV_DIR/bin/python manual_control/startup.py"
echo ""
