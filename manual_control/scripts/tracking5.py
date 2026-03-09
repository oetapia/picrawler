#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-Aware PiCrawler Robot
Combines obstacle avoidance, per-leg IR floor detection, and MPU-6050
tilt sensing for smarter autonomous navigation.
"""

import os
import sys
import time
import random
from datetime import datetime
from threading import Event
from enum import Enum

def safe_print(message):
    """Print with fallback for terminals that don't support UTF-8"""
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
    'robot':     get_icon('🤖', '[ROBOT]'),
    'spider':    get_icon('🕷️', '[SPIDER]'),
    'speaker':   get_icon('🔊', '[SPEAKER]'),
    'warning':   get_icon('⚠️', '[WARNING]'),
    'obstacle':  get_icon('🚧', '[OBSTACLE]'),
    'cycle':     get_icon('🔄', '[CYCLE]'),
    'forward':   get_icon('➡️', '[FORWARD]'),
    'stop':      get_icon('🛑', '[STOP]'),
    'check':     get_icon('✅', '[OK]'),
    'rocket':    get_icon('🚀', '[START]'),
    'wave':      get_icon('👋', '[WAVE]'),
    'stats':     get_icon('📊', '[STATS]'),
    'chart':     get_icon('📈', '[CHART]'),
    'explosion': get_icon('💥', '[ERROR]'),
    'tilt':      get_icon('📐', '[TILT]'),
}

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from picrawler import Picrawler
from robot_hat import TTS, Pin
try:
    from robot_hat import Ultrasonic
except ImportError:
    Ultrasonic = None
from components.sensors import ir_distance
from components.sensors import accelerometer
import numpy as np


class RobotState(Enum):
    EXPLORING            = "exploring"
    AVOIDING_OBSTACLE    = "avoiding_obstacle"
    AVOIDING_FLOOR_DANGER = "avoiding_floor_danger"
    TILT_CAUTION         = "tilt_caution"
    STUCK                = "stuck"
    AIRBORNE             = "airborne"


