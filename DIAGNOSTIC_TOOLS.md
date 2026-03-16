# Diagnostic Tools Inventory - dev Branch

**Branch:** dev (development)  
**Date:** March 17, 2026  
**Purpose:** Complete inventory of diagnostic and testing tools

---

## Overview

The `dev` branch contains **18 development files** (vs 0 in v3.0 production). These tools are essential for hardware testing, debugging, and development but are excluded from production deployment.

**Total Development Overhead:** ~88KB (252KB vs 164KB in self_aware/)

---

## 📋 Existing Diagnostic Tools

### Camera Module (3 files)

**1. `components/camera/camera_diagnostic.py`**
- **Purpose:** Test camera initialization and capture
- **Tests:** Picamera2 setup, image capture, display
- **Usage:** `python3 components/camera/camera_diagnostic.py`
- **Status:** ✅ Available

**2. `components/camera/camera_diagnostic.py.backup`**
- **Purpose:** Backup of working camera diagnostic
- **Status:** 📦 Reference only

**3. `components/camera/INTEGRATION_GUIDE.md`**
- **Purpose:** Camera integration documentation
- **Contains:** Setup instructions, API usage, troubleshooting
- **Status:** 📖 Documentation

---

### Display/OLED Module (5 files)

**4. `components/screens/oled_diagnostic.py`**
- **Purpose:** Test OLED display functionality
- **Tests:** I2C communication, text rendering, icon display
- **Usage:** `python3 components/screens/oled_diagnostic.py`
- **Status:** ✅ Available

**5. `components/screens/oled_diagnostic_v2.py`**
- **Purpose:** Enhanced OLED diagnostic with multiplexer support
- **Tests:** Multiplexed OLED, multiple display modes
- **Usage:** `python3 components/screens/oled_diagnostic_v2.py`
- **Status:** ✅ Available

**6. `components/screens/test_oled_with_mux.py`**
- **Purpose:** Test OLED via PCA9548A multiplexer
- **Tests:** Multiplexer channel switching, display communication
- **Usage:** `python3 components/screens/test_oled_with_mux.py`
- **Status:** ✅ Available

**7. `components/screens/OLED_FIX_GUIDE.md`**
- **Purpose:** OLED troubleshooting guide
- **Contains:** Common issues, I2C conflicts, wiring fixes
- **Status:** 📖 Documentation

**8. `components/screens/OLED_TROUBLESHOOTING.md`**
- **Purpose:** Extended OLED troubleshooting
- **Contains:** Advanced debugging, multiplexer issues
- **Status:** 📖 Documentation

---

### Sensors Module (7 files)

**9. `components/sensors/accel_diagnostic.py`**
- **Purpose:** Test ADXL345 accelerometer
- **Tests:** I2C communication, axis readings, tilt detection
- **Usage:** `python3 components/sensors/accel_diagnostic.py`
- **Status:** ✅ Available

**10. `components/sensors/ir_diagnostic.py`**
- **Purpose:** Test IR floor sensors (4 legs)
- **Tests:** Analog readings, danger thresholds, calibration
- **Usage:** `python3 components/sensors/ir_diagnostic.py`
- **Status:** ✅ Available

**11. `components/sensors/tof_diagnostic.py`**
- **Purpose:** Test VL53L0X ToF distance sensors
- **Tests:** Single sensor initialization, ranging, accuracy
- **Usage:** `python3 components/sensors/tof_diagnostic.py`
- **Status:** ✅ Available

**12. `components/sensors/pca9548a_diagnostic.py`**
- **Purpose:** Test PCA9548A I2C multiplexer
- **Tests:** Channel switching, device detection per channel
- **Usage:** `python3 components/sensors/pca9548a_diagnostic.py`
- **Status:** ✅ Available

**13. `components/sensors/pca9548a_diagnostic_with_data.py`**
- **Purpose:** Enhanced multiplexer diagnostic with data logging
- **Tests:** Channel switching, sensor data collection, timing
- **Usage:** `python3 components/sensors/pca9548a_diagnostic_with_data.py`
- **Status:** ✅ Available

**14. `components/sensors/front_rear_tof_sensor.py.backup`**
- **Purpose:** Backup of dual ToF sensor driver
- **Status:** 📦 Reference only

**15. `components/sensors/sensor_fusion.py.backup`**
- **Purpose:** Backup of unified sensor hub
- **Status:** 📦 Reference only

---

### Autonomous Navigation Module (3 files)

**16. `self_aware/test_logging_paths.py`**
- **Purpose:** Test data logger path resolution
- **Tests:** Log directory creation, file permissions, path handling
- **Usage:** `python3 self_aware/test_logging_paths.py`
- **Status:** ✅ Available

**17. `self_aware/autonomous_navigator.py.backup`**
- **Purpose:** Backup of main autonomous system
- **Status:** 📦 Reference only

**18. `self_aware/data_logger.py.backup`**
- **Purpose:** Backup of data logger
- **Status:** 📦 Reference only

---

## ❌ Missing Diagnostic Tools (Recommendations)

### High Priority

