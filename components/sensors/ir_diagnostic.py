"""
ir_diagnostic.py — live IR sensor pin mapper

Run this to figure out which physical leg is wired to which pin.
Break a leg's IR circuit (lift the leg) and the pin will show TRIGGERED.
Everything quiet = idle.

Usage:
    python ir_diagnostic.py
"""

from robot_hat import Pin
import time

SENSORS = [
    ("D3", "front_left"),
    ("D1", "front_right"),
    ("D0", "back_left"),
    ("D2", "back_right"),
]

pins = {name: Pin(pin_id, Pin.IN) for pin_id, name in SENSORS}


def read_all():
    return {name: pins[name].value() for _, name in SENSORS}


def print_status(readings):
    lines = []
    for pin_id, name in SENSORS:
        state = "TRIGGERED" if readings[name] == 1 else "idle"
        lines.append(f"  {pin_id}  {name:<14}  {state}")
    print("\033[H\033[J", end="")  # clear screen
    print("IR Pin Diagnostic — lift a leg to see which pin triggers\n")
    print("\n".join(lines))
    print("\nPress Ctrl+C to exit.")


def main():
    print("Starting IR diagnostic...")
    time.sleep(0.5)
    while True:
        print_status(read_all())
        time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDone.")
