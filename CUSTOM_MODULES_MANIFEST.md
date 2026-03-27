# Custom Modules Manifest - v3.0

**Version:** 3.0 (Production)  
**Date:** March 17, 2026  
**Purpose:** Inventory of custom modules for Picrawler robot

---

## Overview

This document catalogs all custom modules in the v3.0 production branch. These modules extend the factory `picrawler` core with sensors, navigation, autonomy, and control capabilities.

**Total Size:** ~3.5MB  
**Total Files:** 62 Python files  
**Status:** Production-ready for Raspberry Pi deployment

---

## Module Structure

```
picrawler/
├── components/          # Hardware interface layer (3.2MB, 47 files)
├── manual_control/      # Manual operation systems (184KB, 8 files)
└── self_aware/          # Autonomous navigation (164KB, 7 files)
```

---

## 1. Components Module (Hardware Interface Layer)

**Path:** `components/`  
**Size:** 3.2MB  
**Files:** 47 Python files

### Sensors (`components/sensors/`)
Hardware abstraction for all robot sensors:

**Core Sensors:**
- `battery_status.py` - Battery voltage monitoring
- `ir_distance.py` - 4-leg IR floor sensors
- `accelerometer.py` - ADXL345 tilt/orientation
- `front_rear_tof_sensor.py` - Dual VL53L0X ToF sensors via multiplexer
- `pca9548a_mux.py` - I2C multiplexer driver
- `distance_sensor.py` - Factory function for sensor types
- `floor_analyzer.py` - Floor danger detection logic
- `sensor_fusion.py` - **⭐ Unified sensor interface hub**
- `ps4_control.py` - PS4 controller input (optional)

**ToF Library:**
- `vl53l0x_lib/VL53L0X.py` - VL53L0X driver
- `vl53l0x_lib/vl53l0x_mp.py` - Multi-platform support

### Navigation (`components/navigation/`)
Motion control and obstacle avoidance:

- `motion_controller.py` - Smooth speed ramping and transitions
- `obstacle_handler.py` - Decision-making for obstacles
- `balance.py` - Dynamic balance pose calculation

### Navigation State (`components/navigation_state/`)
State machine for autonomous behavior:

- `states.py` - RobotState enum (EXPLORING, AVOIDING, STUCK, etc.)
- `recovery.py` - StuckDetector with escalating escape patterns

### Display (`components/screens/`)
Visual feedback via OLED:

- `oled.py` - Main OLED interface (direct connection)
- `oled_mux.py` - OLED via multiplexer (alternative)
- `icons.py` - Icon definitions
- `imageConvert.py` - Image conversion utilities
- `font5x8.bin` - Font file

### Audio (`components/sounds/`)
Sound effects and text-to-speech:

- `library.py` - Sound effect paths
- `audio_manager.py` - Audio playback manager
- `tts_manager.py` - Text-to-speech manager
- `glados/*.wav` - GLaDOS voice effects
- `source/*.wav` - Standard sound effects

### Utilities (`components/utils/`)
Configuration and helpers:

- `config.py` - **⭐ Centralized configuration** (sensor types, thresholds, speeds)
- `display.py` - Console display utilities

### Camera (`components/camera/`)
Vision system (optional):

- `simple_camera.py` - Basic Picamera2 interface
- `vilib_detector.py` - Computer vision detection (optional)

### Additional Modules
- `motion/` - Motion poses and patterns
- `save/` - Video/file saving utilities
- `server/` - Flask web server (optional)

---

## 2. Manual Control Module

**Path:** `manual_control/`  
**Size:** 184KB  
**Files:** 8 Python files

### Core Files
- `startup.py` - **⭐ Button-based launcher** (USR/RST buttons)
- `scripts/keyboard_control.py` - Manual keyboard control
- `scripts/tracking.py` - **⭐ Production tracking** (consolidated from dev iterations)
- `scripts/balance.py` - Balance testing tool
- `scripts/restapi3.py` - REST API control (optional)

### Dev-only Files (not in v3.0 production)
- `scripts/tracking2.py` - Tracking iteration (dev only)
- `scripts/tracking5.py` - Tracking iteration (dev only)
- `scripts/tracking6.py` - Tracking iteration (dev only)

