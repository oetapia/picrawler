# Migration Plan: v2.0 → v3.0

**Date:** March 14, 2026  
**Branch:** v2.0 → v3.0  
**Focus:** components/, manual_control/, self_aware/

---

## Hardware Configuration

Your current setup:
- ✅ **PCA9548A Multiplexer** (I2C address: 0x70)
- ✅ **Dual VL53L0X ToF sensors** via multiplexer
  - Front sensor on channel 0
  - Rear sensor on channel 1
- ✅ **ADXL345 Accelerometer** via multiplexer (channel 2)
- ✅ **SSD1306 OLED Display** - Direct connection to Robot HAT
- ✅ **IR Floor Sensors** (FL, FR, BL, BR)

---

## Executive Summary

**What happened in v3.0:**
- v3.0 is a **stripped-down version** - almost all code in components/, manual_control/, and self_aware/ was deleted
- Only `__pycache__` directories remain
- This appears to be a factory reset or cleanup branch

**Migration Strategy:**
Selectively restore v2.0 functionality to v3.0, focusing on:
1. Core sensor/hardware infrastructure
2. Navigation system with obstacle avoidance
3. Manual control interfaces
4. Autonomous navigation system

**Skip:**
- `/old` directories
- Non-factory examples
- Backup files (*.backup)
- Outdated scripts (tracking.py, tracking5.py, tracking6.py)
- Verbose documentation files (keep READMEs only)

---

## Phase 1: Foundation - Utilities & Configuration

### Priority: CRITICAL (Do First)

#### Files to Restore:

```
components/utils/
├── __init__.py
├── config.py                 # ⭐ Centralized configuration constants
└── display.py                # Console display utilities
```

**Why First?**
- All other modules import from `components.utils.config`
- Contains critical constants: DISTANCE_SENSOR_TYPE, sensor thresholds, speeds, I2C addresses

**Key Configuration Values (from config.py):**
```python
DISTANCE_SENSOR_TYPE = "FRONT_REAR_VL53L0X"  # Your hardware
DISTANCE_SENSOR_CONFIG = {
    "FRONT_REAR_VL53L0X": {
        "use_multiplexer": True,
        "mux_address": 0x70,
        "front_channel": 0,
        "rear_channel": 1
    }
}
ACCEL_CHANNEL = 2  # Accelerometer on multiplexer channel 2
```

**Testing:**
```bash
cd /Users/tapiapil/dev2/picrawler
python3 -c "from components.utils import config; print(config.DISTANCE_SENSOR_TYPE)"
```

---

## Phase 2: Sensors - Hardware Interface Layer

### Priority: CRITICAL

#### 2.1 Base Sensor Files

```
components/sensors/
├── __init__.py
├── battery_status.py         # Battery voltage/status
├── ir_distance.py            # IR floor sensors (4 legs)
└── accelerometer.py          # ADXL345 interface
```

**Testing:**
```bash
# Test battery
python3 -c "from components.sensors import battery_status; print(battery_status.get_battery_state())"

# Test accelerometer (via multiplexer)
python3 -c "from components.sensors import accelerometer; accelerometer.wake(); print(accelerometer.get_tilt())"

# Test floor sensors
python3 -c "from components.sensors import ir_distance; print(ir_distance.read_legs())"
```

#### 2.2 Distance Sensors (Multiplexer-Aware)

```
components/sensors/
├── pca9548a_mux.py           # ⭐ Multiplexer driver
├── distance_sensor.py        # Factory function for sensor types
├── front_rear_tof_sensor.py  # ⭐ Dual ToF with multiplexer
└── floor_analyzer.py         # Floor danger analysis
```

**Critical:** `front_rear_tof_sensor.py` manages:
- Multiplexer channel switching
- Front/rear sensor coordination
- Read filtering (median of 3 readings)
- Sensor initialization with proper delays

**Testing:**
```bash
# Test multiplexer
python3 components/sensors/pca9548a_diagnostic.py

# Test dual ToF
python3 -c "
from components.sensors.front_rear_tof_sensor import FrontRearToFSensor
sensor = FrontRearToFSensor()
print('Front:', sensor.read_front_filtered())
print('Rear:', sensor.read_rear_filtered())
"
```

#### 2.3 Sensor Fusion Hub

