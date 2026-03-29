# PCA9548A I2C Multiplexer Setup Guide

This guide explains how to use the PCA9548A I2C multiplexer with your PiCrawler robot to control multiple I2C devices with the same address (e.g., two VL53L0X ToF sensors and an OLED display).

## What is the PCA9548A?

The PCA9548A is an 8-channel I2C multiplexer that allows you to connect up to 8 I2C buses to a single I2C port on your Raspberry Pi. This is essential when you have multiple devices with the same I2C address.

### Common Use Cases:
- **Multiple VL53L0X sensors** (all use address 0x29)
- **Multiple OLED displays** (all use address 0x3C)
- **Isolating noisy I2C devices**
- **Extending I2C bus capacity**

## Hardware Setup

### Pin Connections

**Raspberry Pi → PCA9548A:**
```
Pi GPIO 2 (SDA) → PCA9548A SDA
Pi GPIO 3 (SCL) → PCA9548A SCL
Pi 3.3V        → PCA9548A VCC
Pi GND         → PCA9548A GND
```

**PCA9548A → Devices:**
```
Channel 0 (SD0/SC0) → VL53L0X Sensor #1
Channel 1 (SD1/SC1) → VL53L0X Sensor #2
Channel 2 (SD2/SC2) → OLED Display
... (up to Channel 7)
```

### I2C Address Selection

The PCA9548A supports addresses 0x70-0x77 via address pins:

| A2 | A1 | A0 | Address |
|----|----|----|---------|
| L  | L  | L  | 0x70    |
| L  | L  | H  | 0x71    |
| L  | H  | L  | 0x72    |
| ... | ... | ... | ...    |
| H  | H  | H  | 0x77    |

**Default:** All address pins to GND = **0x70**

## Software Installation

### 1. Enable I2C on Raspberry Pi

```bash
sudo raspi-config
```

Navigate to: **Interface Options → I2C → Enable**

Reboot if needed:
```bash
sudo reboot
```

### 2. Install Required Python Libraries

**No special library needed for PCA9548A!** It works with the standard `smbus` library that comes with Raspberry Pi OS.

For VL53L0X sensors:
```bash
pip install VL53L0X
```

For OLED displays (if using):
```bash
pip install adafruit-circuitpython-ssd1306
```

### 3. Verify I2C is Working

Check that I2C devices are detected:
```bash
i2cdetect -y 1
```

You should see the multiplexer at 0x70 (or your chosen address).

## Testing Your Setup

### Step 1: Run the Diagnostic Tool

This will scan the multiplexer and detect all connected devices:

```bash
cd /Users/tapiapil/dev2/picrawler
python3 components/sensors/pca9548a_diagnostic.py
```

**Expected Output:**
```
======================================================================
  PCA9548A I2C Multiplexer Diagnostic
======================================================================

[1] Scanning main I2C bus (no multiplexer)...
  ✓ Found 1 device(s) on main bus:
      [0x70]  PCA9548A Multiplexer

[2] Checking for PCA9548A multiplexer...
  ✓ PCA9548A detected at 0x70

[3] Scanning multiplexer channels...
  Current control byte: 0x00

  ✓ Found devices on 2 channel(s):

  📍 Channel 0 (SD0):
     Found 1 device(s):
      [0x29]  VL53L0X/VL53L1X ToF Sensor - VL53L0X (ID: 0xEE) ✓

  📍 Channel 1 (SD1):
     Found 1 device(s):
      [0x29]  VL53L0X/VL53L1X ToF Sensor - VL53L0X (ID: 0xEE) ✓

[4] Summary and Recommendations
----------------------------------------------------------------------
  ✓ Two VL53L0X sensors detected - perfect for dual ToF setup!
```

### Step 2: Run the Dual Sensor Demo

Test reading from both sensors simultaneously:

```bash
python3 examples/dual_tof_with_multiplexer.py
```

This will show live distance readings from both sensors in a visual bar graph format.

## Using the Multiplexer in Your Code

### Basic Example

