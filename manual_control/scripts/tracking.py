#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced PiCrawler Autonomous Navigation System

Features:
- Smooth movement with sensor fusion (IR sensors, accelerometer, distance sensor)
- Support for multiple distance sensors (HC-SR04, VL53L0X, VL53L1X)
- Adaptive speed control based on terrain and obstacles
- Dynamic balance correction
- Intelligent obstacle avoidance with path planning
"""

import os
import sys
import time
import random
from threading import Event
from enum import Enum
from collections import deque
import math

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from picrawler import Picrawler
from robot_hat import TTS, Pin, utils
from components.sensors.distance_sensor import create_distance_sensor
from components.sensors import ir_distance, accelerometer


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_print(message):
    """Print with Unicode fallback"""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', 'replace').decode('ascii'))


def get_icon(emoji, fallback):
    """Return emoji or fallback for terminal compatibility"""
    try:
        emoji.encode(sys.stdout.encoding or 'utf-8')
        return emoji
    except (UnicodeEncodeError, AttributeError):
        return fallback


ICONS = {
    'robot': get_icon('🤖', '[ROBOT]'),
    'forward': get_icon('➡️', '[FWD]'),
    'warning': get_icon('⚠️', '[WARN]'),
    'obstacle': get_icon('🚧', '[OBS]'),
    'tilt': get_icon('📐', '[TILT]'),
    'scan': get_icon('🔍', '[SCAN]'),
    'check': get_icon('✅', '[OK]'),
    'stop': get_icon('🛑', '[STOP]'),
    'stats': get_icon('📊', '[STATS]'),
}


# ============================================================================
# CONFIGURATION
# ============================================================================

# Distance sensor configuration (change type here!)
# Set to None to disable distance sensor and rely only on IR sensors
DISTANCE_SENSOR_TYPE = None  # Options: None, "HC-SR04", "VL53L0X", "VL53L1X"

# Pin names as strings to avoid creating Pin objects until needed
DISTANCE_SENSOR_CONFIG = {
    "HC-SR04": {"trigger_pin": "D2", "echo_pin": "D3"},  # Pin names, not objects
    "VL53L0X": {"i2c_address": 0x29},
    "VL53L1X": {"i2c_address": 0x29},
}

# Movement parameters
SPEED_MAX = 80
SPEED_NORMAL = 70
SPEED_CAUTION = 50
SPEED_MIN = 35

# Distance thresholds (cm)
DISTANCE_DANGER = 15
DISTANCE_WARNING = 25
DISTANCE_SAFE = 40

# Tilt thresholds (degrees)
TILT_CAUTION = 10.0
TILT_DANGER = 20.0

# Balance correction
BALANCE_DEADZONE = 3.0
BALANCE_MAX_TILT = 25.0
BALANCE_SPEED = 60

# Leg positions for balance [x, y, z]
LEG_EXTENDED = [60, 45, -75]
LEG_NEUTRAL = [45, 37, -52]
LEG_RETRACTED = [30, 30, -30]

# Leg IR sensor mapping
LEG_IR = {0: 'fl', 1: 'fr', 2: 'bl', 3: 'br'}


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class RobotState(Enum):
    EXPLORING = "exploring"
    AVOIDING_OBSTACLE = "avoiding_obstacle"
    AVOIDING_FLOOR_DANGER = "avoiding_floor_danger"
    TILT_CORRECTION = "tilt_correction"
    STUCK = "stuck"
    EMERGENCY = "emergency"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def lerp(a, b, t):
    """Linear interpolation between two 3D points"""
    return [a[i] + t * (b[i] - a[i]) for i in range(3)]


def compute_balance_pose(pitch, roll):
    """Calculate leg positions to compensate for tilt"""
    # Sign matrix: how each leg should move to counter tilt
    # [FL, FR, BL, BR]
    pitch_signs = [+1, +1, -1, -1]  # pitch > 0 (nose down): extend front
    roll_signs = [+1, -1, +1, -1]   # roll > 0 (tilt right): extend left
    
    # Normalize tilt to -1..+1 range
    pitch_factor = max(-1.0, min(1.0, pitch / BALANCE_MAX_TILT))
    roll_factor = max(-1.0, min(1.0, roll / BALANCE_MAX_TILT))
    
    pose = []
    for i in range(4):
        # Combine pitch and roll corrections
        factor = pitch_signs[i] * pitch_factor + roll_signs[i] * roll_factor
        factor = max(-1.0, min(1.0, factor))
        
        if factor >= 0.0:
            # Extend leg (push down)
            pose.append(lerp(LEG_NEUTRAL, LEG_EXTENDED, factor))
        else:
            # Retract leg (pull up)
            pose.append(lerp(LEG_RETRACTED, LEG_NEUTRAL, factor + 1.0))
    
    return pose


# ============================================================================
# SMOOTH MOTION CONTROLLER
# ============================================================================

class SmoothMotionController:
    """Handles smooth speed transitions and movement planning"""
    
    def __init__(self, initial_speed=SPEED_NORMAL):
        self.current_speed = initial_speed
        self.target_speed = initial_speed
        self.speed_change_rate = 5  # Speed units per update
        
    def set_target_speed(self, target):
        """Set new target speed"""
        self.target_speed = max(SPEED_MIN, min(SPEED_MAX, target))
    
    def update(self):
        """Smoothly transition current speed towards target"""
        if self.current_speed < self.target_speed:
            self.current_speed = min(self.current_speed + self.speed_change_rate, 
                                    self.target_speed)
        elif self.current_speed > self.target_speed:
            self.current_speed = max(self.current_speed - self.speed_change_rate, 
                                    self.target_speed)
        return int(self.current_speed)
    
    def get_speed(self):
        """Get current speed"""
        return int(self.current_speed)
    
    def emergency_stop(self):
        """Immediately set speed to minimum"""
        self.current_speed = SPEED_MIN
        self.target_speed = SPEED_MIN


# ============================================================================
# MAIN ROBOT CLASS
# ============================================================================

class EnhancedPiCrawler:
    """Enhanced autonomous navigation with sensor fusion"""
    
    def __init__(self, distance_sensor_type=DISTANCE_SENSOR_TYPE):
        safe_print(f"\n{ICONS['robot']} Initializing Enhanced PiCrawler...")
        
        # Reset MCU/GPIO to ensure clean state (important for reliable sensor readings)
        safe_print("Resetting MCU...")
        utils.reset_mcu()
        time.sleep(0.2)
        
        # Core components
        self.crawler = Picrawler()
        self.tts = TTS()
        self.motion = SmoothMotionController()
        
        # Initialize distance sensor
        sensor_config = DISTANCE_SENSOR_CONFIG.get(distance_sensor_type, {})
        self.distance_sensor = create_distance_sensor(distance_sensor_type, **sensor_config)
        
        if self.distance_sensor is None:
            safe_print(f"{ICONS['warning']} No distance sensor available - using IR only")
        
        # Initialize accelerometer
        try:
            accelerometer.wake()
            time.sleep(0.1)
            self.accel_available = True
            safe_print(f"{ICONS['check']} Accelerometer initialized")
        except Exception as e:
            safe_print(f"{ICONS['warning']} Accelerometer not available: {e}")
            self.accel_available = False
        
        # State management
        self.state = RobotState.EXPLORING
        self.previous_state = RobotState.EXPLORING
        self.running = False
        self.stop_event = Event()
        
        # Movement tracking
        self.distance_history = deque(maxlen=10)
        self.last_successful_move = time.time()
        self.total_steps = 0
        self.start_time = time.time()
        
        # Obstacle tracking
        self.consecutive_obstacles = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter = 0
        
        # Escape patterns for when stuck
        self.escape_patterns = [
            [('backward', 2), ('turn left', 3), ('forward', 1)],
            [('backward', 2), ('turn right', 3), ('forward', 1)],
            [('turn left', 4), ('forward', 2)],
            [('turn right', 4), ('forward', 2)],
            [('backward', 3), ('turn left', 2), ('turn right', 2)],
        ]
        
        safe_print(f"{ICONS['check']} Enhanced PiCrawler ready!\n")
    
    def announce(self, message):
        """Announce status via TTS"""
        safe_print(f"🔊 {message}")
        try:
            self.tts.say(message)
        except Exception as e:
            safe_print(f"TTS Error: {e}")
    
    def change_state(self, new_state):
        """Change robot state"""
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            safe_print(f"State: {self.previous_state.value} → {new_state.value}")
    
    # ========================================================================
    # SENSOR METHODS
    # ========================================================================
    
    def get_distance(self):
        """Get filtered distance reading"""
        if self.distance_sensor is None:
            return 999
        return self.distance_sensor.read_filtered()
    
    def get_tilt(self):
        """Get pitch and roll from accelerometer"""
        if not self.accel_available:
            return 0.0, 0.0
        try:
            return accelerometer.get_tilt()
        except Exception:
            return 0.0, 0.0
    
    def get_floor_sensors(self):
        """Read all IR floor sensors"""
        try:
            return ir_distance.read_legs()
        except Exception as e:
            safe_print(f"IR sensor error: {e}")
            return {'fl': 0, 'fr': 0, 'bl': 0, 'br': 0}
    
    def analyze_floor_danger(self, sensors):
        """Analyze floor sensor readings and return danger type"""
        fl, fr = sensors['fl'], sensors['fr']
        bl, br = sensors['bl'], sensors['br']
        danger_count = fl + fr + bl + br
        
        if danger_count == 0:
            return None, None
        
        if danger_count == 4:
            return 'airborne', None
        
        # Front danger
        if fl and fr:
            return 'front_edge', 'backward'
        
        # Back danger
        if bl and br:
            return 'back_edge', 'forward'
        
        # Side dangers
        if fl and bl:
            return 'left_edge', 'turn right'
        if fr and br:
            return 'right_edge', 'turn left'
        
        # Corner dangers
        if fl:
            return 'corner_fl', 'turn right'
        if fr:
            return 'corner_fr', 'turn left'
        if bl:
            return 'corner_bl', 'turn right'
        if br:
            return 'corner_br', 'turn left'
        
        return 'unknown', None
    
    # ========================================================================
    # BALANCE AND MOVEMENT
    # ========================================================================
    
    def apply_balance(self):
        """Apply dynamic balance correction based on tilt"""
        if not self.accel_available:
            return
        
        try:
            pitch, roll = self.get_tilt()
            max_tilt = max(abs(pitch), abs(roll))
            
            if max_tilt < BALANCE_DEADZONE:
                return
            
            pose = compute_balance_pose(pitch, roll)
            self.crawler.do_step(pose, BALANCE_SPEED)
            safe_print(f"{ICONS['tilt']} Balance: pitch={pitch:+.1f}° roll={roll:+.1f}°")
        except Exception as e:
            safe_print(f"Balance error: {e}")
    
    def update_speed_from_tilt(self):
        """Adjust speed based on tilt angle"""
        if not self.accel_available:
            return
        
        pitch, roll = self.get_tilt()
        max_tilt = max(abs(pitch), abs(roll))
        
        if max_tilt > TILT_DANGER:
            self.motion.set_target_speed(SPEED_MIN)
            if self.state not in [RobotState.EMERGENCY, RobotState.TILT_CORRECTION]:
                self.change_state(RobotState.TILT_CORRECTION)
                safe_print(f"{ICONS['warning']} Danger tilt: {max_tilt:.1f}°")
        
        elif max_tilt > TILT_CAUTION:
            self.motion.set_target_speed(SPEED_CAUTION)
            if self.state == RobotState.EXPLORING:
                self.change_state(RobotState.TILT_CORRECTION)
        
        else:
            if self.state == RobotState.TILT_CORRECTION:
                self.change_state(RobotState.EXPLORING)
            if self.state == RobotState.EXPLORING:
                self.motion.set_target_speed(SPEED_NORMAL)
    
    def move_forward(self):
        """Execute smooth forward movement"""
        speed = self.motion.update()
        safe_print(f"{ICONS['forward']} Forward (speed={speed})")
        self.crawler.do_action('forward', 1, speed)
        self.last_successful_move = time.time()
        self.total_steps += 1
        
        # Decay obstacle counters on successful movement
        if self.consecutive_obstacles > 0:
            self.consecutive_obstacles -= 1
        if self.consecutive_floor_dangers > 0:
            self.consecutive_floor_dangers -= 1
    
    # ========================================================================
    # OBSTACLE AVOIDANCE
    # ========================================================================
    
    def handle_obstacle(self, distance):
        """Handle obstacle detected by distance sensor"""
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.consecutive_obstacles += 1
        
        safe_print(f"{ICONS['obstacle']} Obstacle at {distance:.1f}cm")
        
        # Emergency stop for very close obstacles
        if distance < DISTANCE_DANGER:
            self.motion.emergency_stop()
            self.announce("Emergency stop!")
            self.crawler.do_action('backward', 3, SPEED_MIN)
            time.sleep(0.4)
        else:
            self.crawler.do_action('backward', 2, self.motion.get_speed())
            time.sleep(0.3)
        
        # Use accelerometer to pick best turn direction if available
        if self.accel_available:
            _, roll = self.get_tilt()
            if roll > 3:
                turn_direction = 'turn left'
            elif roll < -3:
                turn_direction = 'turn right'
            else:
                turn_direction = random.choice(['turn left', 'turn right'])
        else:
            turn_direction = random.choice(['turn left', 'turn right'])
        
        # More aggressive turning if stuck
        turn_amount = 3 if self.consecutive_obstacles > 3 else 2
        self.crawler.do_action(turn_direction, turn_amount, self.motion.get_speed())
        time.sleep(0.3)
        
        return True
    
    def handle_floor_danger(self, danger_type, suggested_action):
        """Handle floor edge/drop detected by IR sensors"""
        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.consecutive_floor_dangers += 1
        
        safe_print(f"{ICONS['warning']} Floor danger: {danger_type}")
        
        if danger_type == 'airborne':
            self.motion.emergency_stop()
            self.announce("Airborne detected!")
            # Tuck legs and hope for the best
            compact_pose = [[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]]
            self.crawler.do_step(compact_pose, SPEED_MIN)
            time.sleep(0.5)
            return True
        
        # Handle edge dangers
        if 'edge' in danger_type or 'corner' in danger_type:
            self.announce(f"Edge detected!")
            
            if suggested_action == 'backward':
                self.crawler.do_action('backward', 2, self.motion.get_speed())
                time.sleep(0.3)
                # Turn away from edge
                turn_dir = random.choice(['turn left', 'turn right'])
                self.crawler.do_action(turn_dir, 2, self.motion.get_speed())
            
            elif suggested_action == 'forward':
                # Back edge detected - move forward if safe
                distance = self.get_distance()
                if distance > DISTANCE_SAFE:
                    self.crawler.do_action('forward', 2, self.motion.get_speed())
                else:
                    # Can't go forward - turn around
                    self.crawler.do_action('turn right', 4, self.motion.get_speed())
            
            elif suggested_action:
                # Specific turn direction suggested
                self.crawler.do_action(suggested_action, 2, self.motion.get_speed())
            
            time.sleep(0.3)
        
        return True
    
    # ========================================================================
    # STUCK DETECTION AND RECOVERY
    # ========================================================================
    
    def is_stuck(self):
        """Check if robot appears to be stuck"""
        time_since_move = time.time() - self.last_successful_move
        return (self.consecutive_obstacles > 5 or
                self.consecutive_floor_dangers > 4 or
                time_since_move > 15)
    
    def execute_escape_pattern(self):
        """Execute random escape pattern when stuck"""
        self.change_state(RobotState.STUCK)
        pattern = random.choice(self.escape_patterns)
        
        self.announce("Executing escape maneuver")
        safe_print(f"{ICONS['warning']} Stuck! Escape pattern: {pattern}")
        
        for action, steps in pattern:
            if self.stop_event.is_set():
                break
            self.crawler.do_action(action, steps, self.motion.get_speed())
            time.sleep(0.3)
        
        # Reset counters
        self.consecutive_obstacles = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter = 0
        self.last_successful_move = time.time()
    
    # ========================================================================
    # MAIN EXPLORATION LOOP
    # ========================================================================
    
    def print_status(self):
        """Print current robot status"""
        uptime = time.time() - self.start_time
        pitch, roll = self.get_tilt()
        
        safe_print(f"\n{ICONS['stats']} ===== Status =====")
        safe_print(f"  State: {self.state.value}")
        safe_print(f"  Uptime: {uptime:.1f}s")
        safe_print(f"  Steps: {self.total_steps}")
        safe_print(f"  Speed: {self.motion.get_speed()}")
        safe_print(f"  Obstacles: {self.consecutive_obstacles}")
        safe_print(f"  Floor dangers: {self.consecutive_floor_dangers}")
        if self.accel_available:
            safe_print(f"  Tilt: pitch={pitch:+.1f}° roll={roll:+.1f}°")
        safe_print("=" * 30 + "\n")
    
    def exploration_loop(self):
        """Main autonomous exploration loop"""
        safe_print(f"{ICONS['robot']} Starting exploration...\n")
        self.announce("Beginning autonomous exploration")
        
        last_status_time = time.time()
        status_interval = 30
        
        while self.running and not self.stop_event.is_set():
            try:
                # Periodic status report
                if time.time() - last_status_time > status_interval:
                    self.print_status()
                    last_status_time = time.time()
                
                # 1. Update speed from tilt
                self.update_speed_from_tilt()
                
                # 2. Check floor sensors (highest priority)
                floor_sensors = self.get_floor_sensors()
                danger_type, suggested_action = self.analyze_floor_danger(floor_sensors)
                
                if danger_type:
                    self.handle_floor_danger(danger_type, suggested_action)
                    continue
                
                # 3. Check distance sensor for obstacles
                distance = self.get_distance()
                
                # Adjust warning threshold based on state
                if self.state == RobotState.AVOIDING_OBSTACLE:
                    threshold = DISTANCE_SAFE
                else:
                    threshold = DISTANCE_WARNING
                
                if distance < threshold:
                    self.handle_obstacle(distance)
                    continue
                
                # 4. Check if stuck
                if self.is_stuck():
                    self.stuck_counter += 1
                    if self.stuck_counter >= 2:
                        self.execute_escape_pattern()
                        continue
                
                # 5. Normal exploration - move forward
                if self.state not in [RobotState.EXPLORING, RobotState.TILT_CORRECTION]:
                    self.change_state(RobotState.EXPLORING)
                
                self.move_forward()
                
                # Apply balance correction between steps
                self.apply_balance()
                
                # Random announcements
                if random.randint(1, 150) == 1:
                    self.announce(random.choice([
                        "Exploring",
                        "All systems nominal",
                        "Navigation active",
                    ]))
                
                time.sleep(0.1)
            
            except KeyboardInterrupt:
                safe_print(f"\n{ICONS['stop']} Manual stop")
                break
            
            except Exception as e:
                safe_print(f"Error in main loop: {e}")
                time.sleep(1)
    
    def start(self):
        """Start autonomous exploration"""
        self.running = True
        self.exploration_loop()
    
    def stop(self):
        """Stop exploration and print final stats"""
        safe_print(f"\n{ICONS['stop']} Stopping exploration...")
        self.running = False
        self.stop_event.set()
        
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['stats']} ===== Final Statistics =====")
        safe_print(f"  Runtime: {uptime:.1f}s")
        safe_print(f"  Total steps: {self.total_steps}")
        safe_print(f"  Final state: {self.state.value}")
        safe_print("=" * 40)
        
        # Return to neutral stance
        neutral_pose = [list(LEG_NEUTRAL)] * 4
        self.crawler.do_step(neutral_pose, 40)
        
        # Close distance sensor if needed
        if self.distance_sensor and hasattr(self.distance_sensor, 'close'):
            self.distance_sensor.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    safe_print(f"\n{ICONS['robot']} Enhanced PiCrawler Autonomous Navigation")
    safe_print("=" * 50)
    safe_print(f"Distance Sensor: {DISTANCE_SENSOR_TYPE}")
    safe_print(f"Smooth movement with sensor fusion enabled")
    safe_print("=" * 50 + "\n")
    
    robot = EnhancedPiCrawler()
    
    try:
        robot.start()
    except KeyboardInterrupt:
        safe_print(f"\n{ICONS['stop']} Keyboard interrupt")
    except Exception as e:
        safe_print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        robot.stop()
        safe_print(f"\n{ICONS['check']} Shutdown complete\n")


if __name__ == '__main__':
    main()
