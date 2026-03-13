# OLED Not Detected - Issue & Solution

## Problem Summary

Your OLED screen is **connected to the PCA9548A multiplexer** (on one of the 8 channels), but your original `oled.py` module was trying to access it **directly on the main I2C bus** without selecting the multiplexer channel first.

### Why Other Sensors Work

- ✅ **VL53L0X ToF sensors** (2x) - Detected because they're properly accessed through multiplexer channels
- ✅ **MPU6050 accelerometer** - Detected (likely on main bus or properly configured)
- ❌ **OLED screen** - NOT detected because `oled.py` doesn't select the multiplexer channel

## Root Cause

Your `components/screens/oled.py` file has this initialization:

```python
def initialize_display():
    global display
    # Initialize I2C with default pins
    i2c = busio.I2C(board.SCL, board.SDA)  # ❌ Accesses main bus only!
    
    # Scan for I2C devices
    devices = i2c.scan()
    print('I2C devices found:', devices)
    
    # Try to initialize the OLED display
    display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)  # ❌ Won't see OLED behind mux!
```

**The problem:** This code only scans the main I2C bus. The OLED is on a multiplexer channel, so it's invisible without first selecting that channel.

## The Solution

I've created a new module `components/screens/oled_mux.py` that:

1. ✅ Imports the PCA9548A multiplexer controller
2. ✅ Auto-detects which channel the OLED is on (or accepts manual channel specification)
3. ✅ Selects the correct multiplexer channel before accessing the OLED
4. ✅ Maintains the channel selection for all subsequent operations
5. ✅ Properly cleans up resources when done

### Key Features

```python
# Auto-detect OLED channel
initialize_display(use_multiplexer=True, channel=None)

# Or specify the channel if you know it
initialize_display(use_multiplexer=True, channel=2)

# Automatically maintains channel selection
update_display(header="Status", text="Working!")

# Proper cleanup
close_display()
```

## How to Fix Your Code

### Option 1: Quick Test (Recommended First)

Run the diagnostic to see which channel your OLED is on:

```bash
cd /Users/tapiapil/dev2/picrawler
python3 components/sensors/pca9548a_diagnostic.py
```

This will show you something like:
```
>> Channel 2 (SD2):
   Found 1 device(s):
     [0x3C]  SSD1306 OLED Display (128x64)
```

Then test the new OLED module:

```bash
python3 test_oled_with_mux.py
```

### Option 2: Update Your Existing Code

Replace your OLED imports and initialization:

**Before (in your code):**
```python
from components.screens import oled

# Initialize
oled.initialize_display()  # ❌ Won't find OLED behind mux

# Update display
oled.update_display(header="Status", text="Running")
```

**After (updated):**
```python
from components.screens import oled_mux

# Initialize with auto-detection
oled_mux.initialize_display(use_multiplexer=True, channel=None)

# Update display (same API!)
oled_mux.update_display(header="Status", text="Running")

# Clean up when done
oled_mux.close_display()
```

### Option 3: Fix the Original oled.py

If you want to fix the original `oled.py` file instead, you can add multiplexer support to it. The key changes needed are:

1. Import the multiplexer controller
2. Select the channel before initialization
3. Keep the channel selected for all operations

## Testing Steps

### Step 1: Run Multiplexer Diagnostic
```bash
python3 components/sensors/pca9548a_diagnostic.py
```

**Expected output:**
```
[3] Scanning multiplexer channels...
  >> Channel 0 (SD0):
     Found 1 device(s):
       [0x29]  VL53L0X/VL53L1X ToF Sensor - VL53L0X (ID: 0xEE) [OK]

  >> Channel 1 (SD1):
     Found 1 device(s):
       [0x29]  VL53L0X/VL53L1X ToF Sensor - VL53L0X (ID: 0xEE) [OK]

  >> Channel 2 (SD2):  ← YOUR OLED IS HERE!
     Found 1 device(s):
       [0x3C]  SSD1306 OLED Display (128x64)
```

### Step 2: Test New OLED Module
```bash
python3 test_oled_with_mux.py
```

**Expected output:**
```
[TEST 1] Auto-detecting OLED on multiplexer channels...
Initializing OLED through multiplexer at 0x70...
  [OK] Multiplexer initialized
  Scanning multiplexer channels for OLED...
  [OK] OLED found on channel 2
  [OK] Selected multiplexer channel 2
  Initializing I2C connection...
  Scanning I2C bus...
  I2C devices found: ['0x3c']
  Initializing OLED at 0x3C...
  [OK] OLED initialized (128x64)
[OK] OLED display initialized successfully!
     - Through multiplexer channel 2

[SUCCESS] OLED initialized successfully!
```

### Step 3: Update Your Application Code

Find where you use `oled.py` in your application and update the import:

```bash
# Find all files that import oled
grep -r "from components.screens import oled" .
grep -r "import components.screens.oled" .
```

Then update each file to use `oled_mux` instead.

## Technical Explanation

### How the Multiplexer Works

The PCA9548A multiplexer acts like a switch:

