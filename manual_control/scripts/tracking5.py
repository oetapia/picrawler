#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-Aware PiCrawler Robot
Combines sonar obstacle avoidance, per-leg IR floor detection, MPU-6050
tilt sensing, and active 3-D leg-probe scanning for autonomous navigation.

Active leg probing:
  The IR sensor on each foot detects nearby surfaces (active-low: 0 = surface
  detected, 1 = clear).  While a leg is lifted and moved to a probe position,
  reading 0 means an object is within sensor range at that location; reading 1
  means the path is clear.  This lets the robot scan for walls, steps, and
  overhangs at different heights without any additional hardware.
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
    'scan':      get_icon('🔍', '[SCAN]'),
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


# ---------------------------------------------------------------------------
# Leg → IR sensor key mapping
# Leg indices match Picrawler.do_single_leg():
#   0 = front-left (FL), 1 = front-right (FR)
#   2 = back-left  (BL), 3 = back-right  (BR)
# ---------------------------------------------------------------------------
LEG_IR = {0: 'fl', 1: 'fr', 2: 'bl', 3: 'br'}

# ---------------------------------------------------------------------------
# Active-probe positions  [x, y, z]  used by probe_leg() / scan_*()
#
# Coordinate system (from Picrawler.coord2polar):
#   x  – reach forward from shoulder   (larger = further forward)
#   y  – lateral reach outward         (larger = more to the side)
#   z  – height                        (less negative = higher off ground)
#
# Servo limits (from Picrawler.limit_angle):
#   alpha (elevation) : -90 to  90
#   beta  (extension) : -10 to  90
#   gamma (rotation)  : -60 to  60   →  y / x ratio governs this
#
# Probe design:
#   FORWARD_MID  – leg extended forward at body height  → detects walls & objects
#   FORWARD_LOW  – leg extended forward near floor level → detects step-ups / ledge base
#   SIDE_OUT     – leg swept 90° outward at mid height  → detects side walls
# ---------------------------------------------------------------------------
PROBE = {
    'forward_mid': [80, 10, -20],   # forward, raised (body-height obstacle check)
    'forward_low': [78, 10, -52],   # forward, near floor (step / low-wall check)
    'side_out':    [45, 90, -35],   # straight out to the side at mid height
}
PROBE_SETTLE = 0.12   # seconds to wait after moving leg before reading sensor
PROBE_SPEED  = 90     # servo speed for probe moves (fast but not jerky)

# ---------------------------------------------------------------------------
# Balance compensation leg pose reference points  [x, y, z]
# Leg order: [FL, FR, BL, BR]
#   EXTENDED  – leg pushed fully down → lifts that body corner
#   RETRACTED – leg pulled up        → drops that body corner
#   NEUTRAL   – midpoint standing pose
# Sign matrix (positive = extend leg to compensate):
#   pitch > 0 (nose down): extend front legs  [+1, +1, -1, -1]
#   roll  > 0 (tilt right): extend left legs  [+1, -1, +1, -1]
# ---------------------------------------------------------------------------
BAL_EXTENDED  = [60, 45, -75]
BAL_RETRACTED = [30, 30, -30]
BAL_NEUTRAL   = [45, 37, -52]
BAL_COMPACT   = [[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]]
BAL_PITCH_SIGN = [+1, +1, -1, -1]
BAL_ROLL_SIGN  = [+1, -1, +1, -1]
BAL_MAX_TILT   = 25.0   # degrees → full extension/retraction
BAL_DEAD_ZONE  = 3.0    # degrees → no correction below this
BAL_SPEED      = 60     # servo speed for balance adjustments


def _bal_lerp(a, b, t):
    return [a[j] + t * (b[j] - a[j]) for j in range(3)]


def compute_balance_pose(pitch, roll):
    """Return a 4-leg [[x,y,z],...] pose that compensates pitch/roll."""
    pf = max(-1.0, min(1.0, pitch / BAL_MAX_TILT))
    rf = max(-1.0, min(1.0, roll  / BAL_MAX_TILT))
    pose = []
    for i in range(4):
        f = max(-1.0, min(1.0, BAL_PITCH_SIGN[i] * pf + BAL_ROLL_SIGN[i] * rf))
        if f >= 0.0:
            pose.append(_bal_lerp(BAL_NEUTRAL, BAL_EXTENDED, f))
        else:
            pose.append(_bal_lerp(BAL_RETRACTED, BAL_NEUTRAL, f + 1.0))
    return pose


