#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced PCA9548A Diagnostic with Live Sensor Data

This enhanced diagnostic tool not only detects devices on the multiplexer
but also initializes them and displays live sensor readings.

Tests:
1. Multiplexer detection and channel scanning
2. Device identification
3. LIVE sensor readings:
   - Accelerometer (SD1): pitch, roll, acceleration
   - Front ToF sensor (SD2): distance measurements
   - Rear ToF sensor (SD3): distance measurements

Hardware Setup:
    - PCA9548A at address 0x70
    - SD1 (Channel 1): VL53L0X Rear ToF
    - SD2 (Channel 2): VL53L0X Front ToF
    - SD7 (Channel 7): MPU6050 Accelerometer

Usage:
    python pca9548a_diagnostic_with_data.py
"""

import os
import sys
import smbus
import time

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configuration
I2C_BUS = 1
MUX_DEFAULT_ADDR = 0x70
REAR_TOF_CHANNEL = 1   # SD1: Rear ToF sensor
FRONT_TOF_CHANNEL = 2  # SD2: Front ToF sensor
ACCEL_CHANNEL = 7      # SD7: MPU6050 Accelerometer

# Common device names for known I2C addresses
KNOWN_DEVICES = {
    0x29: "VL53L0X/VL53L1X ToF Sensor",
    0x3C: "SSD1306 OLED Display (128x64)",
    0x3D: "SSD1306 OLED Display (128x32)",
    0x48: "ADS1115 ADC",
    0x50: "EEPROM (AT24C)",
    0x68: "MPU6050/DS1307 RTC",
    0x76: "BMP280/BME280",
    0x77: "BMP180/BMP280",
}

# Check for required libraries
HAS_VL53L0X = False
HAS_ACCELEROMETER = False

try:
    import VL53L0X
    HAS_VL53L0X = True
except ImportError:
    print("[!] VL53L0X library not found. Install with: pip install VL53L0X")

try:
    from components.sensors import accelerometer
    HAS_ACCELEROMETER = True
except ImportError:
    print("[!] Accelerometer module not found. Check components/sensors/accelerometer.py")


class PCA9548A:
    """Simple controller for PCA9548A I2C multiplexer"""
    
    def __init__(self, bus_number=1, address=0x70):
        """
        Initialize multiplexer controller.
        
        Args:
            bus_number: I2C bus number (default 1 for Raspberry Pi)
            address: Multiplexer I2C address (default 0x70)
        """
        self.bus = smbus.SMBus(bus_number)
        self.address = address
        self.current_channel = None
        
    def select_channel(self, channel):
        """
        Select a single channel (0-7) on the multiplexer.
        
        Args:
            channel: Channel number 0-7, or None to disable all channels
        """
        if channel is None:
            # Disable all channels
            self.bus.write_byte(self.address, 0x00)
            self.current_channel = None
        elif 0 <= channel <= 7:
            # Enable specific channel
            control_byte = 1 << channel
            self.bus.write_byte(self.address, control_byte)
            self.current_channel = channel
        else:
            raise ValueError(f"Channel must be 0-7, got {channel}")
    
    def get_current_channel(self):
        """
        Read which channel(s) are currently enabled.
        
        Returns:
            int: Control byte showing which channels are active
        """
        return self.bus.read_byte(self.address)
    
    def scan_channel(self, channel):
        """
        Scan for I2C devices on a specific channel.
        
        Args:
            channel: Channel number 0-7
            
        Returns:
            list: List of I2C addresses found on this channel
        """
        self.select_channel(channel)
        time.sleep(0.01)  # Small delay for channel switch
        
        devices = []
        for addr in range(0x03, 0x78):
            if addr == self.address:
                continue  # Skip the multiplexer itself
            
            try:
                self.bus.read_byte(addr)
                devices.append(addr)
            except OSError:
                pass
        
        return devices
    
    def scan_all_channels(self):
        """
        Scan all 8 channels for connected devices.
        
        Returns:
            dict: Dictionary with channel numbers as keys and device lists as values
        """
        results = {}
        for channel in range(8):
            devices = self.scan_channel(channel)
            if devices:
                results[channel] = devices
        
        # Disable all channels when done
        self.select_channel(None)
        return results
    
    def close(self):
        """Close the I2C bus"""
        self.select_channel(None)  # Disable all channels
        self.bus.close()


def scan_main_bus(bus_number=1):
    """
    Scan the main I2C bus (without going through multiplexer).
    
    Returns:
        list: List of I2C addresses found
    """
    bus = smbus.SMBus(bus_number)
    devices = []
    
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            devices.append(addr)
        except OSError:
            pass
    
    bus.close()
    return devices


def detect_vl53l0x(bus, addr):
    """
    Try to detect if a device is a VL53L0X by reading its model ID.
    
    Returns:
        str: "VL53L0X" if detected, "Unknown" otherwise
    """
    try:
        # VL53L0X model ID register is at 0xC0, should return 0xEE
        model_id = bus.read_byte_data(addr, 0xC0)
        if model_id == 0xEE:
            return "VL53L0X (ID: 0xEE) [OK]"
    except Exception:
        pass
    
    return "Device present"


def print_device_info(addr, name_hint="Unknown", detail=""):
    """Pretty print device information"""
    addr_str = f"0x{addr:02X}"
    if detail:
        print(f"      [{addr_str}]  {name_hint} - {detail}")
    else:
        print(f"      [{addr_str}]  {name_hint}")


def detect_and_scan():
    """
    Phase 1: Detect multiplexer and scan all channels.
    
    Returns:
        PCA9548A instance or None if failed
    """
    print("=" * 70)
    print("  Enhanced PCA9548A Diagnostic with Live Sensor Data")
    print("=" * 70)
    print()
    
    # Step 1: Scan main I2C bus
    print("[1] Scanning main I2C bus (no multiplexer)...")
    try:
        main_devices = scan_main_bus(I2C_BUS)
    except Exception as e:
        print(f"  [X] Error accessing I2C bus: {e}")
        print(f"  Make sure I2C is enabled: sudo raspi-config -> Interface Options -> I2C")
        return None
    
    if not main_devices:
        print("  [X] No I2C devices found!")
        print("  Check wiring: SDA, SCL, VCC, GND")
        print("  Check pull-up resistors (usually 4.7kΩ on SDA/SCL)")
        return None
    
    print(f"  [OK] Found {len(main_devices)} device(s) on main bus:")
    for addr in main_devices:
        name = KNOWN_DEVICES.get(addr, "Unknown device")
        print_device_info(addr, name)
    print()
    
    # Step 2: Check for multiplexer
    print("[2] Checking for PCA9548A multiplexer...")
    mux_addresses = [a for a in main_devices if 0x70 <= a <= 0x77]
    
    if not mux_addresses:
        print("  [X] No PCA9548A detected!")
        print(f"  Expected address range: 0x70-0x77")
        print(f"  Your devices: {', '.join(f'0x{a:02X}' for a in main_devices)}")
        return None
    
    mux_addr = mux_addresses[0]
    print(f"  [OK] PCA9548A detected at 0x{mux_addr:02X}")
    
    if len(mux_addresses) > 1:
        print(f"  Note: Multiple possible multiplexers: {', '.join(f'0x{a:02X}' for a in mux_addresses)}")
        print(f"        Using 0x{mux_addr:02X}")
    print()
    
    # Step 3: Initialize multiplexer and scan channels
    print("[3] Scanning multiplexer channels...")
    try:
        mux = PCA9548A(bus_number=I2C_BUS, address=mux_addr)
    except Exception as e:
        print(f"  [X] Failed to initialize multiplexer: {e}")
        return None
    
    try:
        # Read current state
        current_state = mux.get_current_channel()
        print(f"  Current control byte: 0x{current_state:02X}")
        print()
        
        # Scan all channels
        results = mux.scan_all_channels()
        
        if not results:
            print("  [!] No devices found on any multiplexer channel!")
            return mux
        
        print(f"  [OK] Found devices on {len(results)} channel(s):")
        print()
        
        for channel, devices in sorted(results.items()):
            print(f"  >> Channel {channel} (SD{channel}):")
            print(f"     Found {len(devices)} device(s):")
            
            for addr in devices:
                name = KNOWN_DEVICES.get(addr, "Unknown device")
                
                # Try to get more details for specific devices
                if addr == 0x29:
                    detail = detect_vl53l0x(mux.bus, addr)
                    print_device_info(addr, name, detail)
                else:
                    print_device_info(addr, name)
            print()
        
        return mux
        
    except Exception as e:
        print(f"  [X] Error scanning channels: {e}")
        mux.close()
        return None


def initialize_sensors(mux):
    """
    Phase 2: Initialize all sensors on their respective channels.
    
    Args:
        mux: PCA9548A instance
        
    Returns:
        dict: Dictionary with initialized sensor objects
    """
    print("[4] Initializing sensors...")
    print()
    
    sensors = {
        'accelerometer': None,
        'front_tof': None,
        'rear_tof': None
    }
    
    # Initialize accelerometer on channel 1
    if HAS_ACCELEROMETER:
        print(f"  Initializing accelerometer on channel {ACCEL_CHANNEL}...")
        try:
            mux.select_channel(ACCEL_CHANNEL)
            time.sleep(0.05)
            accelerometer.wake()
            time.sleep(0.1)
            # Test read
            pitch, roll = accelerometer.get_tilt()
            sensors['accelerometer'] = True
            print(f"  [OK] Accelerometer initialized (pitch={pitch:.1f}°, roll={roll:.1f}°)")
        except Exception as e:
            print(f"  [X] Accelerometer initialization failed: {e}")
    else:
        print(f"  [!] Skipping accelerometer (library not available)")
    print()
    
    # Initialize front ToF on channel 2
    if HAS_VL53L0X:
        print(f"  Initializing front ToF sensor on channel {FRONT_TOF_CHANNEL}...")
        try:
            mux.select_channel(FRONT_TOF_CHANNEL)
            time.sleep(0.05)
            front = VL53L0X.VL53L0X(i2c_bus=I2C_BUS, i2c_address=0x29)
            front.open()
            front.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
            # Test read
            distance_mm = front.get_distance()
            sensors['front_tof'] = front
            print(f"  [OK] Front ToF initialized (distance={distance_mm/10:.1f}cm)")
        except Exception as e:
            print(f"  [X] Front ToF initialization failed: {e}")
    else:
        print(f"  [!] Skipping front ToF (VL53L0X library not available)")
    print()
    
    # Initialize rear ToF on channel 3
    if HAS_VL53L0X:
        print(f"  Initializing rear ToF sensor on channel {REAR_TOF_CHANNEL}...")
        try:
            mux.select_channel(REAR_TOF_CHANNEL)
            time.sleep(0.05)
            rear = VL53L0X.VL53L0X(i2c_bus=I2C_BUS, i2c_address=0x29)
            rear.open()
            rear.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
            # Test read
            distance_mm = rear.get_distance()
            sensors['rear_tof'] = rear
            print(f"  [OK] Rear ToF initialized (distance={distance_mm/10:.1f}cm)")
        except Exception as e:
            print(f"  [X] Rear ToF initialization failed: {e}")
    else:
        print(f"  [!] Skipping rear ToF (VL53L0X library not available)")
    print()
    
    # Disable all channels
    mux.select_channel(None)
    
    # Check if any sensors initialized
    if not any(sensors.values()):
        print("  [X] No sensors initialized successfully!")
        return None
    
    return sensors


def live_data_loop(mux, sensors):
    """
    Phase 3: Display live sensor data in a loop.
    
    Args:
        mux: PCA9548A instance
        sensors: Dictionary of initialized sensor objects
    """
    print("[5] Starting live data stream...")
    print("    Press Ctrl+C to stop")
    print()
    time.sleep(2)  # Give user time to read
    
    try:
        while True:
            # Clear screen
            print("\033[2J\033[H", end="")
            
            print("=" * 70)
            print("  Live Sensor Data (Ctrl+C to exit)")
            print("=" * 70)
            print()
            
            # Read accelerometer
            if sensors['accelerometer']:
                try:
                    mux.select_channel(ACCEL_CHANNEL)
                    time.sleep(0.01)
                    pitch, roll = accelerometer.get_tilt()
                    ax, ay, az = accelerometer.read_accel()
                    
                    print(f"Accelerometer (Channel {ACCEL_CHANNEL}, SD{ACCEL_CHANNEL}):")
                    print(f"  Pitch:       {pitch:+7.2f}°")
                    print(f"  Roll:        {roll:+7.2f}°")
                    print(f"  Accel X:     {ax:+7.3f}g")
                    print(f"  Accel Y:     {ay:+7.3f}g")
                    print(f"  Accel Z:     {az:+7.3f}g")
                    print()
                except Exception as e:
                    print(f"Accelerometer: ERROR - {e}")
                    print()
            
            # Read front ToF
            if sensors['front_tof']:
                try:
                    mux.select_channel(FRONT_TOF_CHANNEL)
                    time.sleep(0.002)
                    distance_mm = sensors['front_tof'].get_distance()
                    distance_cm = distance_mm / 10.0
                    
                    # Create bar graph (scaled to 120cm max)
                    bar_length = int(min(50, distance_cm / 120.0 * 50))
                    bar = "#" * bar_length
                    
                    print(f"Front ToF Sensor (Channel {FRONT_TOF_CHANNEL}, SD{FRONT_TOF_CHANNEL}):")
                    print(f"  Distance:    {distance_cm:7.1f} cm")
                    print(f"  [{bar:<50}]")
                    print()
                except Exception as e:
                    print(f"Front ToF: ERROR - {e}")
                    print()
            
            # Read rear ToF
            if sensors['rear_tof']:
                try:
                    mux.select_channel(REAR_TOF_CHANNEL)
                    time.sleep(0.002)
                    distance_mm = sensors['rear_tof'].get_distance()
                    distance_cm = distance_mm / 10.0
                    
                    # Create bar graph (scaled to 120cm max)
                    bar_length = int(min(50, distance_cm / 120.0 * 50))
                    bar = "#" * bar_length
                    
                    print(f"Rear ToF Sensor (Channel {REAR_TOF_CHANNEL}, SD{REAR_TOF_CHANNEL}):")
                    print(f"  Distance:    {distance_cm:7.1f} cm")
                    print(f"  [{bar:<50}]")
                    print()
                except Exception as e:
                    print(f"Rear ToF: ERROR - {e}")
                    print()
            
            print("=" * 70)
            
            time.sleep(0.1)  # 10 Hz update rate
    
    except KeyboardInterrupt:
        print("\n\n[!] Stopped by user")
        print()


def cleanup_sensors(mux, sensors):
    """
    Clean up and close all sensors.
    
    Args:
        mux: PCA9548A instance
        sensors: Dictionary of sensor objects
    """
    print("[6] Cleaning up sensors...")
    
    # Stop front ToF
    if sensors and sensors.get('front_tof'):
        try:
            mux.select_channel(FRONT_TOF_CHANNEL)
            sensors['front_tof'].stop_ranging()
            sensors['front_tof'].close()
            print("  [OK] Front ToF closed")
        except Exception as e:
            print(f"  [!] Front ToF cleanup error: {e}")
    
    # Stop rear ToF
    if sensors and sensors.get('rear_tof'):
        try:
            mux.select_channel(REAR_TOF_CHANNEL)
            sensors['rear_tof'].stop_ranging()
            sensors['rear_tof'].close()
            print("  [OK] Rear ToF closed")
        except Exception as e:
            print(f"  [!] Rear ToF cleanup error: {e}")
    
    # Close multiplexer
    if mux:
        try:
            mux.close()
            print("  [OK] Multiplexer closed")
        except Exception as e:
            print(f"  [!] Multiplexer cleanup error: {e}")
    
    print()


def main():
    """Main diagnostic routine"""
    mux = None
    sensors = None
    
    try:
        # Phase 1: Detect and scan
        mux = detect_and_scan()
        if not mux:
            return 1
        
        # Phase 2: Initialize sensors
        sensors = initialize_sensors(mux)
        if not sensors:
            print("  [X] Cannot proceed - no sensors initialized")
            mux.close()
            return 1
        
        # Phase 3: Live data display
        live_data_loop(mux, sensors)
        
    except Exception as e:
        print(f"\n[X] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Always cleanup
        cleanup_sensors(mux, sensors)
    
    print("=" * 70)
    print("  Diagnostic complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(0)