```
Main I2C Bus (Pi GPIO 2/3)
    ↓
PCA9548A (0x70) ← Multiplexer switch
    ├─ Channel 0 (SD0) → VL53L0X sensor #1 (0x29)
    ├─ Channel 1 (SD1) → VL53L0X sensor #2 (0x29)
    ├─ Channel 2 (SD2) → OLED display (0x3C)
    ├─ Channel 3 (SD3) → (empty)
    ├─ Channel 4 (SD4) → (empty)
    ├─ Channel 5 (SD5) → (empty)
    ├─ Channel 6 (SD6) → (empty)
    └─ Channel 7 (SD7) → (empty)
```

To access a device behind the multiplexer:

1. Write control byte to multiplexer (e.g., `0x04` for channel 2)
2. Now I2C bus "sees" only devices on that channel
3. Access your device normally
4. Optionally disable channel when done (`0x00`)

### Why Your Original Code Failed

```python
# This code only sees the multiplexer itself (0x70)
# It does NOT see devices behind the multiplexer channels!
i2c = busio.I2C(board.SCL, board.SDA)
devices = i2c.scan()  # Returns: [0x68, 0x70]  ← No 0x3C!
```

To see the OLED, you must:

```python
# 1. Select multiplexer channel first
bus = smbus.SMBus(1)
bus.write_byte(0x70, 0x04)  # Enable channel 2

# 2. NOW the I2C bus sees the OLED
i2c = busio.I2C(board.SCL, board.SDA)
devices = i2c.scan()  # Returns: [0x3C, 0x68, 0x70]  ← OLED found!
```

## Comparison: Old vs New

| Feature | Original oled.py | New oled_mux.py |
|---------|-----------------|-----------------|
| Multiplexer support | ❌ No | ✅ Yes |
| Auto-detect channel | ❌ No | ✅ Yes |
| Manual channel selection | ❌ No | ✅ Yes |
| Maintains channel state | ❌ No | ✅ Yes |
| Resource cleanup | ⚠️ Partial | ✅ Complete |
| Works on main bus | ✅ Yes | ✅ Yes (use_multiplexer=False) |
| Works through mux | ❌ No | ✅ Yes |

## Common Issues & Solutions

### Issue 1: "Multiplexer not found"
```python
IOError: PCA9548A not found at address 0x70
```

**Solution:** Check multiplexer address
```bash
i2cdetect -y 1
# Look for 70-77 range
```

### Issue 2: "OLED not found on any channel"
```
[X] OLED not found on any multiplexer channel!
```

**Solutions:**
1. Check OLED wiring (VCC, GND, SDA, SCL)
2. Try OLED address 0x3D instead of 0x3C
3. Verify OLED works with diagnostic: `python3 components/screens/oled_diagnostic_v2.py`

### Issue 3: Multiple Devices Need Different Channels

If you need to use OLED and sensors together:

```python
from components.sensors.pca9548a_mux import PCA9548A
from components.screens import oled_mux

# Initialize multiplexer
mux = PCA9548A()

# Use ToF sensor on channel 0
mux.select_channel(0)
distance1 = tof_sensor1.read()

# Use ToF sensor on channel 1
mux.select_channel(1)
distance2 = tof_sensor2.read()

# Use OLED on channel 2 (oled_mux handles this automatically)
oled_mux.update_display(
    header="Distances",
    text=f"L:{distance1} R:{distance2}"
)
```

## Files Created

1. **`components/screens/oled_mux.py`** - New OLED module with multiplexer support
2. **`test_oled_with_mux.py`** - Test script to verify OLED works
3. **`OLED_FIX_GUIDE.md`** - This guide (documentation)

## Quick Reference

### Initialize OLED
```python
from components.screens import oled_mux

# Auto-detect channel
oled_mux.initialize_display(use_multiplexer=True)

# Or specify channel
oled_mux.initialize_display(use_multiplexer=True, channel=2)

# Without multiplexer (direct connection)
oled_mux.initialize_display(use_multiplexer=False)
```

### Update Display
```python
# Simple text
oled_mux.update_display(header="Status", text="Running")

# With custom layout
oled_mux.update_display(
    header="Sensors",
    text="ToF: 25cm Accel: OK",
    y_start=12,
    line_height=10
)

# With icon
oled_mux.update_display(
    header="System",
    text="Ready",
    icon='rectangle'
)
```

### Cleanup
```python
# Always cleanup when done
oled_mux.close_display()
```

## Next Steps

1. ✅ Run `python3 components/sensors/pca9548a_diagnostic.py` to confirm your setup
2. ✅ Run `python3 test_oled_with_mux.py` to test the new OLED module
3. ✅ Update your application code to use `oled_mux` instead of `oled`
4. ✅ Test your full application

## Need Help?

- Check `components/screens/OLED_TROUBLESHOOTING.md` for detailed OLED diagnostics
- Check `components/sensors/README_MULTIPLEXER.md` for multiplexer documentation
- Run diagnostics to verify hardware: `python3 components/sensors/pca9548a_diagnostic.py`

---

**Created:** March 13, 2026  
**Issue:** OLED not detected by multiplexer diagnostic  
**Solution:** Use `oled_mux.py` with multiplexer channel selection
