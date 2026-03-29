#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED Display Diagnostic Tool V2 - Improved Detection

Fixes I2C bus contention and detection issues.
Tests OLED displays on both main I2C bus and through PCA9548A multiplexer.

Improvements over V1:
- Proper I2C bus management and cleanup
- Single I2C connection strategy
- I2C bus reset capability
- Better error handling and diagnostics

Usage:
    python3 oled_diagnostic_v2.py
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
    from PIL import Image, ImageDraw, ImageFont
    HAS_OLED = True
except ImportError as e:
    HAS_OLED = False
    print(f"[!] OLED libraries not installed: {e}")
    print("    Install with: pip install adafruit-circuitpython-ssd1306 pillow")


def reset_i2c_bus():
    """Attempt to reset the I2C bus by toggling GPIO pins"""
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        # SCL = GPIO 3, SDA = GPIO 2
        GPIO.setup(3, GPIO.OUT)
        GPIO.setup(2, GPIO.OUT)
        
        # Toggle pins to reset bus
        for _ in range(5):
            GPIO.output(3, GPIO.LOW)
            GPIO.output(2, GPIO.LOW)
            time.sleep(0.01)
            GPIO.output(3, GPIO.HIGH)
            GPIO.output(2, GPIO.HIGH)
            time.sleep(0.01)
        
        GPIO.cleanup()
        print("[*] I2C bus reset completed")
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"[!] Could not reset I2C bus: {e}")
        return False


def scan_i2c_bus(bus_number=1):
    """Scan I2C bus for devices using smbus"""
    if not HAS_SMBUS:
        return []
    
    devices = []
    bus = None
    try:
        bus = smbus.SMBus(bus_number)
        for addr in range(0x03, 0x78):
            try:
                bus.read_byte(addr)
                devices.append(addr)
            except OSError:
                pass
    except Exception as e:
        print(f"[X] Error scanning I2C bus: {e}")
    finally:
        if bus:
            try:
                bus.close()
            except:
                pass
    
    return devices


def test_oled_simple_detection():
    """Simple OLED detection test - just check if device responds"""
    print("\n[PRE-TEST] Simple I2C Device Detection")
    print("-" * 60)
    
    if not HAS_SMBUS:
        print("[X] smbus not available")
        return False
    
    devices = scan_i2c_bus()
    print(f"I2C devices found on bus 1: {[hex(d) for d in devices]}")
    
    # Check for common OLED addresses
    oled_addresses = [0x3C, 0x3D]
    found = [addr for addr in oled_addresses if addr in devices]
    
    if found:
        print(f"[OK] Device(s) responding at OLED address(es): {[hex(a) for a in found]}")
        return True
    else:
        print("[X] No device responding at typical OLED addresses (0x3C, 0x3D)")
        return False


