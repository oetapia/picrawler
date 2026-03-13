#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dual VL53L0X Time-of-Flight Sensors with PCA9548A Multiplexer Example

This example demonstrates how to use two VL53L0X sensors with the same I2C address
by using a PCA9548A multiplexer. Also shows OLED display integration.

Hardware Setup:
    - PCA9548A at address 0x70 (default)
    - VL53L0X #1 connected to channel 0 (SD0)
    - VL53L0X #2 connected to channel 1 (SD1)
    - OLED display connected to channel 2 (SD2) - optional
    
Wiring:
    Raspberry Pi → PCA9548A:
        SDA (GPIO 2) → SDA
        SCL (GPIO 3) → SCL
        3.3V → VCC
        GND → GND
    
    PCA9548A → VL53L0X #1 (Channel 0):
        SD0 → SDA
        SC0 → SCL
        (Share VCC and GND)
    
    PCA9548A → VL53L0X #2 (Channel 1):
        SD1 → SDA
        SC1 → SCL
        (Share VCC and GND)
    
    PCA9548A → OLED (Channel 2):
        SD2 → SDA
        SC2 → SCL
        (Share VCC and GND)

Usage:
    python dual_tof_with_multiplexer.py
"""

import sys
import time
from components.sensors.pca9548a_mux import PCA9548A

# Try to import VL53L0X
try:
    import VL53L0X
    HAS_VL53L0X = True
except ImportError:
    HAS_VL53L0X = False
    print("⚠ VL53L0X library not found. Install with: pip install VL53L0X")

# Try to import OLED libraries
try:
    import board
    import busio
    import adafruit_ssd1306
    HAS_OLED = True
except ImportError:
    HAS_OLED = False
    print("⚠ OLED libraries not found. Install with: pip install adafruit-circuitpython-ssd1306")


class DualToFSensors:
    """Manage two VL53L0X sensors through a multiplexer"""
    
    def __init__(self, mux, channel_left=0, channel_right=1):
        """
        Initialize dual ToF sensors.
        
        Args:
            mux: PCA9548A multiplexer instance
            channel_left: Multiplexer channel for left sensor
            channel_right: Multiplexer channel for right sensor
        """
        self.mux = mux
        self.channel_left = channel_left
        self.channel_right = channel_right
        self.sensor_left = None
        self.sensor_right = None
        
        if not HAS_VL53L0X:
            raise ImportError("VL53L0X library required")
        
        # Initialize left sensor
        print(f"Initializing left sensor on channel {channel_left}...")
        self.mux.select_channel(channel_left)
        time.sleep(0.05)
        try:
            self.sensor_left = VL53L0X.VL53L0X(i2c_bus=1, i2c_address=0x29)
            self.sensor_left.open()
            self.sensor_left.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
            print("  ✓ Left sensor initialized")
        except Exception as e:
            print(f"  ✗ Failed to initialize left sensor: {e}")
            raise
        
        # Initialize right sensor
        print(f"Initializing right sensor on channel {channel_right}...")
        self.mux.select_channel(channel_right)
        time.sleep(0.05)
        try:
            self.sensor_right = VL53L0X.VL53L0X(i2c_bus=1, i2c_address=0x29)
            self.sensor_right.open()
            self.sensor_right.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
            print("  ✓ Right sensor initialized")
        except Exception as e:
            print(f"  ✗ Failed to initialize right sensor: {e}")
            raise
        
        # Disable channels when done
        self.mux.select_channel(None)
    
    def read_left(self):
        """Read distance from left sensor in cm"""
        self.mux.select_channel(self.channel_left)
        time.sleep(0.002)  # Small delay for channel switch
        distance_mm = self.sensor_left.get_distance()
        return distance_mm / 10.0
    
    def read_right(self):
        """Read distance from right sensor in cm"""
        self.mux.select_channel(self.channel_right)
        time.sleep(0.002)  # Small delay for channel switch
        distance_mm = self.sensor_right.get_distance()
        return distance_mm / 10.0
    
    def read_both(self):
        """
        Read both sensors and return as tuple.
        
        Returns:
            tuple: (left_cm, right_cm)
        """
        left = self.read_left()
        right = self.read_right()
        return left, right
    
    def close(self):
        """Clean up sensors"""
        if self.sensor_left:
            self.mux.select_channel(self.channel_left)
            try:
                self.sensor_left.stop_ranging()
                self.sensor_left.close()
            except:
                pass
        
        if self.sensor_right:
            self.mux.select_channel(self.channel_right)
            try:
                self.sensor_right.stop_ranging()
                self.sensor_right.close()
            except:
                pass
        
        self.mux.select_channel(None)


def visualize_distances(left_cm, right_cm, max_distance=100):
    """Create a visual bar graph of distances"""
    left_bar = "#" * max(0, min(40, int(left_cm / max_distance * 40)))
    right_bar = "#" * max(0, min(40, int(right_cm / max_distance * 40)))
    
    print(f"\033[2K\rLeft:  {left_cm:6.1f} cm  |{left_bar:<40}|", end="")
    print(f"\033[2K\n\033[2K\rRight: {right_cm:6.1f} cm  |{right_bar:<40}|", end="")
    print("\033[F", end="", flush=True)  # Move cursor up


def main():
    """Main demo routine"""
    print("=" * 70)
    print("  Dual VL53L0X with PCA9548A Multiplexer Demo")
    print("=" * 70)
    print()
    
    # Check dependencies
    if not HAS_VL53L0X:
        print("Error: VL53L0X library required")
        print("Install with: pip install VL53L0X")
        return 1
    
    # Initialize multiplexer
    print("[1] Initializing PCA9548A multiplexer...")
    try:
        mux = PCA9548A(address=0x70)
        print(f"  ✓ Multiplexer found at 0x70")
    except IOError as e:
        print(f"  ✗ {e}")
        print("  Run pca9548a_diagnostic.py to check your setup")
        return 1
    
    # Scan channels
    print()
    print("[2] Scanning multiplexer channels...")
    results = mux.scan_all_channels()
    
    if not results:
        print("  ✗ No devices found on any channel!")
        print("  Connect your sensors to SD0, SD1, etc.")
        mux.close()
        return 1
    
    for channel, devices in sorted(results.items()):
        devices_str = ", ".join(f"0x{d:02X}" for d in devices)
        print(f"  Channel {channel}: {devices_str}")
    
    # Determine which channels have sensors
    sensor_channels = []
    for channel, devices in results.items():
        if 0x29 in devices:
            sensor_channels.append(channel)
    
    if len(sensor_channels) < 2:
        print()
        print(f"  ✗ Need 2 VL53L0X sensors, found {len(sensor_channels)}")
        print("  Connect two VL53L0X sensors to different channels")
        mux.close()
        return 1
    
    print()
    print(f"[3] Using VL53L0X sensors on channels {sensor_channels[0]} and {sensor_channels[1]}")
    
    # Initialize dual sensors
    try:
        sensors = DualToFSensors(mux, 
                                 channel_left=sensor_channels[0], 
                                 channel_right=sensor_channels[1])
    except Exception as e:
        print(f"  ✗ Failed to initialize sensors: {e}")
        mux.close()
        return 1
    
    print()
    print("[4] Reading sensors - Press Ctrl+C to exit")
    print()
    print("Reading both sensors simultaneously...")
    print()
    
    try:
        while True:
            left_cm, right_cm = sensors.read_both()
            visualize_distances(left_cm, right_cm)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        sensors.close()
        mux.close()
    
    print()
    print("=" * 70)
    print("  Demo complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
