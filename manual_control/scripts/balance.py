#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Balance compensation for PiCrawler.

Reads pitch and roll from the MPU-6050 accelerometer and makes small
corrective leg movements to keep the robot body level:

  Pitch > 0  (nose tilts down / forward)  →  step backward
  Pitch < 0  (nose tilts up  / backward)  →  step forward
  Roll  > 0  (tilts right)                →  turn left
  Roll  < 0  (tilts left)                 →  turn right

Corrections are proportional: larger tilt = more steps per cycle.
The loop runs at ~10 Hz; when level, the robot stands still.
"""

import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from picrawler import Picrawler
from components.sensors import accelerometer

# ──────────────────────────────────────────────────────────────────────────────
# Tuning parameters
# ──────────────────────────────────────────────────────────────────────────────

# Tilt (degrees) below which no correction is applied — prevents jitter
DEAD_ZONE = 5.0

# Tilt bands → number of corrective steps taken per loop iteration
#   (tilt_min, tilt_max) → steps
CORRECTION_BANDS = [
    (5.0,  12.0, 1),   # gentle tilt  → 1 step
    (12.0, 22.0, 2),   # moderate     → 2 steps
    (22.0, 999,  3),   # steep        → 3 steps
]

# Servo speed for corrective moves (lower = smoother, higher = snappier)
CORRECTION_SPEED = 55

# Seconds to pause after a correction to let the robot settle before
# re-reading the accelerometer
SETTLE_DELAY = 0.25

# Main loop period (seconds) when no correction was needed
IDLE_DELAY = 0.10

# ──────────────────────────────────────────────────────────────────────────────

def _steps_for_tilt(tilt_deg: float) -> int:
    """Return the number of corrective steps for a given tilt magnitude."""
    mag = abs(tilt_deg)
    for lo, hi, steps in CORRECTION_BANDS:
        if lo <= mag < hi:
            return steps
    return 0  # below dead-zone


def _pitch_action(pitch: float):
    """Return the do_action name that counters the given pitch, or None."""
    if pitch > DEAD_ZONE:
        return 'backward'   # nose tilted down → step back to shift weight
    if pitch < -DEAD_ZONE:
        return 'forward'    # nose tilted up   → step forward
    return None


def _roll_action(roll: float):
    """Return the do_action name that counters the given roll, or None."""
    if roll > DEAD_ZONE:
        return 'turn left'   # tilted right → turn left
    if roll < -DEAD_ZONE:
        return 'turn right'  # tilted left  → turn right
    return None


def run_balance_loop(crawler: Picrawler) -> None:
    print("Balance loop running. Press Ctrl+C to stop.\n")

    while True:
        try:
            pitch, roll = accelerometer.get_tilt()

            pitch_action = _pitch_action(pitch)
            roll_action  = _roll_action(roll)

            corrected = False

            # Prioritise whichever axis is more tilted
            if abs(pitch) >= abs(roll) and pitch_action:
                steps = _steps_for_tilt(pitch)
                print("[pitch %+.1fdeg] -> %s x%d" % (pitch, pitch_action, steps))
                crawler.do_action(pitch_action, steps, CORRECTION_SPEED)
                corrected = True

            elif roll_action:
                steps = _steps_for_tilt(roll)
                print("[roll  %+.1fdeg] -> %s x%d" % (roll, roll_action, steps))
                crawler.do_action(roll_action, steps, CORRECTION_SPEED)
                corrected = True

            else:
                print("[level  pitch=%+.1fdeg  roll=%+.1fdeg]" % (pitch, roll), end='\r', flush=True)

            time.sleep(SETTLE_DELAY if corrected else IDLE_DELAY)

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
        print("MPU-6050 accelerometer ready.")
    except Exception as e:
        print(f"ERROR: Cannot initialise accelerometer: {e}")
        sys.exit(1)

    # Start from a known standing position
    crawler.do_action('stand', 1, CORRECTION_SPEED)
    time.sleep(0.5)

    try:
        run_balance_loop(crawler)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        crawler.do_action('stand', 1, CORRECTION_SPEED)


if __name__ == '__main__':
    main()