class SelfAwarePiCrawler:
    def __init__(self):
        self.crawler = Picrawler()
        self.tts = TTS()

        try:
            self.sonar = Ultrasonic(Pin("D2"), Pin("D3")) if Ultrasonic else None
            if self.sonar:
                safe_print("Ultrasonic sensor initialised")
        except Exception as e:
            safe_print(f"Ultrasonic not available: {e}")
            self.sonar = None

        # Accelerometer
        try:
            accelerometer.wake()
            time.sleep(0.1)
            self.accel_available = True
            safe_print("MPU-6050 accelerometer initialised")
        except Exception as e:
            safe_print(f"Accelerometer not available: {e}")
            self.accel_available = False

        # Speed settings
        self.normal_speed  = 70
        self.caution_speed = 50
        self.speed         = self.normal_speed

        # Tilt thresholds (degrees)
        self.tilt_caution_threshold = 12.0
        self.tilt_danger_threshold  = 25.0

        # Obstacle distances (cm)
        self.obstacle_distance = 20
        self.safe_distance     = 30
        self.stuck_threshold   = 5

        # State
        self.current_state  = RobotState.EXPLORING
        self.previous_state = RobotState.EXPLORING
        self.running        = False
        self.stop_event     = Event()

        # Counters
        self.consecutive_obstacles     = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter             = 0
        self.last_successful_move      = time.time()
        self.total_distance_traveled   = 0
        self.start_time                = time.time()

        self.escape_patterns = [
            [('backward', 2), ('turn left', 3),  ('forward', 1)],
            [('backward', 2), ('turn right', 3), ('forward', 1)],
            [('turn left', 4),  ('forward', 2)],
            [('turn right', 4), ('forward', 2)],
            [('backward', 3), ('turn left', 2), ('turn right', 2), ('forward', 1)],
        ]

        self.tactile_poses = {
            'check_right': np.array([[45, 45, -45], [20, 80, 45], [45, 45, -45], [45, 45, -45]]),
            'check_left':  np.array([[20, 80, 45],  [45, 45, -45], [45, 45, -45], [45, 45, -45]]),
            'neutral':     np.array([[45, 45, -45], [45, 45, -45], [45, 45, -45], [45, 45, -45]]),
            'compact':     np.array([[45, 0, 0],    [45, 0, 0],    [45, 45, 0],   [45, 45, 0]]),
        }

        self.tactile_check_interval     = 10
        self.moves_since_tactile_check  = 0
        self.known_obstacles            = {'left': False, 'right': False}

        safe_print(f"{ICONS['robot']} Self-Aware PiCrawler initialized!")
        self.announce_status("Self aware robot system online")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def announce_status(self, message):
        safe_print(f"{ICONS['speaker']} {message}")
        try:
            self.tts.say(message)
        except Exception as e:
            safe_print(f"TTS Error: {e}")

    def change_state(self, new_state):
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state  = new_state
            safe_print(f"{ICONS['cycle']} State: {self.previous_state.value} -> {new_state.value}")

    def custom_pose(self, pose_array, speed=None):
        try:
            self.crawler.do_step(pose_array.tolist(), speed or self.speed)
            time.sleep(0.3)
        except Exception as e:
            safe_print(f"Pose execution error: {e}")

    # ------------------------------------------------------------------
    # Obstacle / sonar
    # ------------------------------------------------------------------

    def get_obstacle_distance(self):
        if self.sonar is None:
            return 999
        try:
            d = self.sonar.read()
            return 999 if d <= 0 or d == -2 else d
        except Exception as e:
            safe_print(f"Sonar error: {e}")
            return 999

    # ------------------------------------------------------------------
    # Accelerometer helpers
    # ------------------------------------------------------------------

    def _get_tilt(self):
        """Return (pitch, roll) in degrees, or (0, 0) if unavailable."""
        if not self.accel_available:
            return 0.0, 0.0
        try:
            return accelerometer.get_tilt()
        except Exception:
            return 0.0, 0.0

    def _pick_turn_from_accel(self):
        """
        Use roll to pick the uphill (safer) turn direction.
        Roll > 0 means tilted right  → prefer turning left (uphill).
        Roll < 0 means tilted left   → prefer turning right (uphill).
        Returns 'turn left', 'turn right', or None if level/unavailable.
        """
        _, roll = self._get_tilt()
        if roll > 3:
            return 'turn left'
        if roll < -3:
            return 'turn right'
        return None

    def check_and_apply_tilt(self):
        """Adjust speed and state based on current tilt reading."""
        if not self.accel_available:
            return
        pitch, roll = self._get_tilt()
        max_tilt = max(abs(pitch), abs(roll))

        if max_tilt > self.tilt_danger_threshold:
            if self.current_state not in (RobotState.TILT_CAUTION,
                                          RobotState.AVOIDING_FLOOR_DANGER,
                                          RobotState.AVOIDING_OBSTACLE,
                                          RobotState.AIRBORNE):
                self.change_state(RobotState.TILT_CAUTION)
            safe_print(f"{ICONS['tilt']} Steep tilt {max_tilt:.1f}deg - speed reduced")
            self.speed = max(30, self.normal_speed - int(max_tilt))

        elif max_tilt > self.tilt_caution_threshold:
            if self.current_state == RobotState.EXPLORING:
                self.change_state(RobotState.TILT_CAUTION)
                safe_print(f"{ICONS['tilt']} Tilt {max_tilt:.1f}deg - caution mode")
            self.speed = self.caution_speed

        else:
            if self.current_state == RobotState.TILT_CAUTION:
                self.change_state(RobotState.EXPLORING)
                safe_print(f"{ICONS['tilt']} Tilt normalised - resuming normal speed")
            self.speed = self.normal_speed

    # ------------------------------------------------------------------
    # Per-leg IR floor sensing
    # ------------------------------------------------------------------

    def get_leg_sensors(self):
        """Read all 4 IR sensors. Returns dict fl/fr/bl/br: 0=floor, 1=danger."""
        try:
            return ir_distance.read_legs()
        except Exception as e:
            safe_print(f"IR sensor error: {e}")
            return {'fl': 0, 'fr': 0, 'bl': 0, 'br': 0}

    def classify_floor_danger(self, legs):
        """
        Classify floor danger from per-leg readings.

        Returns (danger_type, turn_hint) where:
          danger_type: None | 'airborne' | 'corner_fl' | 'corner_fr' |
                       'corner_bl' | 'corner_br' | 'front' | 'back' |
                       'left' | 'right' | 'diagonal' | 'multiple'
          turn_hint:   None | 'left' | 'right'
        """
        fl, fr, bl, br = legs['fl'], legs['fr'], legs['bl'], legs['br']
        count = fl + fr + bl + br

        if count == 0:
            return None, None

        if count == 4:
            return 'airborne', None

        if count == 1:
            if fl: return 'corner_fl', 'right'   # front-left edge → back + turn right
            if fr: return 'corner_fr', 'left'    # front-right edge → back + turn left
            if bl: return 'corner_bl', 'right'   # back-left edge → forward + turn right
            if br: return 'corner_br', 'left'    # back-right edge → forward + turn left

        if count == 2:
            if fl and fr: return 'front',    None     # full front row → back straight
            if bl and br: return 'back',     None     # full back row  → forward straight
            if fl and bl: return 'left',     'right'  # full left side → turn right
            if fr and br: return 'right',    'left'   # full right side → turn left
            if fl and br: return 'diagonal', 'right'  # anti-diag → back + turn right
            if fr and bl: return 'diagonal', 'left'   # anti-diag → back + turn left

        # count == 3 or any remaining case
        return 'multiple', None

    def handle_floor_danger_smart(self, danger_type, turn_hint):
        """React to classified floor danger using per-corner information."""
        if danger_type is None:
            return False

        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.consecutive_floor_dangers += 1

        # --- Airborne ---
        if danger_type == 'airborne':
            pitch, roll = self._get_tilt()
            if self.accel_available and (abs(pitch) > 30 or abs(roll) > 30):
                # High tilt confirms genuinely airborne
                self.change_state(RobotState.AIRBORNE)
                self.announce_status("Airborne! Tucking legs")
                self.custom_pose(self.tactile_poses['compact'])
            else:
                # All sensors triggered but robot may just be on a very steep slope
                self.announce_status("All sensors triggered - backing up")
                self.crawler.do_action('backward', 2, self.speed)
                time.sleep(0.4)
                turn = self._pick_turn_from_accel() or 'turn right'
                self.crawler.do_action(turn, 2, self.speed)
            return True

        safe_print(f"{ICONS['warning']} Floor danger: {danger_type}  hint={turn_hint}")

        # --- Front / front corner ---
        if danger_type in ('front', 'corner_fl', 'corner_fr'):
            self.announce_status("Ledge ahead!")
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.4)
            if turn_hint:
                self.crawler.do_action(f'turn {turn_hint}', 2, self.speed)
            else:
                turn = self._pick_turn_from_accel() or 'turn right'
                self.crawler.do_action(turn, 2, self.speed)

        # --- Back / back corner ---
        elif danger_type in ('back', 'corner_bl', 'corner_br'):
            self.announce_status("Ledge behind!")
            if self.get_obstacle_distance() > self.obstacle_distance:
                self.crawler.do_action('forward', 2, self.speed)
                time.sleep(0.3)
                if turn_hint:
                    self.crawler.do_action(f'turn {turn_hint}', 1, self.speed)
            else:
                turn = self._pick_turn_from_accel() or 'turn right'
                self.crawler.do_action(turn, 2, self.speed)

        # --- Full side ---
        elif danger_type in ('left', 'right'):
            self.crawler.do_action(f'turn {turn_hint}', 2, self.speed)

        # --- Diagonal / multiple ---
        else:
            self.announce_status("Multiple danger zones!")
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)
            turn = self._pick_turn_from_accel() or 'turn right'
            self.crawler.do_action(turn, 3, self.speed)

        return True

    # ------------------------------------------------------------------
    # Tactile side-check (uses per-leg sensors)
    # ------------------------------------------------------------------

    def check_tactile_obstacles(self):
        """Use leg positioning to probe for side obstacles."""
        obstacles_detected = {'left': False, 'right': False}
        safe_print(f"{ICONS['robot']} Performing tactile obstacle check...")

        try:
            safe_print("   Checking right side...")
            self.custom_pose(self.tactile_poses['check_right'])
            legs = self.get_leg_sensors()
            if legs['fr'] == 1 or legs['br'] == 1:
                obstacles_detected['right'] = True
                safe_print(f"   {ICONS['warning']} Right side obstacle (tactile)")

            self.custom_pose(self.tactile_poses['neutral'])
            time.sleep(0.2)

            safe_print("   Checking left side...")
            self.custom_pose(self.tactile_poses['check_left'])
            legs = self.get_leg_sensors()
            if legs['fl'] == 1 or legs['bl'] == 1:
                obstacles_detected['left'] = True
                safe_print(f"   {ICONS['warning']} Left side obstacle (tactile)")

            self.custom_pose(self.tactile_poses['neutral'])
            self.known_obstacles.update(obstacles_detected)

            if obstacles_detected['left'] or obstacles_detected['right']:
                sides = [s for s, v in obstacles_detected.items() if v]
                self.announce_status(f"Tactile sensors detect obstacles on {' and '.join(sides)} side")
            else:
                safe_print(f"   {ICONS['check']} No side obstacles detected")

        except Exception as e:
            safe_print(f"Tactile sensing error: {e}")
            self.custom_pose(self.tactile_poses['neutral'])

        return obstacles_detected

    # ------------------------------------------------------------------
    # Obstacle avoidance
    # ------------------------------------------------------------------

    def smart_obstacle_avoidance(self, front_distance):
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.consecutive_obstacles += 1
        safe_print(f"{ICONS['obstacle']} Front obstacle at {front_distance}cm")

        if front_distance <= 10:
            self.announce_status("Emergency! Very close obstacle!")
            self.crawler.do_action('backward', 3, self.speed)
            time.sleep(0.5)
        else:
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)

        left_clear  = not self.known_obstacles.get('left', False)
        right_clear = not self.known_obstacles.get('right', False)

        if left_clear and right_clear:
            # Prefer the uphill direction when on a slope
            turn_direction = self._pick_turn_from_accel() or 'turn right'
            safe_print(f"   Both sides clear - {turn_direction} (accel-guided)")
        elif left_clear:
            turn_direction = 'turn left'
            safe_print(f"   {ICONS['check']} Turning left - right side blocked")
        elif right_clear:
            turn_direction = 'turn right'
            safe_print(f"   {ICONS['check']} Turning right - left side blocked")
        else:
            safe_print(f"   {ICONS['warning']} Both sides blocked - turning around")
            self.crawler.do_action('turn right', 4, self.speed)
            time.sleep(0.5)
            return True

        turn_amount = 3 if self.consecutive_obstacles > 2 else 2
        self.crawler.do_action(turn_direction, turn_amount, self.speed)
        time.sleep(0.4)
        return True

    # ------------------------------------------------------------------
    # Stuck handling
    # ------------------------------------------------------------------

    def execute_escape_pattern(self):
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

        self.stuck_counter             = 0
        self.consecutive_obstacles     = 0
        self.consecutive_floor_dangers = 0
        self.last_successful_move      = time.time()
        self.known_obstacles           = {'left': False, 'right': False}

    def is_stuck(self):
        time_since_last_move = time.time() - self.last_successful_move
        return (self.consecutive_obstacles     > 4 or
                self.consecutive_floor_dangers > 3 or
                time_since_last_move           > 10)

    # ------------------------------------------------------------------
    # Forward motion
    # ------------------------------------------------------------------

    def move_forward_safely(self):
        safe_print(f"{ICONS['forward']} Moving forward (speed={self.speed})")
        self.crawler.do_action('forward', 1, self.speed)
        self.last_successful_move       = time.time()
        self.total_distance_traveled   += 1
        self.moves_since_tactile_check += 1

        if self.consecutive_obstacles > 0:
            self.consecutive_obstacles = max(0, self.consecutive_obstacles - 1)
        if self.consecutive_floor_dangers > 0:
            self.consecutive_floor_dangers = max(0, self.consecutive_floor_dangers - 1)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def print_status(self):
        uptime = time.time() - self.start_time
        pitch, roll = self._get_tilt()
        safe_print(f"\n{ICONS['stats']} Robot Status:")
        safe_print(f"   State:              {self.current_state.value}")
        safe_print(f"   Uptime:             {uptime:.1f}s")
        safe_print(f"   Distance traveled:  ~{self.total_distance_traveled} steps")
        safe_print(f"   Speed:              {self.speed}")
        safe_print(f"   Consecutive obstacles:     {self.consecutive_obstacles}")
        safe_print(f"   Consecutive floor dangers: {self.consecutive_floor_dangers}")
        safe_print(f"   Stuck counter:      {self.stuck_counter}")
        safe_print(f"   Known obstacles:    L={self.known_obstacles['left']}  R={self.known_obstacles['right']}")
        if self.accel_available:
            safe_print(f"   Tilt:               pitch={pitch:+.1f}deg  roll={roll:+.1f}deg")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def exploration_loop(self):
        safe_print(f"{ICONS['rocket']} Starting autonomous exploration...")
        self.announce_status("Beginning exploration mode")

        status_interval   = 30
        last_status_time  = time.time()

        while self.running and not self.stop_event.is_set():
            try:
                current_time = time.time()

                if current_time - last_status_time > status_interval:
                    self.print_status()
                    last_status_time = current_time

                # 1. Tilt check - may update speed and state
                self.check_and_apply_tilt()

                # 2. Per-leg floor danger check (higher priority than sonar)
                legs = self.get_leg_sensors()
                danger_type, turn_hint = self.classify_floor_danger(legs)
                if danger_type:
                    if self.handle_floor_danger_smart(danger_type, turn_hint):
                        continue

                # 3. Sonar obstacle check
                distance = self.get_obstacle_distance()

                # Tactile side-check when approaching obstacle or periodically
                if (self.moves_since_tactile_check >= self.tactile_check_interval or
                        (0 < distance <= self.obstacle_distance)):
                    self.check_tactile_obstacles()
                    self.moves_since_tactile_check = 0

                avoid_threshold = (self.safe_distance
                                   if self.current_state == RobotState.AVOIDING_OBSTACLE
                                   else self.obstacle_distance)
                if 0 < distance <= avoid_threshold:
                    if self.smart_obstacle_avoidance(distance):
                        continue

                # 4. Stuck check
                if self.is_stuck():
                    self.stuck_counter += 1
                    if self.stuck_counter >= self.stuck_threshold:
                        self.execute_escape_pattern()
                        continue

                # 5. Move forward
                if self.current_state not in (RobotState.EXPLORING, RobotState.TILT_CAUTION):
                    self.change_state(RobotState.EXPLORING)
                    safe_print(f"{ICONS['check']} Returning to normal exploration")

                self.move_forward_safely()

                if random.randint(1, 100) == 1:
                    self.announce_status(random.choice([
                        "Exploring is fun!",
                        "Looking for interesting things",
                        "All clear ahead",
                        "Navigation systems nominal",
                    ]))

                time.sleep(0.1)

            except KeyboardInterrupt:
                safe_print(f"\n{ICONS['stop']} Manual stop requested")
                break
            except Exception as e:
                safe_print(f"[ERROR] {e}")
                time.sleep(1)

    def start_exploration(self):
        self.running = True
        self.exploration_loop()

    def stop_exploration(self):
        safe_print(f"{ICONS['stop']} Stopping exploration...")
        self.running = False
        self.stop_event.set()
        self.announce_status("Exploration stopped")
        uptime = time.time() - self.start_time
        safe_print(f"\n{ICONS['chart']} Final Statistics:")
        safe_print(f"   Total runtime:     {uptime:.1f} seconds")
        safe_print(f"   Distance traveled: ~{self.total_distance_traveled} steps")
        safe_print(f"   Final state:       {self.current_state.value}")


def main():
    safe_print(f"{ICONS['spider']} Self-Aware PiCrawler Starting...")
    robot = SelfAwarePiCrawler()
    try:
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
