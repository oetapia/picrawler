#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color-Tracking Self-Aware PiCrawler Robot
Steers toward a target color while avoiding obstacles and floor dangers.
"""

import os
import sys
import time
import random
from threading import Event
from enum import Enum


def safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode('ascii', 'replace').decode('ascii'))


def get_icon(emoji, fallback):
    try:
        emoji.encode(sys.stdout.encoding or 'utf-8')
        return emoji
    except (UnicodeEncodeError, AttributeError):
        return fallback


ICONS = {
    'robot':     get_icon('[EMOJI]', '[ROBOT]'),
    'spider':    get_icon('[EMOJI]', '[SPIDER]'),
    'speaker':   get_icon('[EMOJI]', '[SPEAKER]'),
    'warning':   get_icon('[EMOJI]', '[WARNING]'),
    'obstacle':  get_icon('[EMOJI]', '[OBSTACLE]'),
    'cycle':     get_icon('[EMOJI]', '[CYCLE]'),
    'target':    get_icon('[EMOJI]', '[TARGET]'),
    'search':    get_icon('[EMOJI]', '[SEARCH]'),
    'stop':      get_icon('[EMOJI]', '[STOP]'),
    'check':     get_icon('[EMOJI]', '[OK]'),
    'rocket':    get_icon('[EMOJI]', '[START]'),
    'wave':      get_icon('[EMOJI]', '[WAVE]'),
    'stats':     get_icon('[EMOJI]', '[STATS]'),
    'chart':     get_icon('[EMOJI]', '[CHART]'),
    'explosion': get_icon('[EMOJI]', '[ERROR]'),
    'camera':    get_icon('[EMOJI]', '[CAM]'),
}

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from picrawler import Picrawler
from robot_hat import Ultrasonic, TTS, Pin
from components.sensors import ir_distance
from vilib import Vilib
import numpy as np

# X-coordinate thresholds for a 320px-wide frame (matches bull_fight.py)
CENTER_LEFT  = 100
CENTER_RIGHT = 220


class RobotState(Enum):
    TRACKING              = "tracking"
    SEARCHING             = "searching"
    AVOIDING_OBSTACLE     = "avoiding_obstacle"
    AVOIDING_FLOOR_DANGER = "avoiding_floor_danger"
    STUCK                 = "stuck"


class ColorTrackingPiCrawler:
    def __init__(self, color="red"):
        self.crawler = Picrawler()
        self.sonar   = Ultrasonic(Pin("D2"), Pin("D3"))
        self.tts     = TTS()
        self.color   = color

        # Settings
        self.speed             = 70
        self.obstacle_distance = 20  # cm - start avoiding
        self.safe_distance     = 30  # cm - clear to stop avoiding (hysteresis)
        self.stuck_threshold   = 5

        # State
        self.current_state  = RobotState.SEARCHING
        self.previous_state = RobotState.SEARCHING
        self.running        = False
        self.stop_event     = Event()

        # Counters
        self.consecutive_obstacles     = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter             = 0
        self.last_successful_move      = time.time()
        self.total_distance_traveled   = 0
        self.start_time                = time.time()

        # Search rotation state
        self.search_steps          = 0
        self.search_turn_direction = 'turn right'
        self.search_flip_interval  = 8  # reverse scan direction after this many steps

        # Escape patterns
        self.escape_patterns = [
            [('backward', 2), ('turn left', 3),  ('forward', 1)],
            [('backward', 2), ('turn right', 3), ('forward', 1)],
            [('turn left', 4),  ('forward', 2)],
            [('turn right', 4), ('forward', 2)],
            [('backward', 3), ('turn left', 2), ('turn right', 2), ('forward', 1)],
        ]

        # Tactile sensing
        self.tactile_check_interval    = 10
        self.moves_since_tactile_check = 0
        self.known_obstacles           = {'left': False, 'right': False}
        self.tactile_poses = {
            'check_right': np.array([[45, 45, -45], [20, 80, 45], [45, 45, -45], [45, 45, -45]]),
            'check_left':  np.array([[20, 80, 45], [45, 45, -45], [45, 45, -45], [45, 45, -45]]),
            'neutral':     np.array([[45, 45, -45], [45, 45, -45], [45, 45, -45], [45, 45, -45]]),
        }

        safe_print(f"{ICONS['camera']} Starting camera, detecting: {self.color}")
        Vilib.camera_start()
        Vilib.display()
        Vilib.color_detect(self.color)

        safe_print(f"{ICONS['robot']} ColorTrackingPiCrawler initialized!")
        self.announce_status(f"Ready to track {self.color}")

    # ------------------------------------------------------------------
    # Hardware helpers
    # ------------------------------------------------------------------

    def announce_status(self, message):
        safe_print(f"{ICONS['speaker']} {message}")
        try:
            self.tts.say(message)
        except Exception as e:
            safe_print(f"TTS error: {e}")

    def get_obstacle_distance(self):
        try:
            distance = self.sonar.read()
            if distance == -2 or distance <= 0:
                return 999
            return distance
        except Exception as e:
            safe_print(f"Sonar error: {e}")
            return 999

    def check_floor_dangers(self):
        try:
            proximity_status = ir_distance.check_proximity()
            dangers = []
            if "danger_front" in proximity_status: dangers.append("front")
            if "danger_back"  in proximity_status: dangers.append("back")
            if "danger_left"  in proximity_status: dangers.append("left")
            if "danger_right" in proximity_status: dangers.append("right")
            return dangers
        except Exception as e:
            safe_print(f"Floor sensor error: {e}")
            return []

    # ------------------------------------------------------------------
    # Safety responses
    # ------------------------------------------------------------------

    def handle_floor_dangers(self, dangers):
        if not dangers:
            return False
        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.consecutive_floor_dangers += 1
        safe_print(f"{ICONS['warning']} Floor danger: {', '.join(dangers)}")

        if "front" in dangers:
            self.announce_status("Ledge ahead!")
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.5)
            if "right" not in dangers:
                self.crawler.do_action('turn right', 2, self.speed)
            else:
                self.crawler.do_action('turn left', 2, self.speed)

        elif "back" in dangers:
            self.announce_status("Ledge behind!")
            front_distance = self.get_obstacle_distance()
            if front_distance > self.obstacle_distance:
                self.crawler.do_action('forward', 2, self.speed)
            else:
                self.crawler.do_action('turn right', 2, self.speed)
            time.sleep(0.5)

        elif "left" in dangers and "right" not in dangers:
            self.crawler.do_action('turn right', 2, self.speed)

        elif "right" in dangers and "left" not in dangers:
            self.crawler.do_action('turn left', 2, self.speed)

        else:
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)
            self.crawler.do_action('turn right', 4, self.speed)

        return True

    def custom_pose(self, pose_array, speed=None):
        if speed is None:
            speed = self.speed
        try:
            self.crawler.do_step(pose_array.tolist(), speed)
            time.sleep(0.3)
        except Exception as e:
            safe_print(f"Pose error: {e}")

    def check_tactile_obstacles(self):
        obstacles_detected = {'left': False, 'right': False}
        safe_print(f"{ICONS['robot']} Tactile check...")
        try:
            self.custom_pose(self.tactile_poses['check_right'])
            if 'right' in self.check_floor_dangers():
                obstacles_detected['right'] = True
                safe_print(f"   {ICONS['warning']} Right obstacle (tactile)")

            self.custom_pose(self.tactile_poses['neutral'])
            time.sleep(0.2)

            self.custom_pose(self.tactile_poses['check_left'])
            if 'left' in self.check_floor_dangers():
                obstacles_detected['left'] = True
                safe_print(f"   {ICONS['warning']} Left obstacle (tactile)")

            self.custom_pose(self.tactile_poses['neutral'])
            self.known_obstacles.update(obstacles_detected)
        except Exception as e:
            safe_print(f"Tactile error: {e}")
            self.custom_pose(self.tactile_poses['neutral'])
        return obstacles_detected

    def smart_obstacle_avoidance(self, front_distance):
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.consecutive_obstacles += 1
        safe_print(f"{ICONS['obstacle']} Obstacle at {front_distance}cm")

        left_clear  = not self.known_obstacles.get('left', False)
        right_clear = not self.known_obstacles.get('right', False)

        if front_distance <= 10:
            self.announce_status("Very close obstacle!")
            self.crawler.do_action('backward', 3, self.speed)
            time.sleep(0.5)
        else:
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)

        if left_clear and right_clear:
            turn_direction = 'turn right'
        elif left_clear and not right_clear:
            turn_direction = 'turn left'
        elif not left_clear and right_clear:
            turn_direction = 'turn right'
        else:
            safe_print(f"   {ICONS['warning']} Both sides blocked - turning around")
            self.crawler.do_action('turn right', 4, self.speed)
            time.sleep(0.5)
            return True

        turn_amount = 3 if self.consecutive_obstacles > 2 else 2
        self.crawler.do_action(turn_direction, turn_amount, self.speed)
        time.sleep(0.4)
        return True

    def execute_escape_pattern(self):
        self.change_state(RobotState.STUCK)
        pattern = random.choice(self.escape_patterns)
        self.announce_status("Stuck! Trying escape pattern")
        safe_print(f"{ICONS['cycle']} Escape: {pattern}")
        for action, steps in pattern:
            if self.stop_event.is_set():
                break
            self.crawler.do_action(action, steps, self.speed)
            time.sleep(0.4)
        self.stuck_counter             = 0
        self.consecutive_obstacles     = 0
        self.consecutive_floor_dangers = 0
        self.last_successful_move      = time.time()
        self.known_obstacles           = {'left': False, 'right': False}

    def change_state(self, new_state):
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state  = new_state
            safe_print(f"{ICONS['cycle']} {self.previous_state.value} -> {new_state.value}")

    def is_stuck(self):
        return (
            self.consecutive_obstacles     > 4 or
            self.consecutive_floor_dangers > 3 or
            time.time() - self.last_successful_move > 10
        )

    # ------------------------------------------------------------------
    # Color tracking
    # ------------------------------------------------------------------

    def color_visible(self):
        return Vilib.detect_obj_parameter['color_n'] != 0

    def track_color(self):
        """Steer toward the detected color target."""
        color_x = Vilib.detect_obj_parameter['color_x']
        self.change_state(RobotState.TRACKING)
        self.search_steps = 0  # reset scan state on detection

        if color_x < CENTER_LEFT:
            safe_print(f"{ICONS['target']} x={color_x} -> turn left")
            self.crawler.do_action('turn left', 1, self.speed)
        elif color_x > CENTER_RIGHT:
            safe_print(f"{ICONS['target']} x={color_x} -> turn right")
            self.crawler.do_action('turn right', 1, self.speed)
        else:
            safe_print(f"{ICONS['target']} x={color_x} -> forward")
            self.crawler.do_action('forward', 1, self.speed)
            self.last_successful_move = time.time()
            self.total_distance_traveled   += 1
            self.moves_since_tactile_check += 1
            if self.consecutive_obstacles     > 0: self.consecutive_obstacles     -= 1
            if self.consecutive_floor_dangers > 0: self.consecutive_floor_dangers -= 1

    def search_for_color(self):
        """Rotate slowly to scan for the target color."""
        self.change_state(RobotState.SEARCHING)
        self.search_steps += 1

        if self.search_steps % self.search_flip_interval == 0:
            self.search_turn_direction = (
                'turn left' if self.search_turn_direction == 'turn right' else 'turn right'
            )
            safe_print(f"{ICONS['search']} Scan direction -> {self.search_turn_direction}")

        self.crawler.do_action(self.search_turn_direction, 1, self.speed // 2)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def exploration_loop(self):
        safe_print(f"{ICONS['rocket']} Color tracking started (target: {self.color})")
        status_interval  = 30
        last_status_time = time.time()

        while self.running and not self.stop_event.is_set():
            try:
                if time.time() - last_status_time > status_interval:
                    uptime = time.time() - self.start_time
                    safe_print(f"\n{ICONS['stats']} {self.current_state.value} | {uptime:.0f}s | steps: {self.total_distance_traveled}")
                    last_status_time = time.time()

                # 1. Floor dangers (highest priority)
                floor_dangers = self.check_floor_dangers()
                if floor_dangers:
                    self.handle_floor_dangers(floor_dangers)
                    continue

                # 2. Sonar reading
                distance = self.get_obstacle_distance()

                # 3. Periodic tactile check (or when near obstacle)
                if (self.moves_since_tactile_check >= self.tactile_check_interval or
                        (distance <= self.obstacle_distance and distance > 0)):
                    self.check_tactile_obstacles()
                    self.moves_since_tactile_check = 0

                # 4. Obstacle avoidance with hysteresis
                avoid_threshold = (
                    self.safe_distance if self.current_state == RobotState.AVOIDING_OBSTACLE
                    else self.obstacle_distance
                )
                if distance <= avoid_threshold and distance > 0:
                    self.smart_obstacle_avoidance(distance)
                    continue

                # 5. Escape if stuck
                if self.is_stuck():
                    self.stuck_counter += 1
                    if self.stuck_counter >= self.stuck_threshold:
                        self.execute_escape_pattern()
                    continue

                # 6. Track color or scan for it
                if self.color_visible():
                    self.track_color()
                else:
                    self.search_for_color()

                time.sleep(0.05)

            except KeyboardInterrupt:
                safe_print(f"\n{ICONS['stop']} Manual stop")
                break
            except Exception as e:
                safe_print(f"[ERROR] {e}")
                time.sleep(1)

    def start(self):
        self.running = True
        self.exploration_loop()

    def stop(self):
        safe_print(f"{ICONS['stop']} Stopping...")
        self.running = False
        self.stop_event.set()
        self.announce_status("Stopping")
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['chart']} Runtime: {uptime:.1f}s | Steps: {self.total_distance_traveled}")


def main():
    safe_print(f"{ICONS['spider']} Color Tracking PiCrawler Starting...")
    robot = ColorTrackingPiCrawler(color="red")
    try:
        robot.start()
    except KeyboardInterrupt:
        safe_print(f"\n{ICONS['wave']} Shutting down...")
    except Exception as e:
        safe_print(f"{ICONS['explosion']} Unexpected error: {e}")
    finally:
        robot.stop()
        safe_print(f"{ICONS['cycle']} Shutdown complete")


if __name__ == '__main__':
    main()
