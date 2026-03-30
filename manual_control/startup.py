#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PiCrawler Startup Script

This script runs on boot (via systemd) and provides a menu to select
between manual control (REST API) and autonomous navigation.

Button controls:
- USR button (SW): Start manual keyboard control (restapi3.py)
- RST button: Start autonomous navigation (autonomous_navigator.py)
"""

import os
import sys
import subprocess
import atexit
import time

from robot_hat.utils import reset_mcu
from robot_hat import Music, TTS, Pin

# ============================================================================
# GPIO INITIALIZATION - Must happen BEFORE any Pin objects are created
# ============================================================================

print("Resetting MCU/GPIO for clean state...")
reset_mcu()
time.sleep(0.1)  # Brief delay for MCU reset to complete

# ============================================================================
# COMPONENT IMPORTS (after GPIO reset)
# ============================================================================

# Import from the 'components' package
# Note: Requires 'pip install -e .' from project root
from components.screens import oled
from components.sensors import battery_status
from components.sounds import library

# ============================================================================
# GPIO PIN SETUP (after reset, with cleanup registration)
# ============================================================================

# Track pins for cleanup
_pins = []

def _cleanup_gpio():
    """Release GPIO pins on exit to prevent 'GPIO busy' errors on restart."""
    print("Cleaning up GPIO pins...")
    for pin in _pins:
        try:
            if hasattr(pin, 'close'):
                pin.close()
            elif hasattr(pin, 'deinit'):
                pin.deinit()
        except Exception as e:
            print(f"  Warning: Could not close pin: {e}")
    print("GPIO cleanup complete.")

# Register cleanup handler
atexit.register(_cleanup_gpio)

# Initialize button pins (after reset_mcu)
btn1 = Pin("SW", Pin.IN, Pin.PULL_UP)   # USR button - manual control
btn2 = Pin("RST", Pin.IN, Pin.PULL_UP)  # RST button - autonomous mode
_pins.extend([btn1, btn2])

# Initialize audio
tts = TTS()
music = Music()

print("Components initialized.")

# ============================================================================
# STATE VARIABLES
# ============================================================================

robot_hat_on = False
service_started = False
last_press_time = 0
debounce_time = 200  # milliseconds

# ============================================================================
# FUNCTIONS
# ============================================================================

def check_robot_hat_status():
    """Check if the robot HAT is on by monitoring the battery voltage."""
    global robot_hat_on

    status, voltage = battery_status.get_battery_state()
    if status.startswith("Error") or voltage is None:
        print("Robot HAT is off or disconnected.")
        return False
    else:
        print("Robot HAT is on.")
        robot_hat_on = True
        return True


def button_handler(pin):
    """Handle button press events with debouncing."""
    global last_press_time, service_started
    current_time = time.time() * 1000  # Get current time in milliseconds

    # Debounce logic: Ignore button presses within the debounce time
    if (current_time - last_press_time) > debounce_time:
        if pin.value() == 0 and not service_started:  # Button pressed and service not started
            tts.say("Starting service")

            if pin == btn1:
                print("Button 1 pressed")
                tts.say("Starting manual control")
                oled.update_display(header="Starting...", text='Keyboard control')
                run_script('/home/pi/picrawler/manual_control/scripts/restapi3.py')

            elif pin == btn2:
                print("Button 2 pressed")
                tts.say("Starting automated control")
                oled.update_display(header="Starting...", text='Autopilot tracking')
                run_script('/home/pi/picrawler/self_aware/autonomous_navigator.py')

            service_started = True

        elif pin.value() == 1:  # Button released
            print("Button released")

        last_press_time = current_time


def run_script(script_path):
    """
    Run a Python script as a subprocess using the project's virtual environment.
    
    Uses the same Python interpreter that's running this script (sys.executable),
    which will be the venv Python when started via systemd or setup scripts.
    """
    env = os.environ.copy()
    project_root = '/home/pi/picrawler'
    venv_path = os.path.join(project_root, 'venv')

    # Set virtual environment paths
    env['VIRTUAL_ENV'] = venv_path
    env['PATH'] = os.path.join(venv_path, 'bin') + ':' + env.get('PATH', '')

    # Use the same Python that's running this script
    python_executable = sys.executable

    print(f"Running: {script_path}")
    print(f"Python: {python_executable}")

    result = subprocess.run(
        [python_executable, script_path],
        env=env,
        cwd=project_root,
        check=True,
        text=True,
        capture_output=True
    )
    print(f"Executed {script_path} with output: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    return result


def main():
    """Main entry point."""
    global robot_hat_on

    check_robot_hat_status()

    if robot_hat_on:
        print("Starting up")
        music.sound_play_threading(library.intro)
        battery_level, battery_voltage = battery_status.get_battery_state()
        time.sleep(2)
        tts.say(f"Battery level {battery_level} running at {battery_voltage:.1f}")
        oled.update_display(header="Battery", text=f'{battery_level} {battery_voltage:.1f}')
        tts.say("Choose function")
        oled.update_display(header="Function", text='USR: Keyboard control, RST: Autopilot')

        # Attach interrupts to buttons
        btn1.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda pin: button_handler(btn1))
        btn2.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda pin: button_handler(btn2))

        # Keep running until interrupted
        try:
            while True:
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nShutdown requested...")

    else:
        print("Robot hat off")


if __name__ == '__main__':
    main()