```
components/sensors/
└── sensor_fusion.py          # ⭐⭐⭐ Unified sensor interface
```

**Why Critical?**
- Single entry point for ALL sensor readings
- Handles multiplexer channel switching automatically
- Provides debouncing for floor sensors
- Used by autonomous_navigator.py and tracking scripts

**Key Features:**
```python
hub = SensorHub(distance_sensor_type="FRONT_REAR_VL53L0X")

# Automatic multiplexer handling
front_dist = hub.get_front_distance()  # Switches to channel 0
rear_dist = hub.get_rear_distance()    # Switches to channel 1
pitch, roll = hub.get_tilt()           # Switches to channel 2 (accel)

# Debounced floor danger
danger, action = hub.check_floor_danger_debounced()
```

**Testing:**
```bash
python3 -c "
from components.sensors.sensor_fusion import SensorHub
hub = SensorHub('FRONT_REAR_VL53L0X')
print(hub.get_sensor_status())
"
```

#### 2.4 Optional Sensor Files (Skip for now)

- ❌ `ps4_control.py` - PS4 controller (not needed initially)
- ❌ `*_diagnostic.py` - Diagnostic scripts (use only if troubleshooting)
- ❌ `README_MULTIPLEXER.md` - Keep if helpful

---

## Phase 3: Display & Feedback

### Priority: HIGH

#### 3.1 OLED Display (Direct Connection)

```
components/screens/
├── __init__.py
├── oled.py                   # ⭐ Main OLED interface
├── icons.py                  # Icon definitions
├── imageConvert.py           # Image conversion utilities
└── font5x8.bin               # Font file
```

**Note:** Your OLED is **directly connected** to Robot HAT (not on multiplexer), so:
- Use `oled.py` (not `oled_mux.py`)
- No channel switching needed
- Simpler initialization

**Testing:**
```bash
python3 -c "
from components.screens import oled
oled.update_display(header='Test', text='OLED Working')
"
```

#### 3.2 Optional Display Files (Skip for now)

- ❌ `oled_mux.py` - Multiplexer version (not needed for your setup)
- ❌ `oled_diagnostic.py`, `oled_diagnostic_v2.py` - Diagnostics
- ❌ `test_oled_with_mux.py` - Test script
- ❌ `OLED_FIX_GUIDE.md`, `OLED_TROUBLESHOOTING.md` - Guides

#### 3.3 Audio Feedback

```
components/sounds/
├── __init__.py
├── library.py                # ⭐ Sound effect paths
├── audio_manager.py          # Audio playback
├── tts_manager.py            # Text-to-speech
└── glados/*.wav              # Sound files
└── source/*.wav              # Sound files
```

**Testing:**
```bash
python3 -c "
from components.sounds import library
from robot_hat import Music
music = Music()
music.sound_play_threading(library.intro)
"
```

---

## Phase 4: Navigation System

### Priority: HIGH

#### 4.1 Motion Control

```
components/navigation/
├── __init__.py
├── motion_controller.py      # ⭐ Smooth speed ramping
├── obstacle_handler.py       # ⭐ Decision-making logic
└── balance.py                # Balance pose calculation
```

**Key Features:**

**motion_controller.py:**
- Smooth acceleration/deceleration
- Emergency stop
- Speed transitions (50 → 60 → 70 over time)

**obstacle_handler.py:**
- Obstacle distance analysis → recommended action
- Floor danger analysis → recovery maneuver
- Stuck detection → escalating escape patterns

**balance.py:**
- Dynamic balance pose based on pitch/roll
- Neutral/compact poses for emergencies

**Testing:**
```bash
python3 -c "
from components.navigation import SmoothMotionController
mc = SmoothMotionController()
for i in range(10):
    print(f'Speed: {mc.update()}')
"
```

#### 4.2 State Management

```
components/navigation_state/
├── __init__.py
├── states.py                 # RobotState enum
└── recovery.py               # StuckDetector class
```

**States:**
- EXPLORING (normal operation)
- AVOIDING_OBSTACLE
- AVOIDING_FLOOR_DANGER
- TILT_CORRECTION
- STUCK
- EMERGENCY

**StuckDetector:**
- Tracks consecutive obstacles/floor dangers
- Provides escalating escape patterns
- Resets after successful moves

