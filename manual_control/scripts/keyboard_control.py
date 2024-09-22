import os
import sys
import threading
import logging
from picrawler import Picrawler
from time import sleep
import readchar
from datetime import datetime  # Add this import

# Add the 'components' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))
from sensors import ps4_control
from sensors import accelerometer



crawler = Picrawler()


speed = 80

manual = '''
Press keys on keyboard or use PS4 D-pad to control PiCrawler!
    W / Up: Forward
    A / Left: Turn left
    S / Down: Backward
    D / Right: Turn right

    Ctrl^C: Quit
'''

step_two=[[45, 45, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]]
step_one=[[45, 45, 45], [45, 0, -75], [45, 0, -75], [45, 0, -75]]
step_three=[[75, 55, 45], [45, 0, -75], [45, 0, -75], [45, 0, -75]]
step_four=[[-75, 50, 45], [45, 0, -75], [45, 0, -75], [45, 0, -75]]


def speed_adjust(change):
    global speed
    print(f"initial: {speed}")
    # Update speed and ensure it stays within a defined range (e.g., 0 to 100)
    speed += change
    speed = max(0, min(speed, 100))  # Keep speed between 0 and 100
    print(f"Current speed: {speed}")

def custom_steps(name):
    
    #current_step = crawler.get_leg_positions()

    # Debug: Print current step
    #print(f"Current step: {current_step}")
    
    """ new_step = []
    for leg_step in current_step:
        x, y, z = leg_step
        new_step.append([x, y, z + z_offset])
    
    # Debug: Print new step
    print(f"New step: {new_step}") """
    crawler.do_step(name,speed)
    
    # Apply the new step with the z-axis adjust


def handle_input(action,value=0):

    # Read accelerometer data
    #ax, ay, az = accelerometer.read_accel_data()  # Call the function to read data
    #print(f"AX: {ax}, AY: {ay}, AZ: {az}")    # Handle PS4 controller input and keyboard input
    #logging.info(f"AX: {ax}, AY: {ay}, AZ: {az}")  # Log the accelerometer data


        # Handle PS4 controller input and keyboard input
    if action in ('ps_button_press', 'q'):  # Adjust this if you have a different mapping
        print("Exiting...")
        exit()  # Exit the program

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
    elif action in ('x_press', 'b'):
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
        print("compact")
        # Adjust Z-axis to simulate standing
        custom_steps(step_one)  # Example value, adjust as needed
    elif action in ('square_press', 'g'):
        print("custom 2")
        # Adjust Z-axis to simulate standing
        custom_steps(step_two)  # Example value, adjust as needed        

    elif action in ('R1_press', 'u'):
        print("custom 3")
        # Adjust Z-axis to simulate standing
        custom_steps(step_three)  # Example value, adjust as needed       

    elif action in ('L1_press', 't'):
        print("custom 4")
        # Adjust Z-axis to simulate standing
        custom_steps(step_four)  # Example value, adjust as needed      
    
    elif action in ('L3_press', '-'):
        print("slower")
        # Adjust Z-axis to simulate standing
        speed_adjust(-10)  # Example value, adjust as needed           
    
    elif action in ('R3_press', '+'):
        print("faster")
        # Adjust Z-axis to simulate standing
        speed_adjust(+10)  # Example value, adjust as needed               

def show_info():
    print("\033[H\033[J", end='')  # clear terminal window
    print(manual)

from time import sleep

def ps4_controller_thread():
    while True:
        try:
            # Attempt to initialize the PS4 controller
            controller = ps4_control.MyController(
                on_input_change=handle_input,
                interface="/dev/input/js0",
                connecting_using_ds4drv=False
            )
            print("PS4 controller connected. Listening for input...")
            controller.listen()  # Start listening for input events
            
        except Exception as e:
            print(f"Error initializing PS4 controller: {e}")
            print("Retrying in 5 seconds...")
            sleep(5)  # Wait for 5 seconds before retrying the connection




def main():
    show_info()
    

    # Start PS4 controller thread
    controller_thread = threading.Thread(target=ps4_controller_thread, daemon=True)
    controller_thread.start()


    # Initialize the accelerometer
    #accelerometer.main()  # Ensure this is your initialization function

    
    while True:

        
        key = readchar.readkey()
        key = key.lower()

        if key in 'wsadyghbutq-+':
            handle_input(key)  # Handle keyboard input
        
        elif key == readchar.key.CTRL_C:
            print("\nQuit")
            break

        sleep(0.02)

if __name__ == "__main__":
    main()
