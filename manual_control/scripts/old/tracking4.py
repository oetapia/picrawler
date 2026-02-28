#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-Aware PiCrawler Robot
Combines obstacle avoidance with floor danger detection for autonomous navigation
"""

import os
import sys
import time
import random
from datetime import datetime
from threading import Thread, Event
from enum import Enum

# Check if terminal supports UTF-8 output
def safe_print(message):
    """Print with fallback for terminals that don't support UTF-8"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        print(ascii_message)

# Safe emoji/icon functions
def get_icon(emoji, fallback):
    """Get emoji if supported, otherwise return fallback"""
    try:
        # Test if we can encode the emoji
        emoji.encode(sys.stdout.encoding or 'utf-8')
        return emoji
    except (UnicodeEncodeError, AttributeError):
        return fallback

# Define icons with fallbacks
ICONS = {
    'robot': get_icon('🤖', '[ROBOT]'),
    'spider': get_icon('🕷️', '[SPIDER]'),
    'speaker': get_icon('🔊', '[SPEAKER]'),
    'warning': get_icon('⚠️', '[WARNING]'),
    'obstacle': get_icon('🚧', '[OBSTACLE]'),
    'cycle': get_icon('🔄', '[CYCLE]'),
    'forward': get_icon('➡️', '[FORWARD]'),
    'stop': get_icon('🛑', '[STOP]'),
    'check': get_icon('✅', '[OK]'),
    'rocket': get_icon('🚀', '[START]'),
    'wave': get_icon('👋', '[WAVE]'),
    'stats': get_icon('📊', '[STATS]'),
    'chart': get_icon('📈', '[CHART]'),
    'explosion': get_icon('💥', '[ERROR]')
}

# Add the components directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))

# Import robot modules
from picrawler import Picrawler
from robot_hat import Ultrasonic, TTS
from robot_hat import Pin
from sensors import ir_distance

class RobotState(Enum):
    """Robot operational states"""
    EXPLORING = "exploring"
    AVOIDING_OBSTACLE = "avoiding_obstacle"
    AVOIDING_FLOOR_DANGER = "avoiding_floor_danger"
    STUCK = "stuck"
    PAUSED = "paused"
    EMERGENCY = "emergency"

