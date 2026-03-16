# Production Setup Guide - v3.0

**Version:** 3.0 (Production)  
**Date:** March 17, 2026  
**Status:** ✅ Ready for Raspberry Pi deployment

---

## What is v3.0?

v3.0 is the **production-ready** version of your Picrawler robot software, combining:
- **Factory core** (`picrawler/`) - Official Picrawler library (maintained by manufacturer)
- **Custom modules** (`components/`, `manual_control/`, `self_aware/`) - Your enhanced features

**Successfully migrated from:** v2.0 development branch  
**Total custom code:** ~3.5MB (62 Python files)  
**Cleanup:** Removed 27 development files (diagnostics, tests, backups)

---

## Quick Start

### On Raspberry Pi

1. **Clone or pull latest v3.0**
   ```bash
   cd ~
   git clone https://github.com/oetapia/picrawler.git
   cd picrawler
   git checkout v3.0
   ```

2. **Install dependencies** (if needed)
   ```bash
   pip3 install robot_hat picamera2 smbus2 Pillow pygame
   ```

3. **Run autonomous navigation**
   ```bash
   python3 self_aware/autonomous_navigator.py
   ```

4. **Or use button-based startup**
   ```bash
   python3 manual_control/startup.py
   # Press USR button → Keyboard control
   # Press RST button → Autonomous tracking
   ```

---

## What's Included

### ✅ Factory Components (Unchanged)
- `picrawler/` - Core robot control library
- `examples/` - Factory example scripts
- Standard audio files and configuration

### ✅ Custom Modules (Your Code)

**1. Components** (3.2MB)
- Sensors: Battery, IR floor, accelerometer, dual ToF, multiplexer
- Navigation: Motion control, obstacle avoidance, balance
- Display: OLED interface with icons
- Audio: Sound effects and TTS
- Camera: Basic camera interface

**2. Manual Control** (184KB)
- Button-based launcher
- Keyboard control
- Multiple tracking scripts
- REST API (optional)

**3. Self-Aware** (164KB)
- Autonomous navigation system
- Data logging capabilities
- ML infrastructure (future)

---

## Hardware Configuration

**Your Setup:**
```
Robot HAT
├── PCA9548A Multiplexer (0x70)
│   ├── Channel 0: VL53L0X ToF (Front)
│   ├── Channel 1: VL53L0X ToF (Rear)
│   └── Channel 2: ADXL345 Accelerometer
├── SSD1306 OLED (0x3C) - Direct connection
└── IR Floor Sensors x4 (FL, FR, BL, BR)
```

**Configuration file:** `components/utils/config.py`
```python
DISTANCE_SENSOR_TYPE = "FRONT_REAR_VL53L0X"
```

---

## Main Entry Points

### 🤖 Autonomous Navigation (Recommended)
```bash
python3 self_aware/autonomous_navigator.py
```
- Full autonomous exploration
- Multi-sensor obstacle avoidance
- Balance correction
- Stuck recovery
- TTS announcements

### 📊 Autonomous with Logging
```bash
python3 self_aware/autonomous_navigator_with_logging.py
```
- Same as above + sensor data logging
- Logs saved to `self_aware/logs/`

### 🎮 Manual Tracking
```bash
python3 manual_control/scripts/tracking2.py
```
- Manual control with obstacle avoidance
- Best for testing and debugging

### 🔘 Button Launcher
```bash
python3 manual_control/startup.py
```
- USR button → Keyboard control
- RST button → Autonomous tracking
- Perfect for headless operation

---

## File Structure

```
picrawler/
├── components/              # Hardware interface layer
│   ├── sensors/            # All sensor drivers
│   ├── navigation/         # Motion & obstacle handling
│   ├── navigation_state/   # State machine
│   ├── screens/            # OLED display
│   ├── sounds/             # Audio & TTS
│   ├── utils/              # Config & utilities
│   └── camera/             # Camera interface
├── manual_control/          # Manual operation
│   ├── startup.py          # Button launcher
│   ├── scripts/            # Control scripts
│   └── client/             # Web UI (optional)
├── self_aware/              # Autonomous navigation
│   ├── autonomous_navigator.py
│   ├── data_logger.py
│   └── logs/               # Data logs
├── picrawler/               # Factory core (DO NOT MODIFY)
│   ├── __init__.py
│   ├── picrawler.py
│   └── version.py
├── examples/                # Factory examples
└── README.md                # Main documentation
```

