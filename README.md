# PiCrawler v3.0

Production-ready autonomous robot software for the SunFounder PiCrawler, built on top of the factory `picrawler` library with custom sensor fusion, navigation, and control modules.

---

## Quick Start

```bash
# Autonomous navigation (recommended)
python3 self_aware/autonomous_navigator.py

# Button launcher (headless operation)
python3 manual_control/startup.py
#   USR button → Keyboard/REST control
#   RST button → Autonomous navigation

# Manual keyboard + PS4 control
python3 manual_control/scripts/keyboard_control.py

# Color tracking (camera-based)
python3 manual_control/scripts/tracking.py
```

---

## Architecture

```
picrawler/
├── picrawler/                 # Factory core (DO NOT MODIFY)
│   ├── picrawler.py           # Robot control API
│   └── version.py
│
├── components/                # Custom hardware interface layer
│   ├── sensors/               # Sensor drivers
│   │   ├── sensor_fusion.py   # ⭐ Unified sensor hub
│   │   ├── ir_distance.py     # 4-leg IR floor sensors
│   │   ├── accelerometer.py   # ADXL345 tilt/orientation
│   │   ├── front_rear_tof_sensor.py  # Dual VL53L0X ToF via mux
│   │   ├── pca9548a_mux.py    # PCA9548A I2C multiplexer
│   │   ├── distance_sensor.py # Sensor factory
│   │   ├── floor_analyzer.py  # Floor danger classification
│   │   ├── battery_status.py  # Battery monitoring
│   │   └── ps4_control.py     # PS4 gamepad input
│   │
│   ├── navigation/            # Motion control
│   │   ├── motion_controller.py   # Smooth speed ramping
│   │   ├── obstacle_handler.py    # Obstacle decision-making
│   │   └── balance.py             # Dynamic tilt compensation
│   │
│   ├── navigation_state/      # State machine
│   │   ├── states.py          # RobotState enum
│   │   └── recovery.py        # Stuck detection & escape
│   │
│   ├── screens/               # OLED display
│   │   ├── oled.py            # SSD1306 interface
│   │   ├── icons.py           # Icon definitions
│   │   └── imageConvert.py    # Image utilities
│   │
│   ├── sounds/                # Audio
│   │   ├── audio_manager.py   # Playback manager
│   │   ├── tts_manager.py     # Text-to-speech
│   │   ├── library.py         # Sound file paths
│   │   ├── glados/            # GLaDOS voice effects
│   │   └── source/            # Standard sound effects
│   │
│   ├── camera/                # Vision
│   │   ├── simple_camera.py   # Picamera2 interface
│   │   └── vilib_detector.py  # Color/object detection
│   │
│   ├── motion/                # Pose definitions
│   │   └── poses.json         # Named poses (spread_out, compact, wave, etc.)
│   │
│   ├── save/                  # Recording
│   │   ├── save_to_file.py    # Video recorder
│   │   └── convert_video.py   # Format conversion
│   │
│   ├── server/                # Web server
│   │   └── flask.py           # Flask app factory
│   │
│   └── utils/                 # Configuration
│       ├── config.py          # ⭐ Centralized settings
│       └── display.py         # Console utilities
│
├── manual_control/            # Manual operation
│   ├── startup.py             # Button-based launcher
│   ├── scripts/
│   │   ├── keyboard_control.py    # Keyboard + PS4 control
│   │   ├── tracking.py            # Color-tracking navigation
│   │   ├── restapi3.py            # REST API + web UI
│   │   ├── balance.py             # Balance testing tool
│   │   └── camera_trigger/
│   │       └── flaskirapi.py      # Flask camera server
│   └── client/
│       └── webui.html             # Browser control UI
│
├── self_aware/                # Autonomous navigation
│   ├── autonomous_navigator.py            # ⭐ Main autonomous system
│   ├── autonomous_navigator_with_logging.py  # + data logging
│   ├── data_logger.py         # Sensor data logging
│   ├── data_logger_with_photos.py  # Logging with photos
│   └── photo_logger.py        # Photo-only logger
│
└── examples/                  # Factory examples
```

---

## Hardware Configuration

```
Robot HAT
├── PCA9548A Multiplexer (0x70)
│   ├── Channel 0: VL53L0X ToF (Front)
│   ├── Channel 1: VL53L0X ToF (Rear)
│   └── Channel 2: ADXL345 Accelerometer
├── SSD1306 OLED (0x3C) — Direct I2C
├── IR Floor Sensors × 4 (FL, FR, BL, BR)
└── HC-SR04 Ultrasonic (D2/D3) — Optional
```

All sensor configuration is centralized in `components/utils/config.py`.

---

## Components Overview

### Sensor Fusion (`components/sensors/sensor_fusion.py`)
Unified `SensorHub` class that aggregates all sensor data — front/rear ToF distance, IR floor danger, accelerometer tilt — into a single interface used by the navigation system.

### Navigation (`components/navigation/`)
- **Motion Controller** — Smooth speed transitions with ramping, caution/normal/max speed modes
- **Obstacle Handler** — Decides avoidance direction using distance readings and tilt bias
- **Balance** — Real-time leg pose adjustments to keep the body level on uneven terrain

### State Machine (`components/navigation_state/`)
Robot states: `EXPLORING` → `AVOIDING_OBSTACLE` → `AVOIDING_FLOOR_DANGER` → `TILT_CORRECTION` → `STUCK` → `EMERGENCY`. The `StuckDetector` tracks repeated failures and escalates through escape patterns.

### Autonomous Navigator (`self_aware/autonomous_navigator.py`)
The main brain — orchestrates the sensor hub, motion controller, obstacle handler, and state machine in a priority-based loop:
1. Floor danger (prevents falls)
2. Distance obstacles
3. Tilt correction
4. Stuck detection & escape
5. Normal forward exploration

---

## Dependencies

```bash
pip3 install robot_hat picamera2 smbus2 Pillow pygame
```

Optional: `vilib` (color tracking), `flask` (web server), `readchar` (keyboard control)

---

## Troubleshooting

```bash
# Check I2C devices (expect 0x70 mux, 0x3c OLED)
i2cdetect -y 1

# Fix import errors — run from project root
cd ~/picrawler
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Test audio
aplay /usr/share/sounds/alsa/Front_Center.wav
```
