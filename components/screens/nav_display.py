#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Navigation Display Module for OLED Screen

Provides real-time navigation status display on the OLED screen,
showing detected objects, distances, pitch angles, and current actions.
"""

import time
import os
from threading import Thread, Event, Lock
from typing import Optional

# Font path for OLED display
FONT_PATH = os.path.join(os.path.dirname(__file__), 'font5x8.bin')


class NavDisplay:
    """
    Navigation status display for OLED screen.
    
    Shows real-time information about:
    - Detected object type (obstacle, floor, clear)
    - Distance readings
    - Pitch/tilt angles
    - Current navigation action
    
    Uses non-blocking updates to avoid slowing down navigation loop.
    """
    
    def __init__(self, update_interval: float = 0.2):
        """
        Initialize navigation display.
        
        Args:
            update_interval: Minimum time between display updates (seconds)
        """
        self.display = None
        self.initialized = False
        self.update_interval = update_interval
        self.last_update_time = 0
        self.lock = Lock()
        
        # Current display state
        self.current_state = {
            'object_type': 'INIT',
            'distance': 0.0,
            'pitch': 0.0,
            'action': 'Starting',
            'state': 'INIT'
        }
        
        # Try to initialize display
        self._init_display()
    
    def _init_display(self):
        """Initialize the OLED display."""
        try:
            import board
            import busio
            import adafruit_ssd1306
            
            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
            self.display.fill(0)
            self.display.show()
            self.initialized = True
            print("[NavDisplay] OLED initialized successfully")
        except Exception as e:
            print(f"[NavDisplay] OLED init failed: {e}")
            self.initialized = False
    
    def _should_update(self) -> bool:
        """Check if enough time has passed for an update."""
        now = time.time()
        if now - self.last_update_time >= self.update_interval:
            self.last_update_time = now
            return True
        return False
    
    def show_detection(self, object_type: str, distance: float, 
                       pitch: float, action: str = ""):
        """
        Display detection information.
        
        Args:
            object_type: Type of object detected (OBSTACLE, FLOOR, CLEAR, etc.)
            distance: Distance in cm
            pitch: Current pitch angle in degrees
            action: Current action being taken
        """
        if not self.initialized:
            return
        
        with self.lock:
            self.current_state.update({
                'object_type': object_type,
                'distance': distance,
                'pitch': pitch,
                'action': action
            })
        
        if self._should_update():
            self._render_detection()
    
    def show_status(self, state: str, message: str = ""):
        """
        Display general status.
        
        Args:
            state: Current robot state
            message: Optional status message
        """
        if not self.initialized:
            return
        
        with self.lock:
            self.current_state['state'] = state
            if message:
                self.current_state['action'] = message
        
        if self._should_update():
            self._render_status()
    
    def _render_detection(self):
        """Render detection information to display."""
        if not self.display:
            return
        
        try:
            self.display.fill(0)
            
            state = self.current_state
            obj_type = state['object_type']
            distance = state['distance']
            pitch = state['pitch']
            action = state['action']
            
            # Line 1: Header with object type
            header = f"NAV: {obj_type}"
            self.display.text(header[:16], 0, 0, 1, font_name=FONT_PATH)
            
            # Line 2: Distance
            dist_text = f"Dist: {distance:.0f}cm"
            self.display.text(dist_text[:16], 0, 12, 1, font_name=FONT_PATH)
            
            # Line 3: Pitch angle
            pitch_text = f"Pitch: {pitch:+.1f}deg"
            self.display.text(pitch_text[:16], 0, 24, 1, font_name=FONT_PATH)
            
            # Line 4: Current action
            if action:
                action_text = f"Act: {action}"
                self.display.text(action_text[:16], 0, 36, 1, font_name=FONT_PATH)
            
            # Line 5: Visual indicator bar for distance
            bar_width = min(int(distance / 100 * 100), 100)
            if obj_type == "OBSTACLE":
                # Draw filled bar for obstacles
                for x in range(bar_width):
                    self.display.pixel(x + 14, 52, 1)
                    self.display.pixel(x + 14, 53, 1)
                    self.display.pixel(x + 14, 54, 1)
            elif obj_type == "FLOOR":
                # Draw dashed bar for floor readings
                for x in range(0, bar_width, 4):
                    self.display.pixel(x + 14, 53, 1)
            else:
                # Draw thin bar for clear
                for x in range(bar_width):
                    self.display.pixel(x + 14, 53, 1)
            
            self.display.show()
        except Exception as e:
            print(f"[NavDisplay] Render error: {e}")
    
    def _render_status(self):
        """Render general status to display."""
        if not self.display:
            return
        
        try:
            self.display.fill(0)
            
            state = self.current_state
            robot_state = state.get('state', 'UNKNOWN')
            action = state.get('action', '')
            
            # Line 1: Header
            self.display.text("NAV STATUS", 0, 0, 1, font_name=FONT_PATH)
            
            # Line 2: Robot state
            state_text = f"State: {robot_state}"
            self.display.text(state_text[:16], 0, 16, 1, font_name=FONT_PATH)
            
            # Line 3-4: Action/message
            if action:
                # Wrap long messages
                if len(action) > 16:
                    self.display.text(action[:16], 0, 32, 1, font_name=FONT_PATH)
                    self.display.text(action[16:32], 0, 44, 1, font_name=FONT_PATH)
                else:
                    self.display.text(action, 0, 32, 1, font_name=FONT_PATH)
            
            self.display.show()
        except Exception as e:
            print(f"[NavDisplay] Status render error: {e}")
    
    def show_floor_detected(self, distance: float, pitch: float, expected_floor: float):
        """
        Display floor detection (false positive filtered).
        
        Args:
            distance: Measured distance in cm
            pitch: Current pitch angle
            expected_floor: Calculated expected floor distance
        """
        self.show_detection(
            object_type="FLOOR(skip)",
            distance=distance,
            pitch=pitch,
            action=f"Exp:{expected_floor:.0f}cm"
        )
    
    def show_obstacle_detected(self, distance: float, pitch: float, action: str = "AVOID"):
        """
        Display obstacle detection.
        
        Args:
            distance: Distance to obstacle in cm
            pitch: Current pitch angle
            action: Action being taken
        """
        self.show_detection(
            object_type="OBSTACLE",
            distance=distance,
            pitch=pitch,
            action=action
        )
    
    def show_clear(self, distance: float, pitch: float):
        """
        Display clear path.
        
        Args:
            distance: Distance reading in cm
            pitch: Current pitch angle
        """
        self.show_detection(
            object_type="CLEAR",
            distance=distance,
            pitch=pitch,
            action="Forward"
        )
    
    def show_startup(self):
        """Display startup message."""
        if not self.initialized:
            return
        
        try:
            self.display.fill(0)
            self.display.text("PiCrawler NAV", 0, 0, 1, font_name=FONT_PATH)
            self.display.text("Initializing...", 0, 20, 1, font_name=FONT_PATH)
            self.display.text("Tilt-Aware ToF", 0, 36, 1, font_name=FONT_PATH)
            self.display.show()
        except Exception as e:
            print(f"[NavDisplay] Startup render error: {e}")
    
    def show_shutdown(self):
        """Display shutdown message."""
        if not self.initialized:
            return
        
        try:
            self.display.fill(0)
            self.display.text("PiCrawler NAV", 0, 0, 1, font_name=FONT_PATH)
            self.display.text("Shutting down", 0, 20, 1, font_name=FONT_PATH)
            self.display.text("Safe to pickup", 0, 36, 1, font_name=FONT_PATH)
            self.display.show()
        except Exception as e:
            print(f"[NavDisplay] Shutdown render error: {e}")
    
    def clear(self):
        """Clear the display."""
        if not self.initialized or not self.display:
            return
        
        try:
            self.display.fill(0)
            self.display.show()
        except Exception:
            pass
    
    def close(self):
        """Close the display."""
        self.show_shutdown()
        time.sleep(1)
        self.clear()


# ============================================================================
# TESTING
# ============================================================================

def test_display():
    """Test the navigation display."""
    print("Testing NavDisplay")
    print("=" * 40)
    
    nav = NavDisplay()
    
    if not nav.initialized:
        print("Display not available - running in simulation mode")
        return
    
    # Test startup
    nav.show_startup()
    time.sleep(2)
    
    # Test obstacle detection
    print("Showing obstacle...")
    nav.show_obstacle_detected(25.0, 5.0, "BACKWARD")
    time.sleep(2)
    
    # Test floor detection
    print("Showing floor (filtered)...")
    nav.show_floor_detected(30.0, 15.0, 31.0)
    time.sleep(2)
    
    # Test clear
    print("Showing clear...")
    nav.show_clear(150.0, 2.0)
    time.sleep(2)
    
    # Test status
    print("Showing status...")
    nav.show_status("EXPLORING", "All systems OK")
    time.sleep(2)
    
    # Shutdown
    nav.close()
    print("Test complete!")


if __name__ == "__main__":
    test_display()
