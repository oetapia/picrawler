# OLED Display Troubleshooting Guide

## Problem: OLED Not Detected by Diagnostic Tool

### Root Cause Analysis

The original OLED diagnostic (`oled_diagnostic.py`) had several issues that prevented reliable detection:

1. **I2C Bus Contention**: Created multiple `busio.I2C()` instances without proper cleanup
2. **Mixed Library Usage**: Used both `smbus` and `busio` libraries simultaneously, causing conflicts
3. **No Resource Management**: Failed to properly close/deinitialize I2C connections
4. **Bus Lockup**: No mechanism to recover from I2C bus lockup situations

**Why MPU6050 and ToF Sensors Work:**
- These diagnostics use a single I2C library consistently (`smbus`)
- They properly close bus connections after each test
- They don't create multiple I2C instances simultaneously

## Solution: Improved Diagnostic Tool

### New Tool: `oled_diagnostic_v2.py`

**Key Improvements:**
- ✅ Proper I2C resource management and cleanup
- ✅ Single I2C connection strategy (no conflicts)
- ✅ I2C bus reset capability for recovery
- ✅ Better error handling and detailed diagnostics
- ✅ Tests all common configurations automatically

### Usage

```bash
# Run the improved diagnostic
cd /Users/tapiapil/dev2/picrawler
python3 components/screens/oled_diagnostic_v2.py
```

### What the Tool Does

1. **Pre-Test**: Simple I2C device detection
   - Scans for devices at common OLED addresses (0x3C, 0x3D)
   - If none found, attempts I2C bus reset

2. **Main Test**: Tests all common configurations
   - Address 0x3C with 128x64 resolution (most common)
   - Address 0x3C with 128x32 resolution
   - Address 0x3D with 128x64 resolution
   - Address 0x3D with 128x32 resolution

3. **Alternative Test**: Through multiplexer (if main test fails)
   - Scans all 8 channels of PCA9548A
   - Tests each channel for OLED presence

## Common Issues and Solutions

### Issue 1: No Device at OLED Address

**Symptoms:**
```
[X] No device responding at typical OLED addresses (0x3C, 0x3D)
```

**Solutions:**

1. **Check Wiring**
   ```
   OLED Pin    →  Raspberry Pi
   ─────────────────────────────
   VCC         →  3.3V (Pin 1)
   GND         →  GND (Pin 6)
   SDA         →  GPIO 2 (Pin 3)
   SCL         →  GPIO 3 (Pin 5)
   ```

2. **Verify I2C is Enabled**
   ```bash
   # Check if I2C is enabled
   sudo raspi-config
   # Navigate to: Interface Options → I2C → Enable
   ```

3. **Check I2C Bus**
   ```bash
   # Scan I2C bus manually
   i2cdetect -y 1
   
   # You should see something like:
   #      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
   # 00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
   # 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
   # 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
   # 30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- -- 
   # 40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
   # ...
   ```

### Issue 2: Device Found But Initialization Fails

**Symptoms:**
```
[OK] Device(s) responding at OLED address(es): ['0x3c']
[X] Error: [Errno 121] Remote I/O error
```

**Solutions:**

1. **I2C Bus Speed Issue**
   
   Some OLED displays can't handle the default I2C speed. Slow it down:
   
   ```bash
   # Edit boot config
   sudo nano /boot/config.txt
   
   # Add this line (or modify if exists):
   dtparam=i2c_arm_baudrate=50000
   
   # Save and reboot
   sudo reboot
   ```

2. **Power Supply Issue**
   
   ```bash
   # Check if your OLED needs 5V instead of 3.3V
   # Some larger OLEDs require 5V power
   # Connect VCC to Pin 2 (5V) instead of Pin 1 (3.3V)
   # BUT: Keep SDA/SCL on 3.3V logic level!
   ```

3. **Pull-up Resistors**
   
   Most Raspberry Pis have built-in pull-ups, but some OLEDs need external ones:
   ```
   - Add 4.7kΩ resistors between SDA and 3.3V
   - Add 4.7kΩ resistors between SCL and 3.3V
   ```

### Issue 3: Wrong Resolution or Address

**Symptoms:**
```
[X] Failed to initialize OLED at 0x3c
```

**Solutions:**

The diagnostic tests all combinations automatically, but if you need to check manually:

1. **Check OLED Module Documentation**
   - Most are 128x64 at 0x3C
   - Some are 128x32 at 0x3C
   - Few use 0x3D address

2. **Address Solder Jumper**
   
   Some OLED modules have a solder jumper to change address:
   - Default: 0x3C (jumper open)
   - Alternative: 0x3D (jumper closed)
   - Check the back of your OLED module

### Issue 4: I2C Bus Lockup

