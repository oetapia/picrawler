#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Navigation System for PiCrawler

This module demonstrates autonomous navigation using the refactored components
from components/. It uses the same navigation logic as manual_control/scripts/tracking.py
but in a cleaner, more modular structure.

This serves as a foundation for future ML-based autonomous navigation.
"""

import time
import random
import atexit
from threading import Event

# Note: Requires 'pip install -e .' from project root for components imports
from picrawler import Picrawler
from robot_hat import TTS, Pin, utils

# Import refactored components
from components.navigation import SmoothMotionController, compute_balance_pose, ObstacleHandler
from components.navigation.balance import get_neutral_pose, get_compact_pose
from components.navigation_state import RobotState, StuckDetector
from components.sensors.sensor_fusion import SensorHub
from components.sensors.tilt_aware_tof import ReadingType
from components.screens.nav_display import NavDisplay
from components.utils import safe_print, ICONS
from components.utils.config import (
    SPEED_NORMAL, SPEED_MIN, SPEED_CAUTION,
    DISTANCE_WARNING, DISTANCE_SAFE, DISTANCE_DANGER,
    TILT_CAUTION, TILT_DANGER, BALANCE_DEADZONE, BALANCE_SPEED,
    DISTANCE_SENSOR_TYPE,
    # Timing parameters
    MCU_RESET_DELAY, BALANCE_SETTLING_TIME, DISPLAY_UPDATE_INTERVAL,
    STATUS_REPORT_INTERVAL, MAIN_LOOP_DELAY, ACTION_SETTLE_DELAY,
    BACKUP_SETTLE_DELAY,
    # Rear sensor thresholds
    REAR_DISTANCE_THRESHOLD, REAR_DISTANCE_WARNING
)


class AutonomousNavigator:
    """
    Autonomous navigation system using refactored components.
    
    This class orchestrates all the components to provide autonomous
    exploration behavior. It's designed to be extended with ML capabilities
    in the future.
    """
    
    def __init__(self, distance_sensor_type=DISTANCE_SENSOR_TYPE):
        """
        Initialize autonomous navigator.
        
        Args:
            distance_sensor_type: Type of distance sensor to use
        """
        safe_print(f"\n{ICONS['robot']} Initializing Autonomous Navigator...")
        
        # Reset MCU/GPIO for clean state
        safe_print("Resetting MCU...")
        utils.reset_mcu()
        time.sleep(MCU_RESET_DELAY)
        
        # Core hardware
        self.crawler = Picrawler()
        self.tts = TTS()
        
        # Initialize refactored components
        self.motion = SmoothMotionController()
        self.sensors = SensorHub(distance_sensor_type)
        
        # Configure obstacle handler based on sensor capabilities
        has_dual_sensors = getattr(self.sensors, 'has_dual_tof', False)
        self.obstacle_handler = ObstacleHandler(has_dual_sensors=has_dual_sensors)
        self.stuck_detector = StuckDetector()
        
        # Initialize OLED display for navigation status
        self.nav_display = NavDisplay(update_interval=DISPLAY_UPDATE_INTERVAL)
        self.nav_display.show_startup()
        
        # Statistics for floor vs obstacle tracking
        self.floor_readings_filtered = 0
        self.obstacle_readings_triggered = 0
        self.rear_floor_readings_filtered = 0
        self.rear_obstacle_readings_triggered = 0
        
        # State management
        self.state = RobotState.EXPLORING
        self.previous_state = RobotState.EXPLORING
        
        # Control flags
        self.running = False
        self.stop_event = Event()
        
        # Movement tracking for balance timing
        self.last_movement_time = 0
        self.last_movement_type = None
        
        # Statistics
        self.total_steps = 0
        self.start_time = time.time()
        
        # Setup RST button for graceful shutdown
        self._pins = []
        self._setup_shutdown_button()
        atexit.register(self._cleanup_gpio)
        
        self._print_initialization_status()
        safe_print(f"{ICONS['check']} Autonomous Navigator ready!\n")
    
    def _print_initialization_status(self):
        """Print status of all components."""
        sensor_status = self.sensors.get_sensor_status()
        safe_print(f"\n  Sensor Status:")
        safe_print(f"    Distance: {sensor_status['distance_sensor']}")
        safe_print(f"    Accelerometer: {sensor_status['accelerometer']}")
        safe_print(f"    Floor sensors: {sensor_status['floor_sensors']}")
    
    def announce(self, message):
        """Announce status via TTS."""
        safe_print(f"[EMOJI] {message}")
        try:
            self.tts.say(message)
        except Exception as e:
            safe_print(f"TTS Error: {e}")
    
    def change_state(self, new_state):
        """Change robot state."""
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            safe_print(f"State: {self.previous_state.value} -> {new_state.value}")
    
    # ========================================================================
    # BUTTON HANDLING - Return to startup menu
    # ========================================================================
    
    def _setup_shutdown_button(self):
        """Setup RST button for graceful shutdown."""
        try:
            self.shutdown_button = Pin("RST", Pin.IN, Pin.PULL_UP)
            self._pins.append(self.shutdown_button)
            self.shutdown_button.irq(
                trigger=Pin.IRQ_FALLING,
                handler=self._on_shutdown_pressed
            )
            safe_print(f"  RST button configured for graceful shutdown")
        except Exception as e:
            safe_print(f"  Warning: Could not setup RST button: {e}")
            self.shutdown_button = None
    
    def _on_shutdown_pressed(self, pin):
        """Handle RST button press for graceful shutdown."""
        # Only respond to button press (falling edge = pressed)
        if pin.value() == 0:
            safe_print(f"\n{ICONS['stop']} RST button pressed - shutting down...")
            self.announce("Shutting down")
            self.stop_event.set()
            self.running = False
    
    def _cleanup_gpio(self):
        """Release GPIO pins to prevent 'GPIO busy' errors on restart."""
        safe_print("Cleaning up GPIO pins...")
        for pin in self._pins:
            try:
                if hasattr(pin, 'close'):
                    pin.close()
                elif hasattr(pin, 'deinit'):
                    pin.deinit()
            except Exception as e:
                safe_print(f"  Warning: Could not close pin: {e}")
        self._pins.clear()
        safe_print("GPIO cleanup complete.")
    
    # ========================================================================
    # BALANCE MANAGEMENT
    # ========================================================================
    
    def apply_balance(self):
        """Apply dynamic balance correction based on tilt."""
        if not self.sensors.has_accelerometer():
            return
        
        # CRITICAL FIX: Skip balance if movement was very recent
        # This prevents awkward "backward shuffle" after forward movement
        time_since_movement = time.time() - self.last_movement_time
        if time_since_movement < BALANCE_SETTLING_TIME:
            return
        
        try:
            pitch, roll = self.sensors.get_tilt()
            max_tilt = max(abs(pitch), abs(roll))
            
            if max_tilt < BALANCE_DEADZONE:
                return
            
            pose = compute_balance_pose(pitch, roll)
            self.crawler.do_step(pose, BALANCE_SPEED)
            safe_print(f"{ICONS['tilt']} Balance: pitch={pitch:+.1f} deg roll={roll:+.1f} deg")
        except Exception as e:
            safe_print(f"Balance error: {e}")
    
    def update_speed_from_tilt(self):
        """Adjust speed based on tilt angle."""
        if not self.sensors.has_accelerometer():
            return
        
        pitch, roll = self.sensors.get_tilt()
        max_tilt = max(abs(pitch), abs(roll))
        
        if max_tilt > TILT_DANGER:
            self.motion.set_target_speed(SPEED_MIN)
            if self.state not in [RobotState.EMERGENCY, RobotState.TILT_CORRECTION]:
                self.change_state(RobotState.TILT_CORRECTION)
                safe_print(f"{ICONS['warning']} Danger tilt: {max_tilt:.1f} deg")
        
        elif max_tilt > TILT_CAUTION:
            self.motion.set_target_speed(SPEED_CAUTION)
            if self.state == RobotState.EXPLORING:
                self.change_state(RobotState.TILT_CORRECTION)
        
        else:
            if self.state == RobotState.TILT_CORRECTION:
                self.change_state(RobotState.EXPLORING)
            if self.state == RobotState.EXPLORING:
                self.motion.set_target_speed(SPEED_NORMAL)
    
    # ========================================================================
    # MOVEMENT EXECUTION
    # ========================================================================
    
    def move_forward(self):
        """Execute smooth forward movement."""
        speed = self.motion.update()
        safe_print(f"{ICONS['forward']} Forward (speed={speed})")
        self.crawler.do_action('forward', 1, speed)
        
        # Track movement for balance timing
        self.last_movement_time = time.time()
        self.last_movement_type = 'forward'
        
        self.stuck_detector.record_successful_move()
        self.total_steps += 1
    
    def execute_obstacle_avoidance(self, distance):
        """
        Execute obstacle avoidance maneuver with tilt-aware rear sensor check.
        
        Uses tilt-aware rear sensor classification to avoid false obstacle
        detection when the robot tilts backward during backup maneuvers.
        
        Args:
            distance: Distance to obstacle in cm
        """
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.stuck_detector.record_obstacle()
        
        safe_print(f"{ICONS['obstacle']} Obstacle at {distance:.1f}cm")
        
        # Get recommended action from obstacle handler
        _, roll = self.sensors.get_tilt() if self.sensors.has_accelerometer() else (0, 0)
        action = self.obstacle_handler.decide_obstacle_action(
            distance,
            self.stuck_detector.consecutive_obstacles,
            roll
        )
        
        # Handle emergency
        if action['emergency']:
            self.motion.emergency_stop()
            self.announce("Emergency stop!")
        
        # Check rear sensor with tilt-awareness before backing up
        rear_is_safe, rear_classified = self.sensors.is_backward_safe_tilt_aware(threshold=REAR_DISTANCE_THRESHOLD)
        
        if rear_classified.reading_type == ReadingType.FLOOR:
            # Rear sensor seeing floor (tilted backward) - safe to back up
            self.rear_floor_readings_filtered += 1
            safe_print(f"{ICONS['tilt']} Rear floor reading filtered: {rear_classified.distance:.0f}cm @ pitch={rear_classified.pitch:.1f}deg")
        
        if not rear_is_safe:
            # Real obstacle behind - can't back up, just turn in place
            self.rear_obstacle_readings_triggered += 1
            safe_print(f"{ICONS['warning']} Rear obstacle at {rear_classified.distance:.0f}cm - turning in place")
            self.crawler.do_action(action['turn_direction'], action['turn_amount'] + 1, 
                                  self.motion.get_speed())
            time.sleep(BACKUP_SETTLE_DELAY)
            return
        
        # Execute backward movement (rear is clear or just floor reading)
        self.crawler.do_action('backward', action['backward_steps'], self.motion.get_speed())
        time.sleep(BACKUP_SETTLE_DELAY)
        
        # Execute turn
        self.crawler.do_action(action['turn_direction'], action['turn_amount'], 
                              self.motion.get_speed())
        time.sleep(ACTION_SETTLE_DELAY)
    
    def execute_floor_danger_avoidance(self, danger_type, suggested_action):
        """
        Execute floor danger avoidance maneuver.
        
        Args:
            danger_type: Type of floor danger
            suggested_action: Suggested action from analyzer
        """
        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.stuck_detector.record_floor_danger()
        
        safe_print(f"{ICONS['warning']} Floor danger: {danger_type}")
        self.announce(f"Edge detected!")
        
        # Get recommended action from obstacle handler
        distance = self.sensors.get_distance()
        action = self.obstacle_handler.decide_floor_danger_action(danger_type, distance)
        
        # Handle airborne emergency
        if action['emergency'] and action['action'] == 'compact':
            self.motion.emergency_stop()
            pose = get_compact_pose()
            self.crawler.do_step(pose, SPEED_MIN)
            time.sleep(ACTION_SETTLE_DELAY + 0.2)  # Extra time for emergency
            return
        
        # Execute primary action
        if action['action']:
            self.crawler.do_action(action['action'], action['steps'], 
                                  self.motion.get_speed())
            time.sleep(ACTION_SETTLE_DELAY)
        
        # Execute secondary action if provided
        if action['secondary_action']:
            self.crawler.do_action(action['secondary_action'], action['secondary_steps'],
                                  self.motion.get_speed())
            time.sleep(ACTION_SETTLE_DELAY)
    
    def execute_escape_pattern(self):
        """Execute escape pattern when stuck."""
        self.change_state(RobotState.STUCK)
        pattern = self.stuck_detector.get_escape_pattern()
        
        self.announce("Executing escape maneuver")
        safe_print(f"{ICONS['warning']} Stuck! Escape pattern: {pattern}")
        
        for action, steps in pattern:
            if self.stop_event.is_set():
                break
            self.crawler.do_action(action, steps, self.motion.get_speed())
            time.sleep(ACTION_SETTLE_DELAY)
        
        # Reset stuck detector
        self.stuck_detector.reset()
    
    # ========================================================================
    # MAIN NAVIGATION LOOP
    # ========================================================================
    
    def check_and_handle_sensors(self):
        """
        Check all sensors and handle any detected conditions.
        
        Uses tilt-aware distance classification to distinguish between
        floor readings and actual obstacles when the robot is tilted.
        
        Returns:
            bool: True if action was taken, False if clear to proceed
        """
        # 1. Check floor sensors (highest priority - IR edge detection)
        danger_type, suggested_action = self.sensors.check_floor_danger_debounced()
        if danger_type:
            self.execute_floor_danger_avoidance(danger_type, suggested_action)
            return True
        
        # 2. Check distance sensor with tilt-aware classification
        if self.sensors.has_distance_sensor():
            # Adjust threshold based on state
            threshold = DISTANCE_SAFE if self.state == RobotState.AVOIDING_OBSTACLE else DISTANCE_WARNING
            
            # Get classified distance reading (filters floor readings when tilted)
            should_avoid, classified = self.sensors.should_avoid_obstacle(threshold)
            
            # Update OLED display with detection info
            pitch, _ = self.sensors.get_tilt()
            
            if classified.reading_type == ReadingType.FLOOR:
                # Floor reading detected - skip obstacle avoidance
                self.floor_readings_filtered += 1
                self.nav_display.show_floor_detected(
                    classified.distance, 
                    classified.pitch,
                    classified.expected_floor_dist or 0
                )
                safe_print(f"{ICONS['tilt']} Floor reading filtered: {classified.distance:.0f}cm @ pitch={classified.pitch:.1f} deg (expected floor: {classified.expected_floor_dist:.0f}cm)")
                # Don't trigger avoidance - continue exploring
                
            elif should_avoid:
                # Real obstacle detected
                self.obstacle_readings_triggered += 1
                self.nav_display.show_obstacle_detected(
                    classified.distance,
                    classified.pitch,
                    "AVOID"
                )
                self.execute_obstacle_avoidance(classified.distance)
                return True
            
            else:
                # Clear path
                self.nav_display.show_clear(classified.distance, pitch)
        
        # 3. Check if stuck
        if self.stuck_detector.is_stuck():
            self.stuck_detector.increment_stuck_counter()
            if self.stuck_detector.should_execute_escape():
                self.execute_escape_pattern()
                return True
        
        return False
    
    def print_status(self):
        """Print current navigation status."""
        uptime = time.time() - self.start_time
        pitch, roll = self.sensors.get_tilt()
        
        safe_print(f"\n{ICONS['stats']} ===== Status =====")
        safe_print(f"  State: {self.state.value}")
        safe_print(f"  Uptime: {uptime:.1f}s")
        safe_print(f"  Steps: {self.total_steps}")
        safe_print(f"  Speed: {self.motion.get_speed()}")
        
        # Stuck detector status
        stuck_status = self.stuck_detector.get_status()
        safe_print(f"  Obstacles: {stuck_status['consecutive_obstacles']}")
        safe_print(f"  Floor dangers: {stuck_status['consecutive_floor_dangers']}")
        
        # Tilt-aware ToF statistics (front sensor)
        safe_print(f"  Front floor filtered: {self.floor_readings_filtered}")
        safe_print(f"  Front obstacles: {self.obstacle_readings_triggered}")
        # Rear sensor statistics
        safe_print(f"  Rear floor filtered: {self.rear_floor_readings_filtered}")
        safe_print(f"  Rear obstacles: {self.rear_obstacle_readings_triggered}")
        
        if self.sensors.has_accelerometer():
            safe_print(f"  Tilt: pitch={pitch:+.1f} deg roll={roll:+.1f} deg")
        
        # Update OLED with status
        self.nav_display.show_status(self.state.value, f"Steps: {self.total_steps}")
        
        safe_print("=" * 30 + "\n")
    
    def exploration_loop(self):
        """
        Main autonomous exploration loop.
        
        Orchestrates sensor checking, decision making, and movement execution.
        """
        safe_print(f"{ICONS['robot']} Starting autonomous exploration...\n")
        self.announce("Beginning autonomous navigation")
        
        last_status_time = time.time()
        
        while self.running and not self.stop_event.is_set():
            try:
                # Periodic status report
                if time.time() - last_status_time > STATUS_REPORT_INTERVAL:
                    self.print_status()
                    last_status_time = time.time()
                
                # Update speed based on tilt
                self.update_speed_from_tilt()
                
                # Check sensors and handle any detected conditions
                action_taken = self.check_and_handle_sensors()
                
                if action_taken:
                    # Action was taken, continue to next iteration
                    continue
                
                # No obstacles or dangers - proceed with exploration
                if self.state not in [RobotState.EXPLORING, RobotState.TILT_CORRECTION]:
                    self.change_state(RobotState.EXPLORING)
                
                # Move forward
                self.move_forward()
                
                # Apply balance correction
                self.apply_balance()
                
                # Random status announcements
                if random.randint(1, 150) == 1:
                    self.announce(random.choice([
                        "Exploring",
                        "All systems nominal",
                        "Navigation active",
                    ]))
                
                time.sleep(MAIN_LOOP_DELAY)
            
            except KeyboardInterrupt:
                safe_print(f"\n{ICONS['stop']} Manual stop")
                break
            
            except Exception as e:
                safe_print(f"Error in navigation loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start autonomous navigation."""
        self.running = True
        self.exploration_loop()
    
    def stop(self):
        """Stop navigation and print final stats."""
        safe_print(f"\n{ICONS['stop']} Stopping navigation...")
        self.running = False
        self.stop_event.set()
        
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['stats']} ===== Final Statistics =====")
        safe_print(f"  Runtime: {uptime:.1f}s")
        safe_print(f"  Total steps: {self.total_steps}")
        safe_print(f"  Final state: {self.state.value}")
        safe_print(f"  Front floor filtered: {self.floor_readings_filtered}")
        safe_print(f"  Front obstacles: {self.obstacle_readings_triggered}")
        safe_print(f"  Rear floor filtered: {self.rear_floor_readings_filtered}")
        safe_print(f"  Rear obstacles: {self.rear_obstacle_readings_triggered}")
        safe_print("=" * 40)
        
        # Show shutdown on OLED
        self.nav_display.close()
        
        # Return to compact pose for safe pickup
        safe_print(f"\n{ICONS['robot']} Moving to compact pose for safe pickup...")
        compact_pose = get_compact_pose()
        self.crawler.do_step(compact_pose, 40)
        time.sleep(0.5)  # Give time to settle
        safe_print(f"{ICONS['check']} Robot ready for pickup")
        
        # Close sensors
        self.sensors.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for autonomous navigation."""
    safe_print(f"\n{ICONS['robot']} PiCrawler Autonomous Navigation System")
    safe_print("=" * 50)
    safe_print("Using refactored components from components/")
    safe_print("Distance Sensor: {}".format(DISTANCE_SENSOR_TYPE or "None (IR only)"))
    safe_print("=" * 50 + "\n")
    
    navigator = AutonomousNavigator()
    
    try:
        navigator.start()
    except KeyboardInterrupt:
        safe_print(f"\n{ICONS['stop']} Keyboard interrupt")
    except Exception as e:
        safe_print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        navigator.stop()
        safe_print(f"\n{ICONS['check']} Shutdown complete\n")


if __name__ == '__main__':
    main()
