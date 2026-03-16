# Migration Guide: v3.0 → v4.0 (Future)

**Purpose:** Template for migrating custom modules to future factory updates  
**Created:** March 17, 2026  
**Current Version:** v3.0 (Production)

---

## Overview

This guide provides a step-by-step process for migrating your custom modules (`components/`, `manual_control/`, `self_aware/`) to a future factory update (v4.0).

**Key Principle:** Your custom modules are **isolated** from the factory `picrawler/` core, making migration straightforward.

---

## Pre-Migration Checklist

### ✅ Before Starting

1. **Backup Current Working System**
   ```bash
   # On Raspberry Pi
   cd ~
   tar -czf picrawler_v3.0_backup_$(date +%Y%m%d).tar.gz picrawler/
   
   # Verify backup
   ls -lh picrawler_v3.0_backup_*.tar.gz
   ```

2. **Document Your Configuration**
   - Note any custom settings in `components/utils/config.py`
   - List any hardware modifications
   - Document working scripts and their purposes

3. **Test Current System**
   ```bash
   # Verify everything works before migration
   python3 self_aware/autonomous_navigator.py  # Test for 1 minute
   python3 manual_control/startup.py  # Test button controls
   ```

4. **Save Custom Scripts**
   ```bash
   # If you've created additional scripts outside the modules
   cp -r ~/custom_scripts ~/custom_scripts_backup
   ```

---

## Migration Process

### Step 1: Create v4.0 Branch

```bash
cd ~/picrawler
git fetch origin
git checkout -b v4.0 origin/v4.0  # When v4.0 is released
```

### Step 2: Backup Your Modules

```bash
# Save v3.0 modules to temporary location
mkdir -p ~/v3_modules_backup
cp -r components ~/v3_modules_backup/
cp -r manual_control ~/v3_modules_backup/
cp -r self_aware ~/v3_modules_backup/
```

### Step 3: Restore Custom Modules to v4.0

```bash
# Copy modules to new v4.0 branch
cp -r ~/v3_modules_backup/components ./
cp -r ~/v3_modules_backup/manual_control ./
cp -r ~/v3_modules_backup/self_aware ./
```

### Step 4: Check for Breaking Changes

**Review v4.0 changelog for:**
- Changes to `robot_hat` API
- Changes to `picrawler` core methods
- New dependencies or requirements
- Deprecated functions

**Common areas to check:**
```bash
# Check if these imports still work
python3 -c "from picrawler import Picrawler; print('Core OK')"
python3 -c "from robot_hat import Pin, Music, TTS; print('HAT OK')"
python3 -c "from components.sensors.sensor_fusion import SensorHub; print('Sensors OK')"
```

### Step 5: Update Dependencies (if needed)

```bash
# If v4.0 requires new packages
pip3 install -r requirements.txt  # If provided

# Or manually install known dependencies
pip3 install robot_hat picrawler picamera2 smbus2 Pillow pygame
```

### Step 6: Test Each Module

**Test Order:**

1. **Sensors**
   ```bash
   python3 -c "from components.sensors.sensor_fusion import SensorHub; hub = SensorHub('FRONT_REAR_VL53L0X'); print(hub.get_sensor_status())"
   ```

2. **Navigation**
   ```bash
   python3 -c "from components.navigation import SmoothMotionController; mc = SmoothMotionController(); print('Navigation OK')"
   ```

3. **Display**
   ```bash
   python3 -c "from components.screens import oled; oled.update_display('Test', 'Migration Check'); print('OLED OK')"
   ```

4. **Autonomous Navigator**
   ```bash
   # Run for 30 seconds to verify
   python3 self_aware/autonomous_navigator.py
   ```

### Step 7: Fix Compatibility Issues (if any)

**If imports fail:**
```bash
# Check what changed in v4.0
git diff v3.0..v4.0 picrawler/

# Update your code accordingly
# Common fixes:
# - Update method names
# - Adjust parameter orders
# - Update deprecated functions
```

**Example compatibility fix:**
```python
# If v4.0 changes Picrawler.do_action() signature:

# Old (v3.0):
robot.do_action('forward', 1, 50)

# New (v4.0) - hypothetical:
robot.do_action('forward', speed=50, duration=1)

# Update in: components/navigation/motion_controller.py
```

### Step 8: Clean Up

```bash
# Remove v3.0 backup after successful migration
rm -rf ~/v3_modules_backup

# Remove old logs
rm -f self_aware/logs/*.csv
```

### Step 9: Commit Changes

```bash
git add components/ manual_control/ self_aware/
git commit -m "Migrated custom modules from v3.0 to v4.0"
git push origin v4.0
```

---

## Troubleshooting

### Issue: Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'components'`

**Solution:**
```bash
# Run from project root
cd ~/picrawler
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Sensor Not Responding

**Symptom:** Sensors timeout or return 999

**Solution:**
```bash
# Check I2C devices
i2cdetect -y 1

