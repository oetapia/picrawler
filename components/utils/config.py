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
# Options: None, "HC-SR04", "VL53L0X", "VL53L1X", "FRONT_REAR_VL53L0X"
DISTANCE_SENSOR_TYPE = "FRONT_REAR_VL53L0X"  # Dual ToF with multiplexer

# Pin names as strings to avoid creating Pin objects until needed
DISTANCE_SENSOR_CONFIG = {
    "HC-SR04": {"trigger_pin": "D2", "echo_pin": "D3"},
    "VL53L0X": {"i2c_address": 0x29},
    "VL53L1X": {"i2c_address": 0x29},
    "FRONT_REAR_VL53L0X": {
        "mux_address": 0x70,
        "front_channel": 2,
        "rear_channel": 1,
        "i2c_bus": 1
    },
}

# ============================================================================
# MULTIPLEXER CONFIGURATION (for FRONT_REAR_VL53L0X)
# ============================================================================

# PCA9548A I2C Multiplexer settings
MUX_ADDRESS = 0x70
FRONT_TOF_CHANNEL = 2   # SD2: Front VL53L0X sensor
REAR_TOF_CHANNEL = 1    # SD1: Rear VL53L0X sensor
ACCEL_CHANNEL = 7       # SD7: MPU6050 Accelerometer
I2C_BUS = 1

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

# ============================================================================
# TIMING PARAMETERS
# ============================================================================

MCU_RESET_DELAY = 0.2           # Delay after MCU reset (seconds)
BALANCE_SETTLING_TIME = 0.2     # Time to wait after movement before balance (seconds)
DISPLAY_UPDATE_INTERVAL = 0.25  # OLED display refresh interval (seconds)
STATUS_REPORT_INTERVAL = 30     # Status report interval (seconds)
MAIN_LOOP_DELAY = 0.1           # Main navigation loop delay (seconds)
ACTION_SETTLE_DELAY = 0.3       # Delay after actions to settle (seconds)
BACKUP_SETTLE_DELAY = 0.4       # Delay after backup movements (seconds)

# ============================================================================
# REAR SENSOR THRESHOLDS (cm)
# ============================================================================

REAR_DISTANCE_THRESHOLD = 15.0  # Minimum safe distance for backward movement
REAR_DISTANCE_WARNING = 25.0    # Warning threshold for rear sensor