**Symptoms:**
```
[X] Could not acquire I2C lock
```

**Solutions:**

1. **Use Built-in Reset**
   
   The V2 diagnostic includes automatic I2C reset:
   ```python
   # The tool will try this automatically
   reset_i2c_bus()
   ```

2. **Manual Reset**
   ```bash
   # Reset I2C bus manually
   sudo rmmod i2c_bcm2835
   sudo modprobe i2c_bcm2835
   ```

3. **Reboot**
   ```bash
   sudo reboot
   ```

### Issue 5: OLED Behind Multiplexer

**Symptoms:**
```
[X] OLED NOT DETECTED on main bus
[OK] OLED working through MULTIPLEXER on channel X
```

**Solutions:**

Update your code to use multiplexer channel selection:

```python
import smbus

# Initialize
bus = smbus.SMBus(1)
MUX_ADDR = 0x70
CHANNEL = X  # Replace with detected channel number

# Select channel
bus.write_byte(MUX_ADDR, 1 << CHANNEL)

# Now initialize OLED as normal
import board
import busio
import adafruit_ssd1306

i2c = busio.I2C(board.SCL, board.SDA)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

# Don't forget to disable channel when done
bus.write_byte(MUX_ADDR, 0x00)
bus.close()
```

## Hardware Compatibility

### Verified Compatible OLEDs
- SSD1306 128x64 OLED (most common)
- SSD1306 128x32 OLED
- 0.96" I2C OLED displays
- 1.3" I2C OLED displays (SH1106 - needs different driver)

### Known Issues
- **SH1106 displays**: Need `adafruit-circuitpython-sh1106` instead
- **SPI OLEDs**: This diagnostic is for I2C only
- **0.91" displays**: Usually work but might need 5V power

## Testing Workflow

### Step 1: Basic Hardware Check
```bash
# Verify I2C devices are detected
i2cdetect -y 1

# Should show:
# - 0x3C or 0x3D (OLED)
# - 0x29 (ToF sensors if connected)
# - 0x68 (MPU6050 if connected)
# - 0x70 (Multiplexer if connected)
```

### Step 2: Run Diagnostic
```bash
python3 components/screens/oled_diagnostic_v2.py
```

### Step 3: Interpret Results

**Success:**
```
[OK] ✓ OLED working on MAIN I2C BUS
Configuration: Address=0x3c, Size=128x64
```
→ OLED is working correctly!

**Partial Success:**
```
[OK] ✓ OLED working through MULTIPLEXER
```
→ OLED is behind multiplexer, update your code

**Failure:**
```
[X] ✗ OLED NOT DETECTED
```
→ Check wiring, power, and I2C configuration

## Comparison: Original vs V2 Diagnostic

| Feature | Original | V2 |
|---------|----------|-----|
| I2C Resource Management | ❌ Poor | ✅ Excellent |
| Bus Reset Capability | ❌ No | ✅ Yes |
| Multiple I2C Instance Creation | ❌ Yes (causes conflicts) | ✅ No |
| Proper Cleanup | ❌ No | ✅ Yes |
| Error Messages | ⚠️ Generic | ✅ Detailed |
| All Config Testing | ⚠️ Limited | ✅ Comprehensive |
| Lock Timeout Handling | ❌ No | ✅ Yes |

## Quick Command Reference

```bash
# Run improved diagnostic
python3 components/screens/oled_diagnostic_v2.py

# Check I2C devices
i2cdetect -y 1

# Check I2C bus status
dmesg | grep i2c

# Adjust I2C speed (add to /boot/config.txt)
dtparam=i2c_arm_baudrate=50000

# Reset I2C manually
sudo rmmod i2c_bcm2835 && sudo modprobe i2c_bcm2835

# Check if libraries are installed
python3 -c "import adafruit_ssd1306; print('OLED libs OK')"
```

## Still Having Issues?

1. **Verify OLED with another device** (Arduino, another Pi)
2. **Try different wiring** (use different jumper wires)
3. **Check for damaged pins** on OLED module
4. **Test with minimal setup** (disconnect other I2C devices)
5. **Try a different OLED module** (hardware may be faulty)

## Success Checklist

- [ ] I2C is enabled in `raspi-config`
- [ ] `i2cdetect -y 1` shows device at 0x3C or 0x3D
- [ ] Wiring is correct (VCC, GND, SDA, SCL)
- [ ] Power supply is adequate (3.3V or 5V as needed)
- [ ] Python libraries are installed
- [ ] V2 diagnostic detects and initializes OLED
- [ ] Display shows test message

---

**Last Updated:** March 13, 2026  
**Tool Version:** oled_diagnostic_v2.py  
**Author:** Diagnostic Improvement Project
