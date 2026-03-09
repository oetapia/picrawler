from robot_hat import Pin, TTS
import time

# One IR sensor per leg on digital pins D0-D3 (active-low: 0 = floor detected, 1 = no floor)
front_left  = Pin("D3", Pin.IN)
front_right = Pin("D1", Pin.IN)
back_left   = Pin("D0", Pin.IN)
back_right  = Pin("D2", Pin.IN)

tts = TTS()

def check_proximity():
    fl = front_left.value()
    fr = front_right.value()
    bl = back_left.value()
    br = back_right.value()

    # All legs off the floor
    if fl == 1 and fr == 1 and bl == 1 and br == 1:
        return {"airborne"}

    dangers = set()
    if fl == 1 or fr == 1:
        dangers.add("danger_front")
    if bl == 1 or br == 1:
        dangers.add("danger_back")
    if fl == 1 or bl == 1:
        dangers.add("danger_left")
    if fr == 1 or br == 1:
        dangers.add("danger_right")

    if dangers:
        tts.say(" and ".join(sorted(d.replace("danger_", "") for d in dangers)))

    return dangers if dangers else {"floor_all"}

def read_legs():
    """Return individual sensor states as a dict.
    Keys: 'fl', 'fr', 'bl', 'br'.  0 = floor detected, 1 = no floor (danger/lifted)."""
    return {
        'fl': front_left.value(),
        'fr': front_right.value(),
        'bl': back_left.value(),
        'br': back_right.value(),
    }

def diagnose():
    """Interactive diagnostic: shows idle state and highlights any pin that breaks the circuit."""
    SENSORS = [
        ("D0", "front_left",  front_left),
        ("D1", "front_right", front_right),
        ("D2", "back_left",   back_left),
        ("D3", "back_right",  back_right),
    ]

    print("IR sensor diagnostic - break a circuit to see which pin triggers.")
    print("Press Ctrl+C to exit.\n")

    prev = {}

    while True:
        readings = {pin: sensor.value() for pin, _, sensor in SENSORS}
        triggered = [(pin, name) for pin, name, _ in SENSORS if readings[pin] == 1]

        if triggered:
            for pin, name in triggered:
                if prev.get(pin) != 1:
                    print(f"  TRIGGERED  {pin} ({name})")
            for pin, name in [(p, n) for p, n, _ in SENSORS if readings[p] == 0]:
                if prev.get(pin) != 0:
                    print(f"  restored   {pin} ({name})")
        else:
            if any(prev.get(pin) != 0 for pin, *_ in SENSORS):
                print("  idle - all sensors detecting floor")

        prev = dict(readings)
        time.sleep(0.05)


def main():
    while True:
        proximity_status = check_proximity()
        print(proximity_status)
        time.sleep(1)

if __name__ == "__main__":
    import sys
    try:
        if "--diagnose" in sys.argv:
            diagnose()
        else:
            main()
    except KeyboardInterrupt:
        print("\nProgram stopped.")