**Testing:**
```bash
python3 -c "
from components.navigation_state import RobotState, StuckDetector
detector = StuckDetector()
print(detector.is_stuck())
"
```

#### 4.3 Optional Navigation Files (Skip)

- ❌ `components/motion/poses.json` - Custom poses (not used in main code)
- ❌ `components/save/` - Video/file saving (not needed for navigation)

---

## Phase 5: Camera (Optional)

### Priority: MEDIUM (Can skip initially)

```
components/camera/
├── __init__.py
└── simple_camera.py          # Basic Picamera2 interface
```

**When Needed:**
- Manual control web UI (streaming)
- Computer vision tracking
- Data collection with photos

**Skip:**
- ❌ `vilib_detector.py` - Computer vision (heavy, optional)
- ❌ `camera_diagnostic.py` - Diagnostics
- ❌ `INTEGRATION_GUIDE.md`, `README_VILIB.md`, `VILIB_API_FIXES.md`

---

## Phase 6: Manual Control System

### Priority: HIGH

#### 6.1 Startup System

```
manual_control/
├── __init__.py
└── startup.py                # ⭐ Button-based launcher
```

**Features:**
- USR button (SW) → Keyboard control (restapi3.py)
- RST button → Autonomous tracking (tracking5.py or tracking2.py)
- Battery status on OLED
- TTS announcements

**Testing:**
```bash
# Test imports only (don't run - requires button press)
python3 -c "import manual_control.startup; print('OK')"
```

#### 6.2 Control Scripts

```
manual_control/scripts/
├── keyboard_control.py       # Manual keyboard control
├── tracking2.py              # ⭐ Recommended tracking version
├── balance.py                # Balance testing tool
└── restapi3.py               # REST API control (optional)
```

**Recommended: tracking2.py**
- Uses refactored components
- Clean sensor fusion integration
- Smooth motion control
- Best obstacle avoidance

**Skip:**
- ❌ `tracking.py` - Old version
- ❌ `tracking5.py`, `tracking6.py` - Later iterations (pick one if preferred)
- ❌ `camera_trigger/` - Camera trigger scripts
- ❌ `nohat/` - No-hat versions
- ❌ `README_TRACKING.md` - Documentation

#### 6.3 Web UI (Optional)

```
manual_control/client/
└── webui.html                # Web-based control interface
```

**When Needed:**
- Remote browser control
- Gamepad support
- Camera streaming view

---

## Phase 7: Autonomous Navigation

### Priority: HIGH

#### 7.1 Core Autonomous System

```
self_aware/
├── __init__.py
└── autonomous_navigator.py   # ⭐⭐⭐ Main autonomous system
```

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
- Autonomous exploration
- Multi-sensor obstacle avoidance (ToF front/rear + IR floor)
- Dynamic balance correction
- Stuck detection with escape patterns
- State machine (EXPLORING → AVOIDING → STUCK → etc.)
- TTS announcements

**Testing:**
```bash
# Dry run (will fail without hardware but tests imports)
python3 self_aware/autonomous_navigator.py
```

#### 7.2 Documentation

```
self_aware/
├── README.md                 # Overview
├── AUTONOMOUS_NAVIGATION.md  # Navigation details
├── QUICKSTART_ML.md          # ML quickstart
└── README_ML.md              # ML details
```

#### 7.3 Data Collection (Future - Skip for now)

```
self_aware/
├── data_logger.py            # Sensor data logging
├── data_logger_with_photos.py
├── photo_logger.py
└── dataset_utils.py
```

**When Needed:**
- ML training data collection
- Behavior analysis
- Dataset creation for next-move prediction

#### 7.4 ML Infrastructure (Future - Skip for now)

```
self_aware/
├── ml_next_move_prediction.ipynb
└── create_ml_notebook.py
```

---

## Migration Checklist

### ✅ Phase 1: Foundation (30 min)
- [ ] Create `components/__init__.py`
- [ ] Restore `components/utils/config.py`
- [ ] Restore `components/utils/display.py`
- [ ] Restore `components/utils/__init__.py`
- [ ] **Test:** `from components.utils import config`

