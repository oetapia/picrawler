#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED Display Diagnostic Tool

Tests OLED displays on both main I2C bus and through PCA9548A multiplexer.
Helps identify connection issues and determine the correct I2C address.

Usage:
    python3 oled_diagnostic.py
"""

import sys
import time

# Try to import required libraries
try:
    import smbus
    HAS_SMBUS = True
except ImportError:
    HAS_SMBUS = False
    print("[!] smbus not available")

try:
    import board
    import busio
    import adafruit_ssd1306
    HAS_OLED = True
except ImportError:
    HAS_OLED = False
    print("[!] OLED libraries not installed")
    print("    Install with: pip install adafruit-circuitpython-ssd1306")


def scan_i2c_bus(bus_number=1):
    """Scan I2C bus for devices"""
    if not HAS_SMBUS:
        return []
    
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


def test_oled_on_main_bus():
    """Test OLED on main I2C bus (not through multiplexer)"""
    print("\n[TEST 1] Checking OLED on main I2C bus...")
    print("-" * 60)
    
    if not HAS_OLED:
        print("[X] OLED libraries not installed")
        return False
    
    # Scan for devices
    devices = scan_i2c_bus()
    print(f"Devices found: {[hex(d) for d in devices]}")
    
    # Check for common OLED addresses
    oled_addresses = [0x3C, 0x3D]
    found_addresses = [addr for addr in oled_addresses if addr in devices]
    
    if not found_addresses:
        print("[X] No OLED detected at 0x3C or 0x3D on main bus")
        return False
    
    print(f"[OK] Possible OLED found at: {[hex(a) for a in found_addresses]}")
    
    # Try to initialize each address
    for addr in found_addresses:
        print(f"\nTrying to initialize OLED at {hex(addr)}...")
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            # Try 128x64 first (most common)
            try:
                display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=addr)
                display.fill(0)
                display.text('Test 128x64', 0, 0, 1)
                display.show()
                print(f"[OK] OLED at {hex(addr)} is 128x64 - Display updated!")
                time.sleep(2)
                display.fill(0)
                display.show()
                return True
            except Exception as e1:
                # Try 128x32
                try:
                    display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=addr)
                    display.fill(0)
                    display.text('Test 128x32', 0, 0, 1)
                    display.show()
                    print(f"[OK] OLED at {hex(addr)} is 128x32 - Display updated!")
                    time.sleep(2)
                    display.fill(0)
                    display.show()
                    return True
                except Exception as e2:
                    print(f"[X] Failed to initialize OLED at {hex(addr)}")
                    print(f"    128x64 error: {e1}")
                    print(f"    128x32 error: {e2}")
        except Exception as e:
            print(f"[X] Error accessing {hex(addr)}: {e}")
    
    return False


def test_oled_through_multiplexer(mux_addr=0x70):
    """Test OLED through PCA9548A multiplexer on each channel"""
    print("\n[TEST 2] Checking OLED through PCA9548A multiplexer...")
    print("-" * 60)
    
    if not HAS_SMBUS:
        print("[X] smbus not available")
        return False
    
    # Check if multiplexer exists
    bus = smbus.SMBus(1)
    try:
        bus.read_byte(mux_addr)
        print(f"[OK] PCA9548A found at {hex(mux_addr)}")
    except OSError:
        print(f"[X] PCA9548A not found at {hex(mux_addr)}")
        bus.close()
        return False
    
    # Scan each channel
    oled_found = False
    for channel in range(8):
        # Select channel
        control_byte = 1 << channel
        bus.write_byte(mux_addr, control_byte)
        time.sleep(0.01)
        
        # Scan for devices on this channel
        devices = []
        for addr in range(0x03, 0x78):
            if addr == mux_addr:
                continue
            try:
                bus.read_byte(addr)
                devices.append(addr)
            except OSError:
                pass
        
        if devices:
            print(f"\nChannel {channel}: {[hex(d) for d in devices]}")
            
            # Check for OLED addresses
            oled_addresses = [0x3C, 0x3D]
            found_oled = [addr for addr in oled_addresses if addr in devices]
            
            if found_oled and HAS_OLED:
                for addr in found_oled:
                    print(f"  Testing OLED at {hex(addr)} on channel {channel}...")
                    try:
                        # Keep channel selected
                        bus.write_byte(mux_addr, control_byte)
                        time.sleep(0.05)
                        
                        i2c = busio.I2C(board.SCL, board.SDA)
                        
                        # Try both resolutions
                        for width, height in [(128, 64), (128, 32)]:
                            try:
                                display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)
                                display.fill(0)
                                display.text(f'CH{channel} {width}x{height}', 0, 0, 1)
                                display.show()
                                print(f"  [OK] OLED {width}x{height} working on channel {channel}!")
                                time.sleep(2)
                                display.fill(0)
                                display.show()
                                oled_found = True
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        print(f"  [X] Error: {e}")
    
    # Disable all channels
    bus.write_byte(mux_addr, 0x00)
    bus.close()
    
    if not oled_found:
        print("\n[X] No working OLED found on any multiplexer channel")
    
    return oled_found


def main():
    print("=" * 60)
    print("  OLED Display Diagnostic Tool")
    print("=" * 60)
    
    if not HAS_SMBUS:
        print("\n[X] smbus module required but not found")
        print("This module should be pre-installed on Raspberry Pi OS")
        return 1
    
    if not HAS_OLED:
        print("\n[X] OLED libraries not installed")
        print("Install with:")
        print("  pip install adafruit-circuitpython-ssd1306")
        return 1
    
    # Test 1: Main I2C bus
    main_bus_ok = test_oled_on_main_bus()
    
    # Test 2: Through multiplexer
    mux_ok = test_oled_through_multiplexer()
    
    # Summary
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if main_bus_ok:
        print("[OK] OLED working on MAIN I2C BUS")
        print("     Your OLED is NOT behind the multiplexer")
        print("     It's connected directly to the Pi's I2C pins")
    elif mux_ok:
        print("[OK] OLED working through MULTIPLEXER")
        print("     Update your code to select the correct channel")
    else:
        print("[X] OLED NOT DETECTED")
        print("\nTroubleshooting:")
        print("  1. Check power: OLED VCC to 3.3V, GND to GND")
        print("  2. Check I2C connections: SDA and SCL")
        print("  3. If using multiplexer, verify channel connections")
        print("  4. Try running: i2cdetect -y 1")
        print("  5. Check if OLED address is 0x3C or 0x3D")
        print("     (some OLEDs have a solder jumper to change address)")
    
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