```python
from components.sensors.pca9548a_mux import PCA9548A
import VL53L0X
import time

# Initialize multiplexer
mux = PCA9548A(address=0x70)

# Initialize first VL53L0X on channel 0
mux.select_channel(0)
sensor1 = VL53L0X.VL53L0X(i2c_bus=1, i2c_address=0x29)
sensor1.open()
sensor1.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)

# Initialize second VL53L0X on channel 1
mux.select_channel(1)
sensor2 = VL53L0X.VL53L0X(i2c_bus=1, i2c_address=0x29)
sensor2.open()
sensor2.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)

# Read from sensors
while True:
    # Read sensor 1
    mux.select_channel(0)
    distance1 = sensor1.get_distance() / 10.0  # Convert to cm
    
    # Read sensor 2
    mux.select_channel(1)
    distance2 = sensor2.get_distance() / 10.0
    
    print(f"Sensor 1: {distance1:.1f} cm  |  Sensor 2: {distance2:.1f} cm")
    time.sleep(0.1)

# Cleanup
sensor1.stop_ranging()
sensor1.close()
sensor2.stop_ranging()
sensor2.close()
mux.close()
```

### Using Context Manager

```python
from components.sensors.pca9548a_mux import PCA9548A

# Automatically closes on exit
with PCA9548A(address=0x70) as mux:
    mux.select_channel(0)
    # Do something with channel 0
    
    mux.select_channel(1)
    # Do something with channel 1
# Channels automatically disabled when exiting
```

### Scanning for Devices

```python
from components.sensors.pca9548a_mux import PCA9548A

mux = PCA9548A()

# Scan all channels
results = mux.scan_all_channels()

for channel, devices in results.items():
    print(f"Channel {channel}: {[hex(d) for d in devices]}")

mux.close()
```

## Troubleshooting

### Problem: "PCA9548A not found at address 0x70"

**Solutions:**
1. Check wiring: SDA, SCL, VCC (3.3V), GND
2. Verify I2C is enabled: `sudo raspi-config`
3. Check for device: `i2cdetect -y 1`
4. Verify address pins (A0, A1, A2)
5. Check for proper pull-up resistors (usually 4.7kΩ)

### Problem: "No devices found on any multiplexer channel"

**Solutions:**
1. Verify sensors are connected to SD0/SC0, SD1/SC1, etc.
2. Each device needs VCC and GND connections
3. Check sensor power (VL53L0X needs 2.6V-3.5V)
4. Use `i2cdetect` after selecting channel manually

### Problem: Sensors not responding

**Solutions:**
1. Add small delays after channel switching (5-10ms)
2. Disable unused channels: `mux.select_channel(None)`
3. Initialize sensors one at a time
4. Check for I2C bus contention

### Problem: Inconsistent readings

**Solutions:**
1. Add proper decoupling capacitors (0.1µF) near each device
2. Keep I2C wires short (< 1 meter)
3. Use proper pull-up resistors (2.2kΩ - 4.7kΩ)
4. Avoid running I2C at high speed (use default 100kHz)

## API Reference

### PCA9548A Class

#### `__init__(bus_number=1, address=0x70)`
Initialize multiplexer controller.

#### `select_channel(channel)`
Select a single channel (0-7) or None to disable all.

```python
mux.select_channel(0)     # Enable channel 0
mux.select_channel(None)  # Disable all channels
```

#### `enable_multiple_channels(channels)`
Enable multiple channels simultaneously.

```python
mux.enable_multiple_channels([0, 1, 2])  # Enable channels 0, 1, 2
```

#### `get_active_channels()`
Get list of currently active channels.

```python
active = mux.get_active_channels()  # Returns [0, 1, 2]
```

#### `scan_channel(channel)`
Scan for devices on a specific channel.

```python
devices = mux.scan_channel(0)  # Returns [0x29, 0x3C, ...]
```

#### `scan_all_channels()`
Scan all channels and return dictionary of results.

```python
results = mux.scan_all_channels()  # {0: [0x29], 1: [0x29], ...}
```

#### `close()`
Disable all channels and close I2C bus.

## Files in This Package

- **`pca9548a_diagnostic.py`** - Diagnostic tool to test multiplexer
- **`pca9548a_mux.py`** - Reusable multiplexer controller class
- **`../examples/dual_tof_with_multiplexer.py`** - Example with dual VL53L0X
- **`README_MULTIPLEXER.md`** - This file

## Additional Resources

- [PCA9548A Datasheet](https://www.ti.com/lit/ds/symlink/pca9548a.pdf)
- [VL53L0X Datasheet](https://www.st.com/resource/en/datasheet/vl53l0x.pdf)
- [Raspberry Pi I2C Documentation](https://www.raspberrypi.org/documentation/hardware/raspberrypi/i2c/)

## Support

If you encounter issues:

1. Run the diagnostic: `python3 components/sensors/pca9548a_diagnostic.py`
2. Check wiring and connections
3. Verify I2C is enabled: `i2cdetect -y 1`
4. Review troubleshooting section above

---

**Happy building! 🤖**