### ✅ Phase 2: Sensors (45 min)
- [ ] Restore `components/sensors/__init__.py`
- [ ] Restore `components/sensors/battery_status.py`
- [ ] Restore `components/sensors/ir_distance.py`
- [ ] Restore `components/sensors/accelerometer.py`
- [ ] **Test:** Battery, IR, accelerometer readings
- [ ] Restore `components/sensors/pca9548a_mux.py`
- [ ] Restore `components/sensors/distance_sensor.py`
- [ ] Restore `components/sensors/front_rear_tof_sensor.py`
- [ ] Restore `components/sensors/floor_analyzer.py`
- [ ] **Test:** Multiplexer + dual ToF readings
- [ ] Restore `components/sensors/sensor_fusion.py`
- [ ] **Test:** `SensorHub.get_sensor_status()`

### ✅ Phase 3: Display & Feedback (20 min)
- [ ] Restore `components/screens/__init__.py`
- [ ] Restore `components/screens/oled.py`
- [ ] Restore `components/screens/icons.py`
- [ ] Restore `components/screens/imageConvert.py`
- [ ] Restore `components/screens/font5x8.bin`
- [ ] **Test:** Display "Hello World" on OLED
- [ ] Restore `components/sounds/__init__.py`
- [ ] Restore `components/sounds/library.py`
- [ ] Restore `components/sounds/audio_manager.py`
- [ ] Restore `components/sounds/tts_manager.py`
- [ ] Restore `components/sounds/glados/*.wav`
- [ ] Restore `components/sounds/source/*.wav`
- [ ] **Test:** Play intro sound

### ✅ Phase 4: Navigation (30 min)
- [ ] Restore `components/navigation/__init__.py`
- [ ] Restore `components/navigation/motion_controller.py`
- [ ] Restore `components/navigation/obstacle_handler.py`
- [ ] Restore `components/navigation/balance.py`
- [ ] **Test:** Motion controller speed ramping
- [ ] Restore `components/navigation_state/__init__.py`
- [ ] Restore `components/navigation_state/states.py`
- [ ] Restore `components/navigation_state/recovery.py`
- [ ] **Test:** State transitions

### ✅ Phase 5: Manual Control (30 min)
- [ ] Restore `manual_control/__init__.py`
- [ ] Restore `manual_control/startup.py`
- [ ] **Test:** Import check only
- [ ] Restore `manual_control/scripts/keyboard_control.py`
- [ ] Restore `manual_control/scripts/tracking2.py`
- [ ] Restore `manual_control/scripts/balance.py`
- [ ] Restore `manual_control/scripts/restapi3.py` (optional)
- [ ] **Test:** Run tracking2.py (with robot on blocks)

### ✅ Phase 6: Autonomous System (20 min)
- [ ] Restore `self_aware/__init__.py`
- [ ] Restore `self_aware/autonomous_navigator.py`
- [ ] Restore `self_aware/README.md`
- [ ] Restore `self_aware/AUTONOMOUS_NAVIGATION.md`
- [ ] **Test:** Run autonomous_navigator.py (robot on blocks)

### ✅ Phase 7: Camera (Optional - Skip for now)
- [ ] Restore `components/camera/__init__.py`
- [ ] Restore `components/camera/simple_camera.py`
- [ ] **Test:** Camera streaming

### ✅ Phase 8: Integration Testing (30 min)
- [ ] Test startup.py button press → tracking2.py launch
- [ ] Test startup.py button press → autonomous navigation
- [ ] Test obstacle avoidance (front + rear)
- [ ] Test floor edge detection
- [ ] Test balance correction
- [ ] Test stuck recovery

---

## Testing Strategy

### Unit Tests (Per Component)

**Sensors:**
```bash
# Battery
python3 -c "from components.sensors import battery_status; print(battery_status.get_battery_state())"

# Floor IR
python3 -c "from components.sensors import ir_distance; print(ir_distance.read_legs())"

# Accelerometer (via mux channel 2)
python3 -c "from components.sensors import accelerometer; accelerometer.wake(); print(accelerometer.get_tilt())"

# Multiplexer
python3 -c "from components.sensors.pca9548a_mux import PCA9548A; mux = PCA9548A(); mux.select_channel(0)"

# Dual ToF
python3 -c "from components.sensors.front_rear_tof_sensor import FrontRearToFSensor; s = FrontRearToFSensor(); print(s.read_front_filtered(), s.read_rear_filtered())"

# Sensor Fusion
python3 -c "from components.sensors.sensor_fusion import SensorHub; hub = SensorHub('FRONT_REAR_VL53L0X'); print(hub.get_sensor_status())"
```

