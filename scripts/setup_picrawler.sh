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

# Install system dependencies (required before pip packages)
echo "[4/9] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y portaudio19-dev  # Required for pyaudio
echo "      System dependencies installed"

# Upgrade pip
echo "[5/9] Upgrading pip and installing dependencies..."
pip install --upgrade pip wheel setuptools

# Install requirements
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "      Installing from requirements.txt..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    echo "      [WARNING] requirements.txt not found!"
fi

# Ensure correct robot-hat package (CRITICAL: PyPI has two packages with similar names!)
echo "[6/9] Installing correct robot-hat package (SunFounder)..."
pip uninstall robot_hat robot-hat -y 2>/dev/null || true
pip install git+https://github.com/sunfounder/robot-hat.git@v2.0
echo "      SunFounder robot-hat installed"

# Build VL53L0X library from source (requires sudo for C library)
echo "[7/9] Building VL53L0X ToF sensor library..."
VL53L0X_DIR="/tmp/VL53L0X-python"
if [ -d "$VL53L0X_DIR" ]; then
    rm -rf "$VL53L0X_DIR"
fi
git clone https://github.com/pimoroni/VL53L0X-python.git "$VL53L0X_DIR"
cd "$VL53L0X_DIR"
# Try without sudo first, fall back to sudo if needed
python setup.py install 2>/dev/null || sudo "$VENV_DIR/bin/python" setup.py install
echo "      VL53L0X library installed"

# Install project in editable mode
echo "[8/9] Installing picrawler package (editable mode)..."
cd "$PROJECT_ROOT"
pip install -e .

# Verify installation
echo "[9/9] Verifying installation..."
python -c "import VL53L0X; print('      VL53L0X: OK')" 2>/dev/null || echo "      VL53L0X: FAILED (may need sudo)"
python -c "from components.sensors import sensor_fusion; print('      components: OK')" 2>/dev/null || echo "      components: FAILED"

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
