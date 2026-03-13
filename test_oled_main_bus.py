#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test OLED on main I2C bus (not through multiplexer)
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.screens import oled_mux

def main():
    print("=" * 70)
    print("  Testing OLED on Main I2C Bus (Direct Connection)")
    print("=" * 70)
    print()
    
    # Initialize OLED on main bus (NOT through multiplexer)
    print("[TEST] Initializing OLED on main I2C bus...")
    if oled_mux.initialize_display(use_multiplexer=False):
        print("\n[SUCCESS] OLED initialized on main bus!\n")
        
        # Test display updates
        oled_mux.update_display(
            header="Main Bus",
            text="OLED working without MUX!"
        )
        time.sleep(2)
        
        oled_mux.update_display(
            header="Status",
            text="All sensors OK",
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
        print("Check wiring and run: i2cdetect -y 1")
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