**Battery Monitor Diagnostic**
- **Needed:** Real-time voltage monitoring and logging
- **Purpose:** Test battery status, low voltage alerts
- **Suggested file:** `components/sensors/battery_diagnostic.py`

**Motion Controller Test**
- **Needed:** Test smooth motion transitions and ramping
- **Purpose:** Verify speed changes, pose transitions
- **Suggested file:** `components/navigation/motion_diagnostic.py`

**Obstacle Handler Test**
- **Needed:** Simulated obstacle scenarios
- **Purpose:** Test avoidance logic, decision making
- **Suggested file:** `components/navigation/obstacle_test.py`

**Sensor Fusion Test**
- **Needed:** Comprehensive multi-sensor test
- **Purpose:** Test all sensors simultaneously, detect conflicts
- **Suggested file:** `components/sensors/sensor_fusion_test.py`

### Medium Priority

**Balance Diagnostic**
- **Needed:** Test balance pose calculation
- **Purpose:** Verify tilt compensation, dynamic poses
- **Suggested file:** `components/navigation/balance_test.py`

**Stuck Detection Test**
- **Needed:** Simulate stuck conditions
- **Purpose:** Test recovery patterns, escalation logic
- **Suggested file:** `components/navigation_state/recovery_test.py`

**Sound System Test**
- **Needed:** Test audio playback and TTS
- **Purpose:** Verify sound effects, voice announcements
- **Suggested file:** `components/sounds/audio_diagnostic.py`

### Low Priority

**PS4 Controller Test**
- **Needed:** Test PS4 controller pairing and input
- **Purpose:** Verify button mapping, joystick calibration
- **Suggested file:** `components/sensors/ps4_diagnostic.py`

**Web Server Test**
- **Needed:** Test Flask REST API endpoints
- **Purpose:** Verify remote control, status reporting
- **Suggested file:** `components/server/api_test.py`

---

## 🔧 Usage Patterns

### Quick Hardware Check
```bash
# Test all I2C devices
python3 components/sensors/pca9548a_diagnostic.py

# Test specific sensor
python3 components/sensors/accel_diagnostic.py
python3 components/sensors/tof_diagnostic.py
python3 components/sensors/ir_diagnostic.py
```

### Display Testing
```bash
# Basic OLED test
python3 components/screens/oled_diagnostic.py

# Multiplexed OLED test
python3 components/screens/test_oled_with_mux.py
```

### Data Collection
```bash
# Test logging paths
python3 self_aware/test_logging_paths.py

# Enhanced multiplexer with data
python3 components/sensors/pca9548a_diagnostic_with_data.py
```

---

## 📊 File Categories

### Active Tools (11 files)
Tools you can run directly for testing:
- 5x Sensor diagnostics
- 3x Display diagnostics  
- 1x Multiplexer diagnostic
- 1x Camera diagnostic
- 1x Logging test

### Documentation (3 files)
Reference guides:
- 2x OLED troubleshooting guides
- 1x Camera integration guide

### Backups (4 files)
Reference backups of production code:
- 2x Sensor backups
- 2x Self-aware backups

---

## 🎯 Development Workflow

1. **Before Hardware Changes**
   ```bash
   # Run relevant diagnostic to establish baseline
   python3 components/sensors/[sensor]_diagnostic.py
   ```

2. **After Code Updates**
   ```bash
   # Test updated component
   python3 components/[module]/[component]_diagnostic.py
   ```

3. **Before Production Migration**
   ```bash
   # Verify all systems work
   python3 tools/pass_to_prod.py --dry-run
   ```

---

## 📝 Creating New Diagnostics

### Template Structure
```python
#!/usr/bin/env python3
"""
Diagnostic tool for [Component Name]
Tests: [list what it tests]
Usage: python3 path/to/diagnostic.py
"""

import time
from [module] import [Component]

def test_initialization():
    """Test component initialization"""
    print("Testing initialization...")
    # Test code here
    
def test_basic_operation():
    """Test basic operation"""
    print("Testing basic operation...")
    # Test code here

def test_edge_cases():
    """Test edge cases and error handling"""
    print("Testing edge cases...")
    # Test code here

if __name__ == "__main__":
    print("=" * 60)
    print("[Component] Diagnostic Test")
    print("=" * 60)
    
    test_initialization()
    test_basic_operation()
    test_edge_cases()
    
    print("\n✅ All tests completed!")
```

---

## 🚀 Quick Reference

| Component | Diagnostic Tool | Tests |
|-----------|----------------|-------|
| Accelerometer | `accel_diagnostic.py` | I2C, axes, tilt |
| IR Sensors | `ir_diagnostic.py` | 4 legs, thresholds |
| ToF Sensors | `tof_diagnostic.py` | Distance, ranging |
| Multiplexer | `pca9548a_diagnostic.py` | Channels, devices |
| OLED Display | `oled_diagnostic.py` | I2C, text, icons |
| Camera | `camera_diagnostic.py` | Init, capture |
| Data Logger | `test_logging_paths.py` | Paths, permissions |

---

**Last Updated:** March 17, 2026  
**Branch:** dev  
**Status:** Active development environment