class SelfAwarePiCrawler:
    def __init__(self):
        """Initialize the self-aware robot"""
        # Hardware initialization
        self.crawler = Picrawler()
        self.sonar = Ultrasonic(Pin("D2"), Pin("D3"))
        self.tts = TTS()
        
        # Robot settings
        self.speed = 70
        self.obstacle_distance = 20  # cm - distance to start avoiding obstacles
        self.safe_distance = 30     # cm - distance considered safe
        self.stuck_threshold = 5    # consecutive failed moves before considering stuck
        
        # State management
        self.current_state = RobotState.EXPLORING
        self.previous_state = RobotState.EXPLORING
        self.running = False
        self.stop_event = Event()
        
        # Behavior tracking
        self.consecutive_obstacles = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter = 0
        self.last_successful_move = time.time()
        self.total_distance_traveled = 0
        self.start_time = time.time()
        
        # Movement patterns for when stuck
        self.escape_patterns = [
            [('backward', 2), ('turn left', 3), ('forward', 1)],
            [('backward', 2), ('turn right', 3), ('forward', 1)],
            [('turn left', 4), ('forward', 2)],
            [('turn right', 4), ('forward', 2)],
            [('backward', 3), ('turn left', 2), ('turn right', 2), ('forward', 1)]
        ]
        
        safe_print(f"{ICONS['robot']} Self-Aware PiCrawler initialized!")
        self.announce_status("Self aware robot system online")

    def announce_status(self, message):
        """Announce status via TTS and print"""
        safe_print(f"{ICONS['speaker']} {message}")
        try:
            self.tts.say(message)
        except Exception as e:
            safe_print(f"TTS Error: {e}")

    def get_obstacle_distance(self):
        """Get distance reading from ultrasonic sensor"""
        try:
            distance = self.sonar.read()
            if distance == -2:  # No obstacle detected
                return 999  # Return high value for no obstacle
            elif distance <= 0:  # Invalid reading
                return 999
            else:
                return distance
        except Exception as e:
            safe_print(f"Sonar error: {e}")
            return 999

    def check_floor_dangers(self):
        """Check for floor-based dangers using IR sensors"""
        try:
            proximity_status = ir_distance.check_proximity()
            dangers = []
            
            if "danger_front" in proximity_status:
                dangers.append("front")
            if "danger_back" in proximity_status:
                dangers.append("back")
            if "danger_left" in proximity_status:
                dangers.append("left")
            if "danger_right" in proximity_status:
                dangers.append("right")
            
            return dangers
        except Exception as e:
            safe_print(f"Floor sensor error: {e}")
            return []

    def handle_floor_dangers(self, dangers):
        """Handle detected floor dangers"""
        if not dangers:
            return False
        
        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.consecutive_floor_dangers += 1
        
        safe_print(f"{ICONS['warning']} Floor danger detected: {', '.join(dangers)}")
        
        if "front" in dangers:
            self.announce_status("Ledge ahead!")
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.5)
            # Choose turn direction based on other dangers
            if "right" not in dangers:
                self.crawler.do_action('turn right', 2, self.speed)
            else:
                self.crawler.do_action('turn left', 2, self.speed)
        
        elif "back" in dangers:
            self.announce_status("Ledge behind!")
            self.crawler.do_action('forward', 2, self.speed)
            time.sleep(0.5)
        
        elif "left" in dangers and "right" not in dangers:
            self.crawler.do_action('turn right', 2, self.speed)
        
        elif "right" in dangers and "left" not in dangers:
            self.crawler.do_action('turn left', 2, self.speed)
        
        else:
            # Multiple dangers - turn around
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)
            self.crawler.do_action('turn right', 4, self.speed)
        
        return True

    def handle_obstacle_avoidance(self, distance):
        """Handle obstacle avoidance"""
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.consecutive_obstacles += 1
        
        safe_print(f"{ICONS['obstacle']} Obstacle at {distance}cm - avoiding")
        
        if distance <= 10:  # Very close obstacle
            self.announce_status("Very close obstacle!")
            self.crawler.do_action('backward', 3, self.speed)
            time.sleep(0.5)
            # Random turn to avoid getting stuck
            turn_direction = random.choice(['turn left', 'turn right'])
            self.crawler.do_action(turn_direction, 3, self.speed)
        
        elif distance <= self.obstacle_distance:
            # Choose avoidance strategy based on consecutive obstacles
            if self.consecutive_obstacles > 3:
                # Try more aggressive avoidance
                self.crawler.do_action('backward', 2, self.speed)
                time.sleep(0.3)
                turn_amount = random.randint(3, 5)
                turn_direction = random.choice(['turn left', 'turn right'])
                self.crawler.do_action(turn_direction, turn_amount, self.speed)
            else:
                # Standard avoidance
                self.crawler.do_action('backward', 1, self.speed)
                time.sleep(0.2)
                self.crawler.do_action('turn right', 2, self.speed)
        
        time.sleep(0.3)
        return True

    def execute_escape_pattern(self):
        """Execute escape pattern when stuck"""
        self.change_state(RobotState.STUCK)
        pattern = random.choice(self.escape_patterns)
        
        self.announce_status("I seem to be stuck. Trying escape pattern")
        safe_print(f"{ICONS['cycle']} Executing escape pattern: {pattern}")
        
        for action, steps in pattern:
            if self.stop_event.is_set():
                break
            safe_print(f"   -> {action} for {steps} steps")
            self.crawler.do_action(action, steps, self.speed)
            time.sleep(0.4)
        
        # Reset counters after escape attempt
        self.stuck_counter = 0
        self.consecutive_obstacles = 0
        self.consecutive_floor_dangers = 0

    def change_state(self, new_state):
        """Change robot state with logging"""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            safe_print(f"{ICONS['cycle']} State: {self.previous_state.value} -> {new_state.value}")

    def move_forward_safely(self):
        """Attempt to move forward with safety checks"""
        safe_print(f"{ICONS['forward']} Moving forward")
        self.crawler.do_action('forward', 1, self.speed)
        self.last_successful_move = time.time()
        self.total_distance_traveled += 1  # Approximate step count
        
        # Reset consecutive counters on successful move
        if self.consecutive_obstacles > 0:
            self.consecutive_obstacles = max(0, self.consecutive_obstacles - 1)
        if self.consecutive_floor_dangers > 0:
            self.consecutive_floor_dangers = max(0, self.consecutive_floor_dangers - 1)

    def is_stuck(self):
        """Determine if robot is stuck"""
        time_since_last_move = time.time() - self.last_successful_move
        
        # Consider stuck if too many consecutive obstacles/dangers or too much time passed
        if (self.consecutive_obstacles > 4 or 
            self.consecutive_floor_dangers > 3 or 
            time_since_last_move > 10):
            return True
        return False

    def print_status(self):
        """Print current robot status"""
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['stats']} Robot Status:")
        safe_print(f"   State: {self.current_state.value}")
        safe_print(f"   Uptime: {uptime:.1f}s")
        safe_print(f"   Distance traveled: ~{self.total_distance_traveled} steps")
        safe_print(f"   Consecutive obstacles: {self.consecutive_obstacles}")
        safe_print(f"   Consecutive floor dangers: {self.consecutive_floor_dangers}")
        safe_print(f"   Stuck counter: {self.stuck_counter}")

    def exploration_loop(self):
        """Main exploration loop"""
        safe_print(f"{ICONS['rocket']} Starting autonomous exploration...")
        self.announce_status("Beginning exploration mode")
        
        status_interval = 30  # Print status every 30 seconds
        last_status_time = time.time()
        
        while self.running and not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                # Print status periodically
                if current_time - last_status_time > status_interval:
                    self.print_status()
                    last_status_time = current_time
                
                # Check for floor dangers first (higher priority)
                floor_dangers = self.check_floor_dangers()
                if floor_dangers:
                    if self.handle_floor_dangers(floor_dangers):
                        continue
                
                # Check for obstacles
                distance = self.get_obstacle_distance()
                
                if distance <= self.obstacle_distance and distance > 0:
                    if self.handle_obstacle_avoidance(distance):
                        continue
                
                # Check if robot is stuck
                if self.is_stuck():
                    self.stuck_counter += 1
                    if self.stuck_counter >= self.stuck_threshold:
                        self.execute_escape_pattern()
                        continue
                
                # Safe to move forward
                if self.current_state != RobotState.EXPLORING:
                    self.change_state(RobotState.EXPLORING)
                    safe_print(f"{ICONS['check']} Returning to normal exploration")
                
                self.move_forward_safely()
                
                # Add some personality - occasional comments
                if random.randint(1, 100) == 1:  # 1% chance
                    comments = [
                        "Exploring is fun!",
                        "Looking for interesting things",
                        "All clear ahead",
                        "Navigation systems nominal"
                    ]
                    self.announce_status(random.choice(comments))
                
                time.sleep(0.1)  # Small delay between iterations
                
            except KeyboardInterrupt:
                safe_print(f"\n{ICONS['stop']} Manual stop requested")
                break
            except Exception as e:
                safe_print(f"[ERROR] Error in exploration loop: {e}")
                time.sleep(1)  # Wait before retrying

    def start_exploration(self):
        """Start the autonomous exploration"""
        self.running = True
        self.exploration_loop()

    def stop_exploration(self):
        """Stop the autonomous exploration"""
        safe_print(f"{ICONS['stop']} Stopping exploration...")
        self.running = False
        self.stop_event.set()
        self.announce_status("Exploration stopped")
        
        # Final status report
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['chart']} Final Statistics:")
        safe_print(f"   Total runtime: {uptime:.1f} seconds")
        safe_print(f"   Distance traveled: ~{self.total_distance_traveled} steps")
        safe_print(f"   Final state: {self.current_state.value}")

def main():
    """Main function to run the self-aware robot"""
    safe_print(f"{ICONS['spider']} Self-Aware PiCrawler Starting...")
    
    robot = SelfAwarePiCrawler()
    
    try:
        # Start exploration
        robot.start_exploration()
        
    except KeyboardInterrupt:
        safe_print(f"\n{ICONS['wave']} Shutting down gracefully...")
    except Exception as e:
        safe_print(f"{ICONS['explosion']} Unexpected error: {e}")
    finally:
        robot.stop_exploration()
        safe_print(f"{ICONS['cycle']} Robot shut down complete")

if __name__ == '__main__':
    main()