class RobotState(Enum):
    EXPLORING             = "exploring"
    AVOIDING_OBSTACLE     = "avoiding_obstacle"
    AVOIDING_FLOOR_DANGER = "avoiding_floor_danger"
    TILT_CAUTION          = "tilt_caution"
    STUCK                 = "stuck"
    AIRBORNE              = "airborne"


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

        # Obstacle / stuck config
        self.obstacle_distance = 20   # cm
        self.safe_distance     = 30   # cm
        self.stuck_threshold   = 5

        # State
        self.current_state  = RobotState.EXPLORING
        self.previous_state = RobotState.EXPLORING
        self.running        = False
        self.stop_event     = Event()

        # Counters / tracking
        self.consecutive_obstacles     = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter             = 0
        self.last_successful_move      = time.time()
        self.total_distance_traveled   = 0
        self.start_time                = time.time()

        # Forward scan interval (steps between full forward probes)
        self.fwd_scan_interval      = 5
        self.steps_since_fwd_scan   = 0

        # Side scan interval
        self.side_scan_interval     = 10
        self.steps_since_side_scan  = 0

        # Last scan results cache
        self.last_fwd_scan  = {}
        self.last_side_scan = {'left': False, 'right': False}
        self.known_obstacles = {'left': False, 'right': False}

        self.escape_patterns = [
            [('backward', 2), ('turn left', 3),  ('forward', 1)],
            [('backward', 2), ('turn right', 3), ('forward', 1)],
            [('turn left', 4),  ('forward', 2)],
            [('turn right', 4), ('forward', 2)],
            [('backward', 3), ('turn left', 2), ('turn right', 2), ('forward', 1)],
        ]

        # Compact/neutral poses (used for airborne tuck)
        self.pose_compact = np.array([[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]])

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

    # ------------------------------------------------------------------
    # Sonar
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
        if not self.accel_available:
            return 0.0, 0.0
        try:
            return accelerometer.get_tilt()
        except Exception:
            return 0.0, 0.0

    def _pick_turn_from_accel(self):
        """Return 'turn left' / 'turn right' toward the uphill side, or None."""
        _, roll = self._get_tilt()
        if roll > 3:
            return 'turn left'
        if roll < -3:
            return 'turn right'
        return None

    def apply_balance(self):
        """
        Flex legs to keep the body level based on current pitch/roll.
        Called between gait steps so it doesn't fight the walking motion.
        """
        if not self.accel_available:
            return
        try:
            pitch, roll = accelerometer.get_tilt()
            if abs(pitch) < BAL_DEAD_ZONE and abs(roll) < BAL_DEAD_ZONE:
                pose = [list(BAL_NEUTRAL)] * 4
            else:
                pose = compute_balance_pose(pitch, roll)
                safe_print(f"{ICONS['tilt']} Balance: pitch={pitch:+.1f} roll={roll:+.1f}")
            self.crawler.do_step(pose, BAL_SPEED)
        except Exception as e:
            safe_print(f"Balance error: {e}")

    def check_and_apply_tilt(self):
        """Adjust speed and state from MPU-6050 pitch/roll."""
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
    # Per-leg IR floor sensing (passive - legs on ground)
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
        Returns (danger_type, turn_hint) or (None, None).
        """
        fl, fr, bl, br = legs['fl'], legs['fr'], legs['bl'], legs['br']
        count = fl + fr + bl + br

        if count == 0:
            return None, None
        if count == 4:
            return 'airborne', None
        if count == 1:
            if fl: return 'corner_fl', 'right'
            if fr: return 'corner_fr', 'left'
            if bl: return 'corner_bl', 'right'
            if br: return 'corner_br', 'left'
        if count == 2:
            if fl and fr: return 'front',    None
            if bl and br: return 'back',     None
            if fl and bl: return 'left',     'right'
            if fr and br: return 'right',    'left'
            if fl and br: return 'diagonal', 'right'
            if fr and bl: return 'diagonal', 'left'
        return 'multiple', None

    def handle_floor_danger_smart(self, danger_type, turn_hint):
        """React to per-corner floor danger."""
        if danger_type is None:
            return False

        self.change_state(RobotState.AVOIDING_FLOOR_DANGER)
        self.consecutive_floor_dangers += 1

        if danger_type == 'airborne':
            pitch, roll = self._get_tilt()
            if self.accel_available and (abs(pitch) > 30 or abs(roll) > 30):
                self.change_state(RobotState.AIRBORNE)
                self.announce_status("Airborne! Tucking legs")
                self.crawler.do_step(self.pose_compact.tolist(), self.speed)
            else:
                self.announce_status("All sensors triggered - backing up")
                self.crawler.do_action('backward', 2, self.speed)
                time.sleep(0.4)
                turn = self._pick_turn_from_accel() or 'turn right'
                self.crawler.do_action(turn, 2, self.speed)
            return True

        safe_print(f"{ICONS['warning']} Floor danger: {danger_type}  hint={turn_hint}")

        if danger_type in ('front', 'corner_fl', 'corner_fr'):
            self.announce_status("Ledge ahead!")
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.4)
            if turn_hint:
                self.crawler.do_action(f'turn {turn_hint}', 2, self.speed)
            else:
                turn = self._pick_turn_from_accel() or 'turn right'
                self.crawler.do_action(turn, 2, self.speed)

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

        elif danger_type in ('left', 'right'):
            self.crawler.do_action(f'turn {turn_hint}', 2, self.speed)

        else:
            self.announce_status("Multiple danger zones!")
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)
            turn = self._pick_turn_from_accel() or 'turn right'
            self.crawler.do_action(turn, 3, self.speed)

        return True

    # ------------------------------------------------------------------
    # Active 3-D leg probing
    # ------------------------------------------------------------------

    def probe_leg(self, leg_idx, coord):
        """
        Move one leg to coord, read its IR sensor, return whether an object
        was detected at that position.

        Sensor logic (active-low):
          value == 0  →  surface within range  →  object detected  (True)
          value == 1  →  nothing nearby        →  clear            (False)

        The robot's other legs remain in place.  The calling code is
        responsible for saving / restoring full leg positions if needed.
        """
        try:
            self.crawler.do_single_leg(leg_idx, coord, speed=PROBE_SPEED)
            time.sleep(PROBE_SETTLE)
            legs = ir_distance.read_legs()
            return legs[LEG_IR[leg_idx]] == 0   # 0 = surface detected
        except Exception as e:
            safe_print(f"probe_leg error (leg {leg_idx}): {e}")
            return False

    def scan_forward(self):
        """
        Sweep FL (leg 0) and FR (leg 1) through two heights in front of the
        robot to build a simple height profile of what lies ahead.

        Returns dict:
          {
            'fl_mid': bool,   True = object at body height on front-left
            'fl_low': bool,   True = object at floor level on front-left
            'fr_mid': bool,
            'fr_low': bool,
          }

        Height interpretation:
          mid=True, low=True  →  solid wall or large obstacle
          mid=False, low=True →  low step / raised threshold (can try step-over)
          mid=True, low=False →  hanging obstacle / overhang
          both False          →  path clear at this side
        """
        safe_print(f"{ICONS['scan']} Forward leg scan...")
        saved = self.crawler.current_step_all_leg_value()
        result = {}

        for leg, key in ((0, 'fl'), (1, 'fr')):
            result[f'{key}_mid'] = self.probe_leg(leg, PROBE['forward_mid'])
            result[f'{key}_low'] = self.probe_leg(leg, PROBE['forward_low'])

        # Restore standing position
        try:
            self.crawler.do_step(saved, self.speed)
            time.sleep(0.15)
        except Exception as e:
            safe_print(f"scan_forward restore error: {e}")

        self._log_scan_result('forward', result)
        self.last_fwd_scan = result
        return result

    def scan_sides(self):
        """
        Extend each front leg outward (y=90) to probe for side walls at mid
        height, then do the same for the back legs.

        Returns {'left': bool, 'right': bool}
          True = obstacle detected on that side within sensor range.
        """
        safe_print(f"{ICONS['scan']} Side leg scan...")
        saved = self.crawler.current_step_all_leg_value()
        result = {'left': False, 'right': False}

        # Front legs probe their outward side
        result['left']  |= self.probe_leg(0, PROBE['side_out'])   # FL → left
        result['right'] |= self.probe_leg(1, PROBE['side_out'])   # FR → right
        # Back legs confirm
        result['left']  |= self.probe_leg(2, PROBE['side_out'])   # BL → left
        result['right'] |= self.probe_leg(3, PROBE['side_out'])   # BR → right

        try:
            self.crawler.do_step(saved, self.speed)
            time.sleep(0.15)
        except Exception as e:
            safe_print(f"scan_sides restore error: {e}")

        self._log_scan_result('sides', result)
        self.last_side_scan = result
        self.known_obstacles.update(result)
        return result

    def _log_scan_result(self, scan_type, result):
        """Print a compact scan summary."""
        if scan_type == 'forward':
            def mark(v): return 'X' if v else '.'
            safe_print(
                f"   scan fwd  FL: mid={mark(result['fl_mid'])} low={mark(result['fl_low'])}  "
                f"FR: mid={mark(result['fr_mid'])} low={mark(result['fr_low'])}"
            )
        else:
            safe_print(
                f"   scan sides  L={'X' if result['left'] else '.'}  R={'X' if result['right'] else '.'}"
            )

    def _interpret_forward_scan(self, scan):
        """
        Convert a forward scan result to a human-readable obstacle description
        and a navigation hint.

        Returns (description, is_steppable)
          description   – short string for logging / TTS
          is_steppable  – True if only floor-level (low) obstacles: step may be
                          climbable, False if mid-height wall is present
        """
        wall_left  = scan.get('fl_mid', False)
        wall_right = scan.get('fr_mid', False)
        step_left  = scan.get('fl_low', False) and not wall_left
        step_right = scan.get('fr_low', False) and not wall_right

        if not any(scan.values()):
            return "path clear", False

        parts = []
        if wall_left and wall_right:
            parts.append("wall ahead")
            steppable = False
        elif wall_left:
            parts.append("wall front-left")
            steppable = False
        elif wall_right:
            parts.append("wall front-right")
            steppable = False
        else:
            steppable = True

        if step_left:  parts.append("step front-left")
        if step_right: parts.append("step front-right")

        return ", ".join(parts), steppable

    # ------------------------------------------------------------------
    # Obstacle avoidance (sonar + forward scan)
    # ------------------------------------------------------------------

    def smart_obstacle_avoidance(self, front_distance):
        self.change_state(RobotState.AVOIDING_OBSTACLE)
        self.consecutive_obstacles += 1

        # Run a forward leg scan to characterise the obstacle
        fwd = self.scan_forward()
        desc, steppable = self._interpret_forward_scan(fwd)
        safe_print(f"{ICONS['obstacle']} Obstacle at {front_distance}cm - {desc}")

        if front_distance <= 10:
            self.announce_status("Emergency! Very close obstacle!")
            self.crawler.do_action('backward', 3, self.speed)
            time.sleep(0.5)
        else:
            self.crawler.do_action('backward', 2, self.speed)
            time.sleep(0.3)

        # Refresh side knowledge from last scan
        left_clear  = not self.known_obstacles.get('left', False)
        right_clear = not self.known_obstacles.get('right', False)

        # Use forward scan to bias side preference
        if fwd.get('fl_mid') and not fwd.get('fr_mid'):
            # Left side has the wall → prefer right even if scan says clear
            left_clear = False
        elif fwd.get('fr_mid') and not fwd.get('fl_mid'):
            right_clear = False

        if left_clear and right_clear:
            turn_direction = self._pick_turn_from_accel() or 'turn right'
            safe_print(f"   Both sides clear - {turn_direction} (accel-guided)")
        elif left_clear:
            turn_direction = 'turn left'
            safe_print(f"   {ICONS['check']} Turning left - right blocked")
        elif right_clear:
            turn_direction = 'turn right'
            safe_print(f"   {ICONS['check']} Turning right - left blocked")
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
        time_since = time.time() - self.last_successful_move
        return (self.consecutive_obstacles     > 4 or
                self.consecutive_floor_dangers > 3 or
                time_since                     > 10)

    # ------------------------------------------------------------------
    # Forward motion
    # ------------------------------------------------------------------

    def move_forward_safely(self):
        safe_print(f"{ICONS['forward']} Moving forward (speed={self.speed})")
        self.crawler.do_action('forward', 1, self.speed)
        self.last_successful_move      = time.time()
        self.total_distance_traveled  += 1
        self.steps_since_fwd_scan     += 1
        self.steps_since_side_scan    += 1

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
        safe_print(f"   State:             {self.current_state.value}")
        safe_print(f"   Uptime:            {uptime:.1f}s")
        safe_print(f"   Distance:          ~{self.total_distance_traveled} steps")
        safe_print(f"   Speed:             {self.speed}")
        safe_print(f"   Obstacles (consec): {self.consecutive_obstacles}")
        safe_print(f"   Floor dangers:     {self.consecutive_floor_dangers}")
        safe_print(f"   Stuck counter:     {self.stuck_counter}")
        safe_print(f"   Known obstacles:   L={self.known_obstacles['left']}  R={self.known_obstacles['right']}")
        if self.accel_available:
            safe_print(f"   Tilt:              pitch={pitch:+.1f}deg  roll={roll:+.1f}deg")
        if self.last_fwd_scan:
            desc, _ = self._interpret_forward_scan(self.last_fwd_scan)
            safe_print(f"   Last fwd scan:     {desc}")

    # ------------------------------------------------------------------
    # Main exploration loop
    # ------------------------------------------------------------------

    def exploration_loop(self):
        safe_print(f"{ICONS['rocket']} Starting autonomous exploration...")
        self.announce_status("Beginning exploration mode")

        status_interval  = 30
        last_status_time = time.time()

        while self.running and not self.stop_event.is_set():
            try:
                if time.time() - last_status_time > status_interval:
                    self.print_status()
                    last_status_time = time.time()

                # 1. Tilt check → adjusts self.speed
                self.check_and_apply_tilt()

                # 2. Floor danger (highest priority - edges / airborne)
                legs = self.get_leg_sensors()
                danger_type, turn_hint = self.classify_floor_danger(legs)
                if danger_type:
                    if self.handle_floor_danger_smart(danger_type, turn_hint):
                        continue

                # 3. Periodic side scan - updates known_obstacles
                if self.steps_since_side_scan >= self.side_scan_interval:
                    self.scan_sides()
                    self.steps_since_side_scan = 0

                # 4. Sonar check
                distance = self.get_obstacle_distance()
                avoid_threshold = (self.safe_distance
                                   if self.current_state == RobotState.AVOIDING_OBSTACLE
                                   else self.obstacle_distance)

                if 0 < distance <= avoid_threshold:
                    # smart_obstacle_avoidance runs its own forward leg scan internally
                    if self.smart_obstacle_avoidance(distance):
                        self.steps_since_fwd_scan = 0
                        continue

                # 5. Periodic forward leg scan (independent of sonar)
                if self.steps_since_fwd_scan >= self.fwd_scan_interval:
                    fwd = self.scan_forward()
                    self.steps_since_fwd_scan = 0
                    desc, steppable = self._interpret_forward_scan(fwd)
                    if any(fwd.values()):
                        safe_print(f"{ICONS['scan']} Forward scan: {desc}")
                        if not steppable:
                            # Treat as a low-confidence obstacle - reduce speed / side-scan
                            self.speed = max(self.caution_speed, self.speed - 10)
                            self.scan_sides()
                        # If only steppable low-steps, keep going but cautiously

                # 6. Stuck check
                if self.is_stuck():
                    self.stuck_counter += 1
                    if self.stuck_counter >= self.stuck_threshold:
                        self.execute_escape_pattern()
                        continue

                # 7. Move forward
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

                # Flex legs to stay level between gait steps
                self.apply_balance()

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
        self.crawler.do_step(BAL_COMPACT, 40)


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
