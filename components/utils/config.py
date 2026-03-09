#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared configuration constants for PiCrawler navigation.

These constants define hardware parameters, movement speeds, thresholds,
and other configuration values used across different navigation modes.
"""

# ============================================================================
# DISTANCE SENSOR CONFIGURATION
# ============================================================================

# Distance sensor type (change here!)
# Set to None to disable distance sensor and rely only on IR sensors
DISTANCE_SENSOR_TYPE = None  # Options: None, "HC-SR04", "VL53L0X", "VL53L1X"

# Pin names as strings to avoid creating Pin objects until needed
DISTANCE_SENSOR_CONFIG = {
    "HC-SR04": {"trigger_pin": "D2", "echo_pin": "D3"},
    "VL53L0X": {"i2c_address": 0x29},
    "VL53L1X": {"i2c_address": 0x29},
}

# ============================================================================
# MOVEMENT PARAMETERS
# ============================================================================

# Speed settings (0-100)
SPEED_MAX = 80
SPEED_NORMAL = 70
SPEED_CAUTION = 50
SPEED_MIN = 35

# ============================================================================
# DISTANCE THRESHOLDS (cm)
# ============================================================================

DISTANCE_DANGER = 15    # Emergency stop distance
DISTANCE_WARNING = 25   # Slow down distance
DISTANCE_SAFE = 40      # Safe distance for full speed

# ============================================================================
# TILT THRESHOLDS (degrees)
# ============================================================================

TILT_CAUTION = 10.0     # Slow down when tilted beyond this
TILT_DANGER = 20.0      # Emergency procedures when tilted beyond this

# ============================================================================
# BALANCE CORRECTION PARAMETERS
# ============================================================================

BALANCE_DEADZONE = 3.0      # Ignore tilt below this value (degrees)
BALANCE_MAX_TILT = 25.0     # Maximum tilt for balance calculations (degrees)
BALANCE_SPEED = 60          # Speed for balance correction movements

# ============================================================================
# LEG POSITIONS FOR BALANCE
# ============================================================================

# Leg positions [x, y, z] coordinates
LEG_EXTENDED = [60, 45, -75]    # Extended down (compensating for tilt)
LEG_NEUTRAL = [45, 37, -52]     # Normal standing position
LEG_RETRACTED = [30, 30, -30]   # Retracted up (opposite side of tilt)

# ============================================================================
# SENSOR MAPPINGS
# ============================================================================

# Leg IR sensor mapping (leg_index: sensor_name)
LEG_IR = {
    0: 'fl',  # Front Left
    1: 'fr',  # Front Right
    2: 'bl',  # Back Left
    3: 'br',  # Back Right
}