### Web UI (Optional)
- `client/webui.html` - Browser-based control interface
- `scripts/camera_trigger/` - Camera trigger scripts

### Specialty Scripts
- `scripts/nohat/tracking_nohat2.py` - No-HAT version for testing (dev only)

**Recommended:** Use `tracking.py` for best performance

---

## 3. Self-Aware Module (Autonomous Navigation)

**Path:** `self_aware/`  
**Size:** 164KB  
**Files:** 7 Python files

### Core Autonomous System
- `autonomous_navigator.py` - **⭐⭐⭐ Main autonomous navigation system**
- `autonomous_navigator_with_logging.py` - Autonomous with data logging

**Architecture:**
```
AutonomousNavigator
├── SensorHub (sensor_fusion.py)
├── SmoothMotionController (motion_controller.py)
├── ObstacleHandler (obstacle_handler.py)
├── StuckDetector (recovery.py)
└── Picrawler (robot control)
```

**Capabilities:**
- Multi-sensor obstacle avoidance (ToF front/rear + IR floor)
- Dynamic balance correction
- Stuck detection with escalating escape patterns
- State machine-based behavior
- TTS announcements

### Data Collection (Optional)
- `data_logger.py` - Sensor data logging to CSV/JSON
- `data_logger_with_photos.py` - Logging with camera captures
- `photo_logger.py` - Photo-only logger
- `dataset_utils.py` - Dataset utilities

### Machine Learning (Future)
- `create_ml_notebook.py` - ML notebook generator
- `ml_next_move_prediction.ipynb` - Next-move prediction model

### Documentation
- `README.md` - Module overview
- `AUTONOMOUS_NAVIGATION.md` - Navigation system details
- `QUICKSTART_ML.md` - ML quickstart guide

---

## Hardware Configuration

**Your Setup:**
- **PCA9548A Multiplexer** (I2C address: 0x70)
- **Dual VL53L0X ToF sensors** via multiplexer
  - Front sensor on channel 0
  - Rear sensor on channel 1
- **ADXL345 Accelerometer** via multiplexer (channel 2)
- **SSD1306 OLED Display** - Direct connection to Robot HAT
- **IR Floor Sensors** (FL, FR, BL, BR)

**Configuration:** Set in `components/utils/config.py`
```python
DISTANCE_SENSOR_TYPE = "FRONT_REAR_VL53L0X"
```

---

## Key Entry Points

### 1. **Autonomous Navigation**
```bash
python3 self_aware/autonomous_navigator.py
```
Full autonomous exploration with obstacle avoidance

### 2. **Autonomous with Logging**
```bash
python3 self_aware/autonomous_navigator_with_logging.py
```
Autonomous mode with sensor data logging

### 3. **Manual Tracking**
```bash
python3 manual_control/scripts/tracking.py
```
Manual control with obstacle avoidance

### 4. **Button-Based Startup**
```bash
python3 manual_control/startup.py
```
- Press USR button → Keyboard control
- Press RST button → Autonomous tracking

---

## Dependencies

**Required:**
- `robot_hat` - Robot HAT library (factory)
- `picrawler` - Core picrawler module (factory)
- `picamera2` - Camera interface (if using camera)
- `smbus2` - I2C communication
- `Pillow` - Image processing (OLED)
- `pygame` - Audio playback

**Optional:**
- `vilib` - Computer vision library
- `flask` - Web server

---

## Version History

- **v3.0** (March 2026) - Production release, cleaned and packaged
- **v2.0** (March 2026) - Development branch with all features
- **v1.0** (Original) - Factory baseline

---

## Notes for v4.0 Migration

See `V4_MIGRATION_GUIDE.md` for instructions on migrating these modules to future factory updates.

**Key Points:**
1. All custom code is isolated in 3 directories
2. No modifications to factory `picrawler/` core
3. Configuration centralized in `components/utils/config.py`
4. Easy to copy/restore from backup

---

**Generated:** March 17, 2026  
**Branch:** v3.0 (production)
