import os
import sys
import threading
from picrawler import Picrawler
from time import sleep
import readchar

# Add the 'components' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))
from sensors import ps4_control

crawler = Picrawler()
speed = 90

manual = '''
Press keys on keyboard or use PS4 D-pad to control PiCrawler!
    W / Up: Forward
    A / Left: Turn left
    S / Down: Backward
    D / Right: Turn right

    Ctrl^C: Quit
'''


def adjust_z_axis(z_offset):
    current_step = crawler.move_list.get('current', [[0, 0, 0]])
    print(current_step)

    #new_step=[[45, 45, -75], [45, 0, -75], [45, 0, -30], [45, 45, -75]]
    
    """    # Retrieve current step or default to neutral
    current_step = crawler.move_list.get('current', [[0, 0, 0]])
    
    # Debug: Print current step
    print(f"Current step: {current_step}")
    
    # Ensure current_step is a valid list of leg positions
    if not all(isinstance(step, list) and len(step) == 3 for step in current_step):
        print("Error: Invalid current_step format. Expected a list of [x, y, z] lists.")
        return

    # Create new step with adjusted Z-axis
    new_step = []
    for leg_step in current_step:
        if len(leg_step) != 3:
            print(f"Error: Invalid leg_step format: {leg_step}. Expected [x, y, z].")
            continue
        
        x, y, z = leg_step
        new_step.append([x, y, z + z_offset])
    
    # Debug: Print new step
    print(f"New step: {new_step}")
    
    # Apply new step """
    #crawler.do_step(new_step, speed)


def handle_input(action,value=0):
    # Handle PS4 controller input and keyboard input
    if action in ('on_up_arrow_press', 'w'):
        print("Forward")
        crawler.do_action('forward', 1, speed)
    elif action in ('on_down_arrow_press', 's'):
        print("Backward")
        crawler.do_action('backward', 1, speed)
    elif action in ('on_left_arrow_press', 'a'):
        print("Turn left")
        crawler.do_action('turn left', 1, speed)
    elif action in ('on_right_arrow_press', 'd'):
        print("Turn right")
        crawler.do_action('turn right', 1, speed)
    elif action in ('x_press', 'x'):
        print("sit")
        #crawler.do_action('turn right', 1, speed
        sit_step = crawler.move_list['sit'][0]
        crawler.do_step(sit_step, speed)
        #crawler.do_step(stand_step, speed)
    elif action in ('triangle_press', 'y'):
        print("stand")
        #crawler.do_action('turn right', 1, speed
        stand_step = crawler.move_list['stand'][0]
        crawler.do_step(stand_step, speed)
        #crawler.do_step(stand_step, speed)
    elif action in ('circle_press', 'h'):
        print("z axis")
        # Adjust Z-axis to simulate standing
        adjust_z_axis(0)  # Example value, adjust as needed

def show_info():
    print("\033[H\033[J", end='')  # clear terminal window
    print(manual)

def ps4_controller_thread():
    controller = ps4_control.MyController(
        on_input_change=handle_input,
        interface="/dev/input/js0",
        connecting_using_ds4drv=False
    )
    try:
        controller.listen()
    except Exception as e:
        print(f"Error initializing PS4 controller: {e}")

def main():
    show_info()

    # Start PS4 controller thread
    controller_thread = threading.Thread(target=ps4_controller_thread, daemon=True)
    controller_thread.start()

    while True:
        key = readchar.readkey()
        key = key.lower()

        if key in 'wsadxygh':
            handle_input(key)  # Handle keyboard input
        
        elif key == readchar.key.CTRL_C:
            print("\nQuit")
            break

        sleep(0.02)

if __name__ == "__main__":
    main()
