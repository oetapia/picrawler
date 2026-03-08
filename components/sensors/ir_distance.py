from robot_hat import Pin, TTS
import time

# One IR sensor per leg on digital pins D0-D3 (active-low: 0 = floor detected, 1 = no floor)
front_left  = Pin("D0", Pin.IN)
front_right = Pin("D1", Pin.IN)
back_left   = Pin("D2", Pin.IN)
back_right  = Pin("D3", Pin.IN)

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

def main():
    while True:
        proximity_status = check_proximity()
        print(proximity_status)
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped.")