---

## Key Features

### Multi-Sensor Obstacle Avoidance
- Front ToF sensor (0-200cm range)
- Rear ToF sensor (0-200cm range)
- Floor IR sensors (4 legs)
- Smooth transitions and speed ramping

### Balance Correction
- Accelerometer monitoring
- Dynamic pose adjustment
- Tilt compensation

### Stuck Detection
- Consecutive obstacle/floor danger tracking
- Escalating escape patterns
- Automatic recovery

### State Machine
- EXPLORING (normal operation)
- AVOIDING_OBSTACLE
- AVOIDING_FLOOR_DANGER
- TILT_CORRECTION
- STUCK
- EMERGENCY

---

## Troubleshooting

### Import Errors
```bash
# Run from project root
cd ~/picrawler
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Sensors Not Responding
```bash
# Check I2C devices
i2cdetect -y 1

# Should see:
# 0x70 - Multiplexer
# 0x3c - OLED
```

### OLED Not Working
- Verify direct connection (not on multiplexer)
- Use `oled.py` (not `oled_mux.py`)
- Check I2C address (usually 0x3C)

### No Sound
```bash
# Test audio system
aplay /usr/share/sounds/alsa/Front_Center.wav

# Check volume
alsamixer
```

---

## Development vs Production

**v2.0 (Development):**
- Contains diagnostic scripts
- Test files present
- Backup files included
- Verbose documentation
- ~4MB total

**v3.0 (Production):** ⭐
- Cleaned and optimized
- Only production files
- Lean and efficient
- ~3.5MB total
- Ready for deployment

---

## Upgrading to v4.0 (Future)

When v4.0 factory update is released:

1. See `V4_MIGRATION_GUIDE.md` for detailed instructions
2. Your custom modules are isolated and easy to migrate
3. Simple 3-step process:
   - Backup v3.0 modules
   - Switch to v4.0 branch
   - Restore custom modules

---

## Support Documents

- **CUSTOM_MODULES_MANIFEST.md** - Complete file inventory
- **V4_MIGRATION_GUIDE.md** - Future migration instructions
- **README.md** - Main project documentation

---

## Testing Checklist

Before deployment, verify:

- [ ] Robot moves in all directions
- [ ] Front/rear ToF sensors detect obstacles
- [ ] Floor sensors detect edges
- [ ] Accelerometer reports tilt
- [ ] OLED displays messages
- [ ] Sounds play correctly
- [ ] TTS works
- [ ] Autonomous navigation runs smoothly
- [ ] Obstacle avoidance functions
- [ ] Stuck recovery activates

---

## Deployment Tips

1. **Test on blocks first**
   - Verify all sensors before floor testing
   - Check motor directions
   - Confirm obstacle detection ranges

2. **Start with short sessions**
   - Run 1-2 minutes initially
   - Gradually increase duration
   - Monitor for issues

3. **Use logging mode**
   - Collect data for analysis
   - Review logs to understand behavior
   - Optimize settings based on data

4. **Keep v2.0 as backup**
   - Don't delete development branch
   - Useful for comparing behavior
   - Contains diagnostic tools if needed

---

## Version History

- **v3.0** (March 2026) - Production release
  - Migrated from v2.0
  - Removed 27 development files
  - Added packaging documentation
  - Ready for Raspberry Pi deployment

- **v2.0** (March 2026) - Development branch
  - Full feature set
  - Diagnostic tools included
  - Development documentation

---

**Status:** ✅ Production Ready  
**Last Updated:** March 17, 2026  
**Branch:** v3.0