# Verify multiplexer (0x70) and OLED (0x3c) are detected
# If not, check wiring and power
```

### Issue: Method Not Found

**Symptom:** `AttributeError: 'Picrawler' object has no attribute 'do_action'`

**Solution:**
- Check v4.0 API documentation
- Update method calls to new API
- Search for all occurrences: `grep -r "do_action" components/ manual_control/ self_aware/`

### Issue: Configuration Mismatch

**Symptom:** Robot behaves differently than v3.0

**Solution:**
```bash
# Verify config matches v3.0
diff ~/v3_modules_backup/components/utils/config.py components/utils/config.py

# Restore your settings if needed
```

---

## Rollback Procedure

If migration fails, rollback to v3.0:

```bash
# 1. Switch back to v3.0
cd ~/picrawler
git checkout v3.0

# 2. Restore from backup (if needed)
cd ~
tar -xzf picrawler_v3.0_backup_YYYYMMDD.tar.gz

# 3. Verify system works
cd picrawler
python3 self_aware/autonomous_navigator.py
```

---

## Module-Specific Migration Notes

### Components Module

**What might change in v4.0:**
- `robot_hat` API (Pin, Motor, Servo methods)
- I2C communication protocols
- Sensor initialization sequences

**Files most likely to need updates:**
- `components/sensors/sensor_fusion.py`
- `components/navigation/motion_controller.py`
- `components/screens/oled.py`

### Manual Control Module

**What might change in v4.0:**
- Button pin assignments
- Keyboard input handling
- Web server frameworks

**Files most likely to need updates:**
- `manual_control/startup.py` (button pins)
- `manual_control/scripts/restapi3.py` (Flask API)

### Self-Aware Module

**What might change in v4.0:**
- Picrawler movement methods
- Timing/delays for hardware responses
- State machine logic (unlikely)

**Files most likely to need updates:**
- `self_aware/autonomous_navigator.py` (Picrawler API calls)

---

## Testing Checklist

After migration, verify these functions:

- [ ] Robot moves forward/backward/left/right
- [ ] Front ToF sensor detects obstacles
- [ ] Rear ToF sensor detects obstacles
- [ ] Floor IR sensors detect edges
- [ ] Accelerometer reports tilt correctly
- [ ] OLED displays messages
- [ ] Sounds play correctly
- [ ] TTS announces events
- [ ] Obstacle avoidance works
- [ ] Floor danger avoidance works
- [ ] Balance correction activates
- [ ] Stuck detection triggers
- [ ] Button controls work (USR/RST)
- [ ] Autonomous navigation runs smoothly
- [ ] Data logging saves correctly

---

## Best Practices

1. **Read v4.0 Release Notes**
   - Check for breaking changes
   - Review new features that might improve your modules

2. **Test Incrementally**
   - Don't migrate everything at once
   - Test sensors first, then navigation, then autonomy

3. **Keep v3.0 Working**
   - Don't delete v3.0 backup until v4.0 is stable
   - Run both versions in parallel during transition

4. **Document Changes**
   - Keep notes on what you had to update
   - Share findings with community if helpful

5. **Version Control**
   - Commit frequently during migration
   - Tag working milestones: `git tag v4.0-sensors-working`

---

## Quick Migration Commands

For experienced users, the minimal migration:

```bash
# Backup
tar -czf picrawler_v3_$(date +%Y%m%d).tar.gz picrawler/

# Switch to v4.0
cd ~/picrawler
git fetch origin
git checkout v4.0

# Copy modules
git checkout v3.0 -- components/ manual_control/ self_aware/

# Test
python3 -c "from components.sensors.sensor_fusion import SensorHub; print('OK')"
python3 self_aware/autonomous_navigator.py

# Commit if successful
git add components/ manual_control/ self_aware/
git commit -m "Migrated custom modules from v3.0"
```

---

## Support Resources

- **Module Manifest:** See `CUSTOM_MODULES_MANIFEST.md` for file inventory
- **v3.0 Configuration:** Reference `components/utils/config.py`
- **Hardware Setup:** Check v3.0 `MIGRATION_PLAN_V2_TO_V3.md` for details

---

## Future-Proofing Tips

To make future migrations even easier:

1. **Keep Modules Self-Contained**
   - Minimize dependencies on factory code
   - Use abstraction layers

2. **Centralize Configuration**
   - All settings in `components/utils/config.py`
   - No hardcoded values in multiple files

3. **Document Custom Changes**
   - Add comments explaining why code is structured a certain way
   - Note any factory API dependencies

4. **Version Your Configurations**
   - Keep `config.py` changes documented
   - Track hardware setup changes

---

**Last Updated:** March 17, 2026  
**For:** v3.0 → v4.0 migration  
**Author:** Automated packaging system