**Display:**
```bash
# OLED
python3 -c "from components.screens import oled; oled.update_display('Test', 'Hello World')"

# Sound
python3 -c "from components.sounds import library; from robot_hat import Music; Music().sound_play_threading(library.intro)"
```

**Navigation:**
```bash
# Motion controller
python3 -c "from components.navigation import SmoothMotionController; mc = SmoothMotionController(); print([mc.update() for _ in range(5)])"

# States
python3 -c "from components.navigation_state import RobotState; print(RobotState.EXPLORING.value)"
```

### Integration Tests (With Robot)

**Test 1: Sensor Hub**
```python
from components.sensors.sensor_fusion import SensorHub
hub = SensorHub("FRONT_REAR_VL53L0X")
print("Front:", hub.get_front_distance())
print("Rear:", hub.get_rear_distance())
print("Tilt:", hub.get_tilt())
print("Floor:", hub.get_floor_sensors())
```

**Test 2: Basic Movement (Robot on blocks!)**
```python
from picrawler import Picrawler
robot = Picrawler()
robot.do_action('forward', 1, 50)
robot.do_action('backward', 1, 50)
```

**Test 3: Obstacle Detection**
```python
from components.sensors.sensor_fusion import SensorHub
hub = SensorHub("FRONT_REAR_VL53L0X")
# Place hand in front of robot
while True:
    dist = hub.get_front_distance()
    print(f"Front: {dist:.1f}cm")
    if dist < 20:
        print("OBSTACLE!")
    time.sleep(0.5)
```

**Test 4: Balance Correction (Robot on blocks)**
```python
from components.navigation import compute_balance_pose
from components.sensors.sensor_fusion import SensorHub
from picrawler import Picrawler

hub = SensorHub()
robot = Picrawler()

# Tilt robot and see correction
pitch, roll = hub.get_tilt()
pose = compute_balance_pose(pitch, roll)
robot.do_step(pose, 50)
```

---

## Common Issues & Solutions

### Issue 1: Import Errors
**Symptom:** `ModuleNotFoundError: No module named 'components'`

**Solution:**
```bash
# Add to PYTHONPATH or run from project root
cd /Users/tapiapil/dev2/picrawler
python3 -c "import sys; sys.path.append('.'); from components.sensors import battery_status"
```

### Issue 2: Multiplexer Not Found
**Symptom:** `OSError: [Errno 121] Remote I/O error` or multiplexer not detected

**Solution:**
```bash
# Check I2C devices
i2cdetect -y 1

# Should see 0x70 (multiplexer)
# Verify wiring and power
```

### Issue 3: ToF Sensor Timeout
**Symptom:** `VL53L0X timeout` or distance always 999

**Solution:**
```bash
# Check multiplexer channel switching
# Add delays after channel switch (already in front_rear_tof_sensor.py)
# Verify sensors are powered and wired correctly
```

### Issue 4: OLED Not Responding
**Symptom:** OLED blank or error

**Solution:**
```bash
# Check I2C address (usually 0x3C)
i2cdetect -y 1

# Verify your OLED is direct-connected (not via mux)
# Use oled.py (not oled_mux.py)
```

### Issue 5: Accelerometer Not Working
**Symptom:** `get_tilt()` returns (0.0, 0.0)

**Solution:**
```bash
# Ensure accelerometer is on multiplexer channel 2
# Check ACCEL_CHANNEL in config.py
# Verify channel switching in sensor_fusion.py
```

---

## File Copy Commands (Quick Reference)

```bash
# From v2.0 branch, copy files to v3.0
git checkout v2.0

# Phase 1: Utils
cp -r components/utils/ /tmp/utils_backup/
git checkout v3.0
cp -r /tmp/utils_backup/* components/utils/

# Phase 2: Sensors
git checkout v2.0
cp -r components/sensors/ /tmp/sensors_backup/
git checkout v3.0
cp -r /tmp/sensors_backup/* components/sensors/

# Repeat for other phases...
```

