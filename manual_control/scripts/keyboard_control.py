import os
import sys
import json
import threading
from picrawler import Picrawler
from time import sleep
import readchar
from robot_hat import Music, TTS, Pin
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from components.sensors import ps4_control
from components.screens import imageConvert, oled

crawler = Picrawler()
tts = TTS()
speed = 80

manual = '''
Press keys on keyboard or use PS4 D-pad to control PiCrawler!
    W / Up: Forward
    A / Left: Turn left
    S / Down: Backward
    D / Right: Turn right

    Ctrl^C: Quit
'''

# Load static poses from shared JSON
_POSES_FILE = os.path.join(os.path.dirname(__file__), '../../components/motion/poses.json')
with open(_POSES_FILE) as f:
    poses = json.load(f)

spread_out      = poses["spread_out"]
compact         = poses["compact"]
wave_1          = poses["wave_1"]
wave_2          = poses["wave_2"]
smelling_ground = poses["smelling_ground"]
looking_at_sky  = poses["looking_at_sky"]

# Numpy versions of interpolation boundary poses (needed for joystick math)
_smelling_np = np.array(poses["smelling_ground"])
_spread_np   = np.array(poses["spread_out"])
_sky_np      = np.array(poses["looking_at_sky"])

# Joystick config
JOYSTICK_MAX = 32767
DEADZONE = 2000
previous_joystick_value = 0


def normalize_joystick_value(raw_value):
    return np.clip(raw_value / JOYSTICK_MAX, -1, 1)


def interpolate_pose_continuous(current_value, previous_value):
    alpha = 0.1
    return previous_value * (1 - alpha) + current_value * alpha


def clamp_angles(pose):
    return np.clip(pose, -90, 90).astype(int)


def interpolate_pose(joystick_value):
    joystick_value = max(min(joystick_value, 1), -1)
    if joystick_value < 0:
        t = joystick_value + 1
        interpolated = _smelling_np * (1 - t) + _spread_np * t
    else:
        t = joystick_value
        interpolated = _spread_np * (1 - t) + _sky_np * t
    return clamp_angles(interpolated)


def handle_joystick_input(raw_value):
    global previous_joystick_value
    normalized = normalize_joystick_value(raw_value)
    if abs(raw_value) < DEADZONE:
        normalized = 0
    interpolated = interpolate_pose_continuous(normalized, previous_joystick_value)
    new_pose = interpolate_pose(interpolated)
    custom_steps(new_pose)
    previous_joystick_value = interpolated


def adjust_speed(pressure, direction):
    DEADZONE = 28384
    speed_change = 0
    if direction == "R2" and abs(pressure) > DEADZONE:
        speed_change = 5 if pressure > DEADZONE else 1
    elif direction == "L2" and abs(pressure) > DEADZONE:
        speed_change = -2 if pressure > DEADZONE else -1
    if speed_change != 0:
        speed_adjust(speed_change)
    sleep(0.1)


def speed_adjust(change):
    global speed
    speed = int(max(0, min(speed + change, 100)))
    print(f"Speed: {speed}")


def custom_steps(values):
    data = values.tolist() if hasattr(values, 'tolist') else values
    print(f"New step: {data}")
    crawler.do_step(data, speed)
    sleep(0.1)


def handle_input(action, value=0):
    global speed

    if action in ('ps_button_press', 'q'):
        print("Exiting...")
        oled.update_display(header="Keyboard Ctrl", text="Stopped")
        exit()

    if action in ('on_up_arrow_press', 'w'):
        crawler.do_action('forward', 1, speed)
        oled.update_display(header="Moving:", text="Forward")
    elif action in ('on_down_arrow_press', 's'):
        crawler.do_action('backward', 1, speed)
        oled.update_display(header="Moving:", text="Backward")
    elif action in ('on_left_arrow_press', 'a'):
        crawler.do_action('turn left', 1, speed)
        oled.update_display(header="Moving:", text="Turn Left")
    elif action in ('on_right_arrow_press', 'd'):
        crawler.do_action('turn right', 1, speed)
        oled.update_display(header="Moving:", text="Turn Right")
    elif action in ('x_press', 'b'):
        custom_steps(looking_at_sky)
        oled.update_display(header="Pose:", text="Look Up")
    elif action in ('triangle_press', 'y'):
        custom_steps(smelling_ground)
        oled.update_display(header="Pose:", text="Look Down")
    elif action in ('circle_press', 'h'):
        custom_steps(spread_out)
        oled.update_display(header="Pose:", text="Spread Out")
    elif action in ('square_press', 'g'):
        custom_steps(compact)
        oled.update_display(header="Pose:", text="Compact")
    elif action in ('R1_press', 'u'):
        custom_steps(wave_1)
        sleep(0.3)
        custom_steps(wave_2)
        sleep(0.3)
        custom_steps(wave_1)
        sleep(0.3)
        custom_steps(wave_2)
        sleep(0.3)
        tts.say("hello")
        oled.update_display(header="Action:", text="Greeting")
        custom_steps(spread_out)
    elif action in ('L1_press', 't'):
        custom_steps(compact)
        oled.update_display(header="Pose:", text="Compact")
    elif action in ('L3_press', '-'):
        speed = 80
        print(speed)
    elif action in ('R3_press', '+'):
        custom_steps(compact)
        oled.update_display(header="Pose:", text="Compact")
    elif action == 'R3_updown':
        handle_joystick_input(value)
    elif action == 'R3_leftright':
        handle_joystick_input(value)
    elif action == 'L2_press':
        adjust_speed(value, "L2")
    elif action == 'R2_press':
        adjust_speed(value, "R2")


def show_info():
    print("\033[H\033[J", end='')
    print(manual)


def ps4_controller_thread():
    while True:
        try:
            controller = ps4_control.MyController(
                on_input_change=handle_input,
                interface="/dev/input/js0",
                connecting_using_ds4drv=False
            )
            print("PS4 controller connected. Listening for input...")
            tts.say("controller connected")
            controller.listen()
        except Exception as e:
            print(f"Error initializing PS4 controller: {e}")
            print("Retrying in 5 seconds...")
            sleep(5)


def main():
    imageConvert.main()
    oled.update_display(header="Keyboard Ctrl", text="Ready  WASD")
    show_info()

    controller_thread = threading.Thread(target=ps4_controller_thread, daemon=True)
    controller_thread.start()

    while True:
        key = readchar.readkey().lower()
        if key in 'wsadyghbutq-+':
            handle_input(key)
        elif key == readchar.key.CTRL_C:
            oled.update_display(header="Keyboard Ctrl", text="Stopped")
            print("\nQuit")
            break
        sleep(0.02)


if __name__ == "__main__":
    main()
