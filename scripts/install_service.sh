#!/bin/bash
# ==============================================================================
# PiCrawler Service Installation Script
# ==============================================================================
# Installs the systemd service for PiCrawler auto-start on boot.
# Must be run with sudo.
#
# Usage:
#   sudo bash scripts/install_service.sh
#
# Commands after installation:
#   sudo systemctl status picrawler    # Check status
#   sudo systemctl start picrawler     # Start service
#   sudo systemctl stop picrawler      # Stop service
#   sudo systemctl restart picrawler   # Restart service
#   journalctl -u picrawler -f         # View live logs
#   journalctl -u picrawler --since "5 min ago"  # Recent logs
#
# ==============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/picrawler.service"
SERVICE_NAME="picrawler"
SYSTEMD_DIR="/etc/systemd/system"

echo "=============================================="
echo "PiCrawler Service Installation"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] This script must be run with sudo"
    echo "        Usage: sudo bash scripts/install_service.sh"
    exit 1
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "[ERROR] Service file not found: $SERVICE_FILE"
    exit 1
fi

# Check if venv exists
VENV_PYTHON="/home/pi/picrawler/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "        Run setup first: bash scripts/setup_picrawler.sh"
    exit 1
fi

# Stop service if running
echo "[1/4] Stopping existing service (if any)..."
systemctl stop $SERVICE_NAME 2>/dev/null || true

# Copy service file
echo "[2/4] Installing service file..."
cp "$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_NAME.service"
echo "      Copied to: $SYSTEMD_DIR/$SERVICE_NAME.service"

# Reload systemd
echo "[3/4] Reloading systemd daemon..."
systemctl daemon-reload

# Enable service
echo "[4/4] Enabling service for auto-start..."
systemctl enable $SERVICE_NAME

echo ""
echo "=============================================="
echo "Installation Complete!"
echo "=============================================="
echo ""
echo "Service commands:"
echo "  sudo systemctl start picrawler     # Start now"
echo "  sudo systemctl stop picrawler      # Stop"
echo "  sudo systemctl status picrawler    # Check status"
echo "  sudo systemctl disable picrawler   # Disable auto-start"
echo ""
echo "View logs:"
echo "  journalctl -u picrawler -f         # Live logs"
echo "  journalctl -u picrawler -n 50      # Last 50 lines"
echo ""
echo "To start the service now:"
echo "  sudo systemctl start picrawler"
echo ""
