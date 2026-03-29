#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify OLED works through multiplexer
"""

import time
import sys

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.screens import oled_mux

def main():
    print("=" * 70)
    print("  Testing OLED Display Through Multiplexer")
    print("=" * 70)
    print()
    
    # Test 1: Initialize with auto-detection
    print("[TEST 1] Auto-detecting OLED on multiplexer channels...")
    if oled_mux.initialize_display(use_multiplexer=True, channel=None):
        print("\n[SUCCESS] OLED initialized successfully!\n")
        
        # Test 2: Display some messages
        print("[TEST 2] Testing display updates...")
        
        oled_mux.update_display(
            header="Test 1",
            text="OLED is working through MUX!"
        )
        time.sleep(2)
        
        oled_mux.update_display(
            header="Test 2",
            text="Sensors: VL53L0X x2 MPU6050",
            y_start=12,
            line_height=10
        )
        time.sleep(2)
        
        oled_mux.update_display(
            header="Test 3",
            text="Icon test",
            icon='rectangle'
        )
        time.sleep(2)
        
        # Clean up
        oled_mux.close_display()
        
        print("\n[SUCCESS] All tests passed!")
        print("=" * 70)
        return 0
    else:
        print("\n[FAILED] Could not initialize OLED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        oled_mux.close_display()
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
