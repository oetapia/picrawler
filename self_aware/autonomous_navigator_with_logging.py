#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Navigation System with Data Logging

Extended version of autonomous_navigator.py that logs sensor data and actions
for machine learning training data collection. Optionally captures photos for
vision-based ML models.

Usage:
    # With logging enabled (10 Hz)
    python3 self_aware/autonomous_navigator_with_logging.py --log
    
    # With custom log rate
    python3 self_aware/autonomous_navigator_with_logging.py --log --log-rate 20
    
    # With photo capture for vision ML (2 Hz, 320x240)
    python3 self_aware/autonomous_navigator_with_logging.py --log --photos
    
    # Custom photo settings
    python3 self_aware/autonomous_navigator_with_logging.py --log --photos --photo-rate 1.5
    
    # Custom log directory
    python3 self_aware/autonomous_navigator_with_logging.py --log --log-dir my_logs
"""

import os
import sys
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.sensors import accelerometer
from components.utils import safe_print, ICONS

# Import base autonomous navigator
from self_aware.autonomous_navigator import AutonomousNavigator

# Import data loggers
from self_aware.data_logger import DataLogger, ThrottledLogger
from self_aware.data_logger_with_photos import DataLoggerWithPhotos


class AutonomousNavigatorWithLogging(AutonomousNavigator):
    """
    Autonomous navigation system with integrated data logging.
    
    Extends AutonomousNavigator to log sensor readings and actions
    for ML training data collection. Optionally captures photos for
    vision-based path detection models.
    """
    
    def __init__(self, distance_sensor_type=None, 
                 enable_logging=False, log_rate_hz=10, log_dir=None,
                 enable_photos=False, photo_rate_hz=2.0, photo_resolution=(320, 240)):
        """
        Initialize autonomous navigator with optional logging.
        
        Args:
            distance_sensor_type: Type of distance sensor to use
            enable_logging: Enable data logging for ML
            log_rate_hz: Logging sample rate (Hz)
            log_dir: Directory to save log files (default: self_aware/logs)
            enable_photos: Enable photo capture (requires enable_logging=True)
            photo_rate_hz: Photo capture rate (Hz, default: 2.0)
            photo_resolution: Photo size tuple (width, height, default: 320x240)
        """
        # Initialize base class
        super().__init__(distance_sensor_type)
        
        # Data logging setup
        self.enable_logging = enable_logging
        self.enable_photos = enable_photos
        self.logger = None
        
        if enable_logging:
            if enable_photos:
                # Use photo-enabled logger
                safe_print(f"{ICONS['camera']} Initializing photo capture at {photo_rate_hz} Hz...")
                self.logger = DataLoggerWithPhotos(
                    log_dir=log_dir or "self_aware/logs",
                    format="csv",
                    buffer_size=100,
                    capture_photos=True,
                    photo_rate_hz=photo_rate_hz,
                    photo_resolution=photo_resolution
                )
                # Start photo capture
                self.logger.start_photo_capture()
                safe_print(f"{ICONS['check']} Photo capture enabled ({photo_resolution[0]}x{photo_resolution[1]})")
            else:
                # Use regular throttled logger
                base_logger = DataLogger(log_dir=log_dir, format="csv", buffer_size=100)
                self.logger = ThrottledLogger(base_logger, sample_rate_hz=log_rate_hz)
                safe_print(f"{ICONS['check']} Data logging enabled at {log_rate_hz} Hz")
    
    # ========================================================================
    # DATA LOGGING
    # ========================================================================
    
    def log_current_state(self, action='none', steps=0):
        """
        Log current sensor readings and action.
        
        Args:
            action: Action being taken
            steps: Number of steps for action
        """
        if not self.enable_logging or self.logger is None:
            return
        
        try:
            # Gather sensor data
            distance = self.sensors.get_distance()
            pitch, roll = self.sensors.get_tilt()
            floor_sensors = self.sensors.get_floor_sensors()
            
            # Get raw accelerometer data
            accel_x, accel_y, accel_z = 0.0, 0.0, 0.0
            gyro_x, gyro_y, gyro_z = 0.0, 0.0, 0.0
            if self.sensors.has_accelerometer():
                try:
                    accel_x, accel_y, accel_z = accelerometer.read_accel()
                    gyro_x, gyro_y, gyro_z = accelerometer.read_gyro()
                except:
                    pass
            
            sensor_data = {
                'distance': distance,
                'front_distance': distance,  # For photo logger compatibility
                'pitch': pitch,
                'roll': roll,
                'accel_x': accel_x,
                'accel_y': accel_y,
                'accel_z': accel_z,
                'gyro_x': gyro_x,
                'gyro_y': gyro_y,
                'gyro_z': gyro_z,
                'floor_fl': floor_sensors['fl'],
                'floor_fr': floor_sensors['fr'],
                'floor_bl': floor_sensors['bl'],
                'floor_br': floor_sensors['br'],
            }
            
            # Gather context data
            stuck_status = self.stuck_detector.get_status()
            context_data = {
                'state': self.state.value,
                'previous_state': self.previous_state.value,
                'current_speed': self.motion.get_speed(),
                'consecutive_obstacles': stuck_status['consecutive_obstacles'],
                'consecutive_floor_dangers': stuck_status['consecutive_floor_dangers'],
                'stuck_counter': stuck_status['stuck_counter'],
            }
            
            # Gather action data
            action_data = {
                'action': action,
                'steps': steps,
                'speed': self.motion.get_speed(),
            }
            
            # Log entry (with or without photos)
            if self.enable_photos:
                self.logger.log_entry_with_photo(sensor_data, action_data, context_data)
            else:
                self.logger.log_entry(sensor_data, action_data, context_data)
            
        except Exception as e:
            safe_print(f"Logging error: {e}")
    
    # ========================================================================
    # OVERRIDE METHODS TO ADD LOGGING
    # ========================================================================
    
    def apply_balance(self):
        """Apply dynamic balance correction with logging."""
        # Call parent implementation
        super().apply_balance()
        
        # Log balance action if balance was applied
        if self.sensors.has_accelerometer():
            pitch, roll = self.sensors.get_tilt()
            from components.utils.config import BALANCE_DEADZONE
            max_tilt = max(abs(pitch), abs(roll))
            if max_tilt >= BALANCE_DEADZONE:
                self.log_current_state(action='balance', steps=1)
    
    def move_forward(self):
        """Execute smooth forward movement with logging."""
        # Log before action
        self.log_current_state(action='forward', steps=1)
        
        # Call parent implementation
        super().move_forward()
    
    def execute_obstacle_avoidance(self, distance):
        """Execute obstacle avoidance maneuver with logging."""
        from components.navigation_state import RobotState
        from components.utils.config import DISTANCE_WARNING, DISTANCE_SAFE
        
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.stuck_detector.record_obstacle()
        
        safe_print(f"{ICONS['obstacle']} Obstacle at {distance:.1f}cm")
        
        # Get recommended action
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
            self.log_current_state(action='emergency_stop', steps=0)
        
        # Execute backward movement with logging
        self.log_current_state(action='backward', steps=action['backward_steps'])
        self.crawler.do_action('backward', action['backward_steps'], self.motion.get_speed())
        
        import time
        time.sleep(0.4)
        
        # Execute turn with logging
        turn_action = 'turn_left' if action['turn_direction'] == 'turn left' else 'turn_right'
        self.log_current_state(action=turn_action, steps=action['turn_amount'])
        self.crawler.do_action(action['turn_direction'], action['turn_amount'], 
                              self.motion.get_speed())
        time.sleep(0.3)
    
    def execute_floor_danger_avoidance(self, danger_type, suggested_action):
        """Execute floor danger avoidance maneuver with logging."""
        from components.navigation_state import RobotState
        from components.navigation.balance import get_compact_pose
        from components.utils.config import SPEED_MIN
        import time
        
        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.stuck_detector.record_floor_danger()
        
        safe_print(f"{ICONS['warning']} Floor danger: {danger_type}")
        self.announce(f"Edge detected!")
        
        # Get recommended action
        distance = self.sensors.get_distance()
        action = self.obstacle_handler.decide_floor_danger_action(danger_type, distance)
        
        # Handle airborne emergency
        if action['emergency'] and action['action'] == 'compact':
            self.motion.emergency_stop()
            pose = get_compact_pose()
            self.log_current_state(action='compact_emergency', steps=0)
            self.crawler.do_step(pose, SPEED_MIN)
            time.sleep(0.5)
            return
        
        # Execute primary action with logging
        if action['action']:
            self.log_current_state(action=action['action'], steps=action['steps'])
            self.crawler.do_action(action['action'], action['steps'], 
                                  self.motion.get_speed())
            time.sleep(0.3)
        
        # Execute secondary action with logging
        if action['secondary_action']:
            self.log_current_state(action=action['secondary_action'], 
                                  steps=action['secondary_steps'])
            self.crawler.do_action(action['secondary_action'], action['secondary_steps'],
                                  self.motion.get_speed())
            time.sleep(0.3)
    
    def execute_escape_pattern(self):
        """Execute escape pattern when stuck with logging."""
        from components.navigation_state import RobotState
        import time
        
        self.change_state(RobotState.STUCK)
        pattern = self.stuck_detector.get_escape_pattern()
        
        self.announce("Executing escape maneuver")
        safe_print(f"{ICONS['warning']} Stuck! Escape pattern: {pattern}")
        
        for action, steps in pattern:
            if self.stop_event.is_set():
                break
            self.log_current_state(action=action, steps=steps)
            self.crawler.do_action(action, steps, self.motion.get_speed())
            time.sleep(0.3)
        
        self.stuck_detector.reset()
    
    def print_status(self):
        """Print current navigation status with logging stats."""
        # Call parent implementation
        super().print_status()
        
        # Add logging-specific stats
        if self.enable_logging and self.logger:
            if self.enable_photos:
                # Photo logger stats
                photo_stats = self.logger.photo_logger.get_stats() if hasattr(self.logger, 'photo_logger') else {}
                safe_print(f"  Photos captured: {photo_stats.get('frames_captured', 0)}")
                safe_print(f"  Sensor entries: {self.logger.entries_logged}")
            else:
                # Regular logger stats
                log_stats = self.logger.get_stats()
                safe_print(f"  Logged: {log_stats['entries_logged']} samples ({log_stats['rate']:.1f} Hz)")
        
        safe_print("")
    
    def stop(self):
        """Stop navigation, close logger, and print final stats."""
        safe_print(f"\n{ICONS['stop']} Stopping navigation...")
        self.running = False
        self.stop_event.set()
        
        import time
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['stats']} ===== Final Statistics =====")
        safe_print(f"  Runtime: {uptime:.1f}s")
        safe_print(f"  Total steps: {self.total_steps}")
        safe_print(f"  Final state: {self.state.value}")
        
        # Close logger and show stats
        if self.enable_logging and self.logger:
            self.logger.close()
        
        safe_print("=" * 40)
        
        # Return to compact pose for safe pickup (using parent's implementation)
        safe_print(f"\n{ICONS['robot']} Moving to compact pose for safe pickup...")
        from components.navigation.balance import get_compact_pose
        compact_pose = get_compact_pose()
        self.crawler.do_step(compact_pose, 40)
        time.sleep(0.5)  # Give time to settle
        safe_print(f"{ICONS['check']} Robot ready for pickup")
        
        # Close sensors
        self.sensors.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="PiCrawler Autonomous Navigation with Data Logging"
    )
    parser.add_argument('--log', action='store_true',
                       help='Enable data logging for ML training')
    parser.add_argument('--log-rate', type=int, default=10,
                       help='Logging sample rate in Hz (default: 10)')
    parser.add_argument('--log-dir', type=str, default=None,
                       help='Directory to save log files (default: self_aware/logs)')
    parser.add_argument('--photos', action='store_true',
                       help='Enable photo capture with logging (requires --log)')
    parser.add_argument('--photo-rate', type=float, default=2.0,
                       help='Photo capture rate in Hz (default: 2.0)')
    parser.add_argument('--photo-resolution', type=str, default='320x240',
                       help='Photo resolution WxH (default: 320x240)')
    
    return parser.parse_args()


def main():
    """Main entry point for autonomous navigation with logging."""
    args = parse_args()
    
    # Validation: photos require logging
    if args.photos and not args.log:
        safe_print(f"\n{ICONS['warning']} Error: --photos requires --log to be enabled")
        safe_print("Usage: python3 autonomous_navigator_with_logging.py --log --photos")
        sys.exit(1)
    
    # Parse photo resolution
    photo_resolution = (320, 240)  # Default
    if args.photo_resolution:
        try:
            width, height = args.photo_resolution.lower().split('x')
            photo_resolution = (int(width), int(height))
        except:
            safe_print(f"{ICONS['warning']} Invalid photo resolution format. Using default 320x240")
    
    # Print banner
    from components.utils.config import DISTANCE_SENSOR_TYPE
    
    safe_print(f"\n{ICONS['robot']} PiCrawler Autonomous Navigation System")
    safe_print("=" * 50)
    safe_print("Using refactored components from components/")
    safe_print("Distance Sensor: {}".format(DISTANCE_SENSOR_TYPE or "None (IR only)"))
    
    if args.log:
        safe_print(f"Data Logging: ENABLED ({args.log_rate} Hz)")
        if args.photos:
            safe_print(f"Photo Capture: ENABLED ({args.photo_rate} Hz, {photo_resolution[0]}x{photo_resolution[1]})")
            safe_print("Photos will be used for clear/non-clear path detection ML")
        else:
            safe_print("Photo Capture: DISABLED (use --photos to enable)")
        safe_print(f"Log Directory: {args.log_dir or 'self_aware/logs'}")
    else:
        safe_print("Data Logging: DISABLED (use --log to enable)")
    
    safe_print("=" * 50 + "\n")
    
    # Create navigator with logging configuration
    navigator = AutonomousNavigatorWithLogging(
        enable_logging=args.log,
        log_rate_hz=args.log_rate,
        log_dir=args.log_dir,
        enable_photos=args.photos,
        photo_rate_hz=args.photo_rate,
        photo_resolution=photo_resolution
    )
    
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
