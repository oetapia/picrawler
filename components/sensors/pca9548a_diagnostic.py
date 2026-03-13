#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCA9548A I2C Multiplexer Diagnostic Tool

Tests the PCA9548A multiplexer and scans all 8 channels for connected devices.
Useful for detecting VL53L0X ToF sensors and OLED displays behind the multiplexer.

The PCA9548A allows up to 8 I2C devices (or buses) to be connected to a single
I2C port. This is especially useful when you have multiple devices with the same
I2C address (like multiple VL53L0X sensors at 0x29).

Multiplexer Control:
    - Default address: 0x70 (can be 0x70-0x77 via address pins)
    - Control byte selects active channel(s):
      * 0x00: All channels disabled
      * 0x01: Channel 0 enabled
      * 0x02: Channel 1 enabled
      * 0x04: Channel 2 enabled
      * ... up to 0x80 for channel 7

Usage:
    python pca9548a_diagnostic.py
"""

import smbus
import time
import sys

# Configuration
I2C_BUS = 1
MUX_DEFAULT_ADDR = 0x70  # PCA9548A default address

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


def detect_vl53l0x(bus, addr, channel_info=""):
    """
    Try to detect if a device is a VL53L0X by reading its model ID.
    
    Returns:
        str: "VL53L0X" if detected, "Unknown" otherwise
    """
    try:
        # VL53L0X model ID register is at 0xC0, should return 0xEE
        model_id = bus.read_byte_data(addr, 0xC0)
        if model_id == 0xEE:
            return "VL53L0X (ID: 0xEE) ✓"
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


def main():
    """Main diagnostic routine"""
    print("=" * 70)
    print("  PCA9548A I2C Multiplexer Diagnostic")
    print("=" * 70)
    print()
    
    # Step 1: Scan main I2C bus
    print("[1] Scanning main I2C bus (no multiplexer)...")
    try:
        main_devices = scan_main_bus(I2C_BUS)
    except Exception as e:
        print(f"  ✗ Error accessing I2C bus: {e}")
        print(f"  Make sure I2C is enabled: sudo raspi-config → Interface Options → I2C")
        return 1
    
    if not main_devices:
        print("  ✗ No I2C devices found!")
        print("  Check wiring: SDA, SCL, VCC, GND")
        print("  Check pull-up resistors (usually 4.7kΩ on SDA/SCL)")
        return 1
    
    print(f"  ✓ Found {len(main_devices)} device(s) on main bus:")
    for addr in main_devices:
        name = KNOWN_DEVICES.get(addr, "Unknown device")
        print_device_info(addr, name)
    print()
    
    # Step 2: Check for multiplexer
    print("[2] Checking for PCA9548A multiplexer...")
    mux_addresses = [a for a in main_devices if 0x70 <= a <= 0x77]
    
    if not mux_addresses:
        print("  ✗ No PCA9548A detected!")
        print(f"  Expected address range: 0x70-0x77")
        print(f"  Your devices: {', '.join(f'0x{a:02X}' for a in main_devices)}")
        print()
        print("  Troubleshooting:")
        print("    - Verify PCA9548A is powered (VCC to 3.3V, GND to GND)")
        print("    - Check SDA/SCL connections from Pi to multiplexer")
        print("    - Default address is 0x70 (all address pins to GND)")
        return 1
    
    mux_addr = mux_addresses[0]
    print(f"  ✓ PCA9548A detected at 0x{mux_addr:02X}")
    
    if len(mux_addresses) > 1:
        print(f"  Note: Multiple possible multiplexers: {', '.join(f'0x{a:02X}' for a in mux_addresses)}")
        print(f"        Using 0x{mux_addr:02X}")
    print()
    
    # Step 3: Initialize multiplexer and scan channels
    print("[3] Scanning multiplexer channels...")
    try:
        mux = PCA9548A(bus_number=I2C_BUS, address=mux_addr)
    except Exception as e:
        print(f"  ✗ Failed to initialize multiplexer: {e}")
        return 1
    
    try:
        # Read current state
        current_state = mux.get_current_channel()
        print(f"  Current control byte: 0x{current_state:02X}")
        print()
        
        # Scan all channels
        results = mux.scan_all_channels()
        
        if not results:
            print("  ⚠ No devices found on any multiplexer channel!")
            print()
            print("  This means:")
            print("    - Multiplexer is working (it responds)")
            print("    - But no devices are connected to SD0-SD7 channels")
            print()
            print("  Check:")
            print("    - Connect your sensors/displays to SD0, SD1, SD2, etc.")
            print("    - Each channel needs its own set of devices")
            print("    - Power (VCC) and GND should go to each device")
        else:
            print(f"  ✓ Found devices on {len(results)} channel(s):")
            print()
            
            for channel, devices in sorted(results.items()):
                print(f"  📍 Channel {channel} (SD{channel}):")
                print(f"     Found {len(devices)} device(s):")
                
                for addr in devices:
                    name = KNOWN_DEVICES.get(addr, "Unknown device")
                    
                    # Try to get more details for specific devices
                    if addr == 0x29:
                        # Could be VL53L0X or VL53L1X
                        detail = detect_vl53l0x(mux.bus, addr, f"CH{channel}")
                        print_device_info(addr, name, detail)
                    else:
                        print_device_info(addr, name)
                print()
        
        # Step 4: Summary and recommendations
        print("[4] Summary and Recommendations")
        print("-" * 70)
        
        # Count device types
        vl53_count = 0
        oled_count = 0
        
        for channel, devices in results.items():
            for addr in devices:
                if addr == 0x29:
                    vl53_count += 1
                elif addr in [0x3C, 0x3D]:
                    oled_count += 1
        
        if vl53_count == 2:
            print("  ✓ Two VL53L0X sensors detected - perfect for dual ToF setup!")
            print("    Use different channels for each sensor to avoid conflicts.")
        elif vl53_count == 1:
            print("  ℹ One VL53L0X sensor detected.")
            print("    Connect the second sensor to a different channel.")
        elif vl53_count > 2:
            print(f"  ℹ {vl53_count} ToF sensors detected.")
        
        if oled_count >= 1:
            print(f"  ✓ OLED display(s) detected on {oled_count} channel(s).")
        
        print()
        print("  💡 Using the multiplexer in your code:")
        print()
        print("     # Import the multiplexer class")
        print("     from components.sensors.pca9548a_mux import PCA9548A")
        print()
        print("     # Initialize")
        print(f"     mux = PCA9548A(address=0x{mux_addr:02X})")
        print()
        print("     # Select channel for first VL53L0X sensor")
        print("     mux.select_channel(0)  # Use channel where sensor 1 is")
        print("     sensor1 = VL53L0XSensor(i2c_address=0x29)")
        print()
        print("     # Select channel for second VL53L0X sensor")
        print("     mux.select_channel(1)  # Use channel where sensor 2 is")
        print("     sensor2 = VL53L0XSensor(i2c_address=0x29)")
        print()
        print("     # Select channel for OLED")
        print("     mux.select_channel(2)  # Use channel where OLED is")
        print("     # Initialize OLED here")
        print()
        
    finally:
        mux.close()
    
    print("=" * 70)
    print("  Diagnostic complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