**Alternative:** Use `git restore` from v2.0:
```bash
git checkout v3.0
git restore --source=v2.0 components/utils/
git restore --source=v2.0 components/sensors/
# etc.
```

---

## Dependencies Graph

```
autonomous_navigator.py
├── components.sensors.sensor_fusion (SensorHub)
│   ├── components.sensors.front_rear_tof_sensor (FrontRearToFSensor)
│   │   ├── components.sensors.pca9548a_mux (PCA9548A)
│   │   └── components.sensors.distance_sensor
│   ├── components.sensors.accelerometer
│   ├── components.sensors.ir_distance
│   └── components.utils.config
├── components.navigation.motion_controller (SmoothMotionController)
│   └── components.utils.config
├── components.navigation.obstacle_handler (ObstacleHandler)
│   └── components.utils.config
├── components.navigation.balance (compute_balance_pose)
├── components.navigation_state.states (RobotState)
├── components.navigation_state.recovery (StuckDetector)
└── picrawler (Picrawler)

manual_control/startup.py
├── components.screens.oled
│   └── components.utils.config
├── components.sensors.battery_status
├── components.sounds.library
└── robot_hat (Music, TTS, Pin)

tracking2.py
└── Same as autonomous_navigator.py
```

---

## Post-Migration Validation

### Checklist:
- [ ] All imports resolve without errors
- [ ] Sensors return valid readings
- [ ] OLED displays correctly
- [ ] Sounds play
- [ ] Robot moves forward/backward smoothly
- [ ] Obstacle avoidance works (front + rear)
- [ ] Floor edge detection works
- [ ] Balance correction works
- [ ] Stuck recovery triggers appropriately
- [ ] Button-based startup works
- [ ] Autonomous navigation runs without crashes

### Validation Script:
```python
#!/usr/bin/env python3
"""
Migration validation script
Run after completing migration to verify all components
"""

def test_imports():
    print("Testing imports...")
    try:
        from components.utils import config
        from components.sensors.sensor_fusion import SensorHub
        from components.navigation import SmoothMotionController
        from components.navigation_state import RobotState
        from components.screens import oled
        from components.sounds import library
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_sensors():
    print("\nTesting sensors...")
    from components.sensors.sensor_fusion import SensorHub
    hub = SensorHub("FRONT_REAR_VL53L0X")
    status = hub.get_sensor_status()
    print(f"  Distance sensor: {status['distance_sensor']}")
    print(f"  Accelerometer: {status['accelerometer']}")
    print(f"  Floor sensors: {status['floor_sensors']}")
    return status['distance_sensor'] == 'available'

def test_display():
    print("\nTesting display...")
    try:
        from components.screens import oled
        oled.update_display("Test", "Validation OK")
        print("✓ OLED working")
        return True
    except Exception as e:
        print(f"✗ OLED failed: {e}")
        return False

def test_navigation():
    print("\nTesting navigation components...")
    from components.navigation import SmoothMotionController
    from components.navigation_state import StuckDetector
    mc = SmoothMotionController()
    detector = StuckDetector()
    print(f"✓ Motion controller initialized (speed: {mc.get_speed()})")
    print(f"✓ Stuck detector initialized")
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("Migration Validation Test")
    print("=" * 50)
    
    results = []
    results.append(test_imports())
    results.append(test_sensors())
    results.append(test_display())
    results.append(test_navigation())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓✓✓ MIGRATION SUCCESSFUL ✓✓✓")
    else:
        print("✗✗✗ MIGRATION INCOMPLETE ✗✗✗")
    print("=" * 50)
```

---

## Next Steps

1. **Review this plan** - Make any adjustments needed
2. **Toggle to Act mode** - When ready to execute
3. **Phase-by-phase migration** - Follow checklist above
4. **Test after each phase** - Verify components work
5. **Integration testing** - Test full autonomous navigation
6. **Iterate** - Fix any issues discovered during testing

---

## Questions to Address

Before starting migration:
1. Do you want ALL diagnostic scripts, or skip them?
2. Should we restore camera components now, or later?
3. Which tracking script do you prefer: tracking2.py, tracking5.py, or tracking6.py?
4. Do you need the web UI (webui.html)?
5. Should we restore ML/data collection infrastructure, or skip for now?

---

**Ready to proceed?** Let me know if you want to adjust this plan, or if you'd like to start the migration!
