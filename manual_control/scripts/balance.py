#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Active balance compensation for PiCrawler using MPU-6050.

Instead of walking, the robot flexes each leg independently to keep
the body level.  Each leg is blended between a retracted (high corner)
and extended (low corner) position proportional to measured pitch/roll.

Leg order: [FL, FR, BL, BR]  (0-front-left, 1-front-right,
                                2-back-left,  3-back-right)

Compensation sign matrix (positive = extend leg to lift that body corner):
          pitch > 0 (nose down)  ->  extend front legs, retract back
          roll  > 0 (tilt right) ->  extend left  legs, retract right
          [FL, FR, BL, BR]
PITCH:    [+1, +1, -1, -1]
ROLL:     [+1, -1, +1, -1]
"""

import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from picrawler import Picrawler
from components.sensors import accelerometer

# [EMOJI]
# Leg pose reference points  [x, y, z]
# [EMOJI]

# Fully extended downward: pushes that body corner UP
EXTENDED  = [60, 45, -75]

# Fully retracted upward: lets that body corner DOWN
RETRACTED = [30, 30, -30]

# Midpoint neutral standing pose (used when level)
NEUTRAL   = [45, 37, -52]

# Known-good starting pose (robot tucked, compact)
RESET_POSE = [[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]]

# [EMOJI]
# Tuning
# [EMOJI]

# Tilt angle (degrees) mapped to full extension/retraction
MAX_TILT  = 25.0

# Below this tilt, return to neutral (prevents jitter on flat surfaces)
DEAD_ZONE = 3.0

# Servo speed for balance corrections (lower = smoother)
SPEED = 60

# Loop period (seconds)
LOOP_HZ = 0.08   # ~12 Hz

# [EMOJI]
# Per-leg signs  [FL, FR, BL, BR]
# [EMOJI]
PITCH_SIGN = [+1, +1, -1, -1]
ROLL_SIGN  = [+1, -1, +1, -1]


def lerp(a, b, t):
    """Linear interpolate between two 3-element coordinate lists."""
    return [a[j] + t * (b[j] - a[j]) for j in range(3)]


def compute_pose(pitch, roll):
    """
    Return a 4-leg pose [[x,y,z], ...] that compensates for the given
    pitch and roll angles.

    factor per leg ranges from -1.0 (fully retracted) to +1.0 (fully extended):
      0.0  ->  NEUTRAL
     +1.0  ->  EXTENDED
     -1.0  ->  RETRACTED
    """
    pitch_factor = max(-1.0, min(1.0, pitch / MAX_TILT))
    roll_factor  = max(-1.0, min(1.0, roll  / MAX_TILT))

    pose = []
    for i in range(4):
        factor = PITCH_SIGN[i] * pitch_factor + ROLL_SIGN[i] * roll_factor
        factor = max(-1.0, min(1.0, factor))

        if factor >= 0.0:
            leg = lerp(NEUTRAL, EXTENDED, factor)
        else:
            leg = lerp(RETRACTED, NEUTRAL, factor + 1.0)

        pose.append(leg)

    return pose


def run_balance_loop(crawler):
    print("Balance loop running. Press Ctrl+C to stop.")
    print("pitch=0.0deg  roll=0.0deg", end='\r', flush=True)

    while True:
        try:
            pitch, roll = accelerometer.get_tilt()

            # If essentially level, hold neutral standing pose
            if abs(pitch) < DEAD_ZONE and abs(roll) < DEAD_ZONE:
                pose = [list(NEUTRAL)] * 4
                print("[level  pitch=%+.1fdeg  roll=%+.1fdeg]" % (pitch, roll),
                      end='\r', flush=True)
            else:
                pose = compute_pose(pitch, roll)
                print("[pitch=%+.1fdeg  roll=%+.1fdeg]  legs=%s" % (
                    pitch, roll,
                    " ".join("[%.0f,%.0f,%.0f]" % tuple(l) for l in pose)
                ))

            crawler.do_step(pose, SPEED)
            time.sleep(LOOP_HZ)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print("\n[ERROR] %s" % e)
            time.sleep(0.5)


def main():
    print("Initialising PiCrawler balance system...")

    crawler = Picrawler()

    try:
        accelerometer.wake()
        time.sleep(0.1)
        print("MPU-6050 ready.")
    except Exception as e:
        print("ERROR: Cannot initialise accelerometer: %s" % e)
        sys.exit(1)

    # Move to known reset pose, then transition to neutral standing
    print("Resetting to known pose...")
    crawler.do_step(RESET_POSE, 40)
    time.sleep(1.0)

    print("Moving to neutral standing pose...")
    crawler.do_step([list(NEUTRAL)] * 4, 40)
    time.sleep(1.0)

    try:
        run_balance_loop(crawler)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        print("Returning to compact pose...")
        crawler.do_step(RESET_POSE, 40)


if __name__ == '__main__':
    main()