def test_oled_initialization(addr=0x3C, width=128, height=64):
    """Test OLED initialization with a single I2C connection"""
    print(f"\n[TEST] Attempting OLED initialization at {hex(addr)} ({width}x{height})")
    
    if not HAS_OLED:
        print("[X] OLED libraries not installed")
        return False
    
    i2c = None
    display = None
    
    try:
        # Create I2C connection
        print("  - Creating I2C connection...")
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Wait for I2C lock
        timeout = time.time() + 2.0
        while not i2c.try_lock() and time.time() < timeout:
            time.sleep(0.01)
        
        if not i2c.try_lock():
            print("  [X] Could not acquire I2C lock")
            return False
        
        # Scan for devices using busio
        devices = i2c.scan()
        i2c.unlock()
        print(f"  - busio I2C scan found: {[hex(d) for d in devices]}")
        
        if addr not in devices:
            print(f"  [X] Address {hex(addr)} not found in busio scan")
            return False
        
        # Try to initialize display
        print("  - Initializing SSD1306 driver...")
        display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)
        
        # Test display by drawing something
        print("  - Testing display output...")
        display.fill(0)
        display.text('OLED Test', 0, 0, 1)
        display.text(f'{width}x{height}', 0, 10, 1)
        display.text('Success!', 0, 20, 1)
        display.show()
        
        print(f"[OK] OLED at {hex(addr)} working! ({width}x{height})")
        time.sleep(2)
        
        # Clear display
        display.fill(0)
        display.show()
        
        return True
        
    except Exception as e:
        print(f"  [X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if display:
            try:
                display.fill(0)
                display.show()
            except:
                pass
        if i2c:
            try:
                if i2c.try_lock():
                    i2c.unlock()
                i2c.deinit()
            except:
                pass


def test_all_oled_configurations():
    """Test all common OLED configurations"""
    print("\n[TEST SUITE] Testing All OLED Configurations")
    print("=" * 60)
    
    # Test configurations: (address, width, height)
    configs = [
        (0x3C, 128, 64, "Most common: 0x3C, 128x64"),
        (0x3C, 128, 32, "Alternative: 0x3C, 128x32"),
        (0x3D, 128, 64, "Alternative: 0x3D, 128x64"),
        (0x3D, 128, 32, "Alternative: 0x3D, 128x32"),
    ]
    
    for addr, width, height, desc in configs:
        print(f"\n{desc}")
        print("-" * 60)
        if test_oled_initialization(addr, width, height):
            print(f"\n[SUCCESS] OLED found and working!")
            print(f"Configuration: Address={hex(addr)}, Size={width}x{height}")
            return True
        time.sleep(0.5)  # Small delay between tests
    
    return False


def test_oled_through_multiplexer(mux_addr=0x70):
    """Test OLED through PCA9548A multiplexer"""
    print("\n[TEST] Checking OLED through PCA9548A multiplexer")
    print("=" * 60)
    
    if not HAS_SMBUS:
        print("[X] smbus not available")
        return False
    
    bus = None
    try:
        bus = smbus.SMBus(1)
        
        # Check if multiplexer exists
        try:
            bus.read_byte(mux_addr)
            print(f"[OK] PCA9548A found at {hex(mux_addr)}")
        except OSError:
            print(f"[X] PCA9548A not found at {hex(mux_addr)}")
            return False
        
        # Test each channel
        for channel in range(8):
            control_byte = 1 << channel
            bus.write_byte(mux_addr, control_byte)
            time.sleep(0.05)
            
            # Scan this channel
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
                
                # Check for OLED
                oled_addrs = [0x3C, 0x3D]
                found_oled = [a for a in oled_addrs if a in devices]
                
                if found_oled:
                    print(f"  Possible OLED at: {[hex(a) for a in found_oled]}")
                    
                    # Close smbus before trying with busio
                    bus.close()
                    bus = None
                    
                    # Keep channel selected and test
                    temp_bus = smbus.SMBus(1)
                    temp_bus.write_byte(mux_addr, control_byte)
                    temp_bus.close()
                    time.sleep(0.1)
                    
                    # Test each found OLED address
                    for oled_addr in found_oled:
                        for width, height in [(128, 64), (128, 32)]:
                            if test_oled_initialization(oled_addr, width, height):
                                print(f"\n[SUCCESS] OLED found on multiplexer channel {channel}!")
                                return True
                    
                    # Reopen bus for next iteration
                    bus = smbus.SMBus(1)
        
        return False
        
    except Exception as e:
        print(f"[X] Error: {e}")
        return False
    
    finally:
        if bus:
            try:
                # Disable all channels
                bus.write_byte(mux_addr, 0x00)
                bus.close()
            except:
                pass


def main():
    print("=" * 60)
    print("  OLED Display Diagnostic Tool V2")
    print("=" * 60)
    
    if not HAS_SMBUS:
        print("\n[X] smbus module required but not found")
        print("This module should be pre-installed on Raspberry Pi OS")
        return 1
    
    if not HAS_OLED:
        print("\n[X] OLED libraries not installed")
        print("Install with:")
        print("  pip install adafruit-circuitpython-ssd1306 pillow")
        return 1
    
    # Pre-test: Simple detection
    detected = test_oled_simple_detection()
    
    if not detected:
        print("\n[*] Attempting I2C bus reset...")
        reset_i2c_bus()
        detected = test_oled_simple_detection()
        
        if not detected:
            print("\n[X] No device detected at OLED addresses")
            print("\nTroubleshooting:")
            print("  1. Check wiring:")
            print("     - VCC to 3.3V (not 5V for most OLEDs)")
            print("     - GND to GND")
            print("     - SDA to GPIO 2 (Pin 3)")
            print("     - SCL to GPIO 3 (Pin 5)")
            print("  2. Run: i2cdetect -y 1")
            print("  3. Check if OLED requires 5V power")
            print("  4. Verify OLED is SSD1306 compatible")
            return 1
    
    # Test 1: Direct connection
    print("\n" + "=" * 60)
    print(" MAIN TEST: Direct I2C Connection")
    print("=" * 60)
    
    main_bus_ok = test_all_oled_configurations()
    
    # Test 2: Through multiplexer (if main bus failed)
    mux_ok = False
    if not main_bus_ok:
        print("\n" + "=" * 60)
        print(" ALTERNATIVE TEST: Through Multiplexer")
        print("=" * 60)
        mux_ok = test_oled_through_multiplexer()
    
    # Summary
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if main_bus_ok:
        print("[OK] [EMOJI] OLED working on MAIN I2C BUS")
        print("     Your OLED is connected directly to the Pi's I2C pins")
        print("     It is NOT behind a multiplexer")
    elif mux_ok:
        print("[OK] [EMOJI] OLED working through MULTIPLEXER")
        print("     Update your code to select the correct multiplexer channel")
    else:
        print("[X] [EMOJI] OLED NOT DETECTED")
        print("\nPossible issues:")
        print("  * Wiring problem (check SDA, SCL, VCC, GND)")
        print("  * Wrong I2C address (try 0x3C and 0x3D)")
        print("  * Wrong display resolution (try 128x64 and 128x32)")
        print("  * Incompatible OLED chip (needs SSD1306)")
        print("  * I2C bus speed issue (try adding dtparam=i2c_arm_baudrate=50000)")
        print("  * Power issue (some OLEDs need 5V, most need 3.3V)")
    
    print("=" * 60)
    return 0 if (main_bus_ok or mux_ok) else 1


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
