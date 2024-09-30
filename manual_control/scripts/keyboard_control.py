import os
import sys
import threading
import logging
from picrawler import Picrawler
from time import sleep
import readchar
from datetime import datetime  # Add this import
from robot_hat import Music, TTS, Pin
import numpy as np

# Add the 'components' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))
from sensors import ps4_control
from sensors import accelerometer



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

spread_out=np.array([[45, 45, -45], [45, 45, -45], [45, 45, -45], [45, 45, -45]])
compact=np.array([[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]])
wave_1 = np.array([[45, 45, -45],[-15, 90, 60], [45, 45, -45], [45, 45, -45]])
wave_2 = np.array([[45, 45, -45],[15, 45, 30], [45, 45, -45], [45, 45, -45]])
smelling_ground = np.array([[30, 30, -30], [30, 30, -30], [60, 45, -75], [60, 45, -75]])
looking_at_sky = np.array([[60, 45, -75], [60, 45, -75], [30, 30, -30], [30, 30, -30]])

# Pose definitions (same as before)
smelling_ground2 = np.array([[30, 30, -30], [30, 30, -30], [60, 45, -75], [60, 45, -75]])
spread_out2=np.array([[45, 45, -45], [45, 45, -45], [45, 45, -45], [45, 45, -45]])
looking_at_sky2 = np.array([[60, 45, -75], [60, 45, -75], [30, 30, -30], [30, 30, -30]])


# Joystick values range
JOYSTICK_MAX = 32767
JOYSTICK_MIN = -32767
THRESHOLD = 3000  # Trigger action when joystick moves significantly
DEADZONE = 2000   # Ignore small changes near the center

# Previous stable joystick value
previous_joystick_value = 0

# Function to normalize joystick input
def normalize_joystick_value(raw_value):
    return np.clip(raw_value / JOYSTICK_MAX, -1, 1)


# Function to check for significant changes in joystick value
def is_significant_change(new_value, old_value, threshold):
    print(f"significant change {new_value - old_value}")
    return abs(new_value - old_value) > threshold

# Time-based interpolation to smooth out the movement
def interpolate_pose_continuous(current_value, previous_value):
    # Assuming some smoothing factor for gradual transition
    alpha = 0.1  # Smoothing factor (between 0 and 1)
    
    # Gradual interpolation between the old and new pose
    return previous_value * (1 - alpha) + current_value * alpha

def clamp_angles(pose):
    return np.clip(pose, -90, 90).astype(int)  # Clamp and convert to integers

# Function to interpolate between poses based on joystick value
def interpolate_pose(joystick_value):
    # Ensure joystick_value is within the valid range [-1, 1]
    joystick_value = max(min(joystick_value, 1), -1)

    if joystick_value < 0:
        # Interpolate between smelling_ground2 and spread_out2
        t = (joystick_value + 1)  # Scale from [-1, 0] to [0, 1]
        interpolated_pose = (smelling_ground2 * (1 - t) + spread_out2 * t)
    else:
        # Interpolate between spread_out2 and looking_at_sky2
        t = joystick_value  # Scale from [0, 1]
        interpolated_pose = (spread_out2 * (1 - t) + looking_at_sky2 * t)

    # Clamp the final interpolated pose to ensure valid angle values and convert to integers
    return clamp_angles(interpolated_pose)


# Function to handle joystick input
def handle_joystick_input(raw_value):
    global previous_joystick_value  # Persist value between calls

    # Normalize joystick value to range [-1, 1]
    normalized_value = normalize_joystick_value(raw_value)

    # Apply deadzone filtering (ignore small movements near the center)
    if abs(raw_value) < DEADZONE:
        normalized_value = 0

    # Gradual interpolation for smooth transitions
    interpolated_value = interpolate_pose_continuous(normalized_value, previous_joystick_value)

    # Interpolate and apply the new pose
    new_pose = interpolate_pose(interpolated_value)
    print(f"Interpolated Pose: {new_pose}")

    # Apply the pose to the robot
    custom_steps(new_pose)

    # Update the previous joystick value to track the next movement
    previous_joystick_value = interpolated_value

def adjust_speed(pressure, adjustment_direction):
    # Map pressure value to a change in speed based on the desired behavior
    DEADZONE = 28384
    speed_change = 0  # Initialize speed_change to ensure it's always defined

    if adjustment_direction == "R2" and abs(pressure) >DEADZONE :
        # Soft press (0-16383) detracts very little, strong press (16384-32767) increases a lot
        if pressure < DEADZONE:  # Soft press
            speed_change = 1  # Small decrement
        elif pressure > DEADZONE:  # Strong press
            speed_change = 5  # Large increment
        else:
            speed_change = 0


    elif adjustment_direction == "L2" and abs(pressure) >DEADZONE:
        # Soft press (0-16383) increases a little, strong press (16384-32767) decreases a lot
        if pressure < DEADZONE:  # Soft press
            speed_change = -1  # Small increment
        elif pressure > DEADZONE:  # Strong press
            speed_change = -2  # Large decrement
        else: 
            speed_change = 0   
    
    # Adjust speed only if speed_change is not zero
    if speed_change != 0:
        speed_adjust(speed_change)
          # Optional: add a small delay to prevent excessive speed adjustments
    sleep(0.1)

def speed_adjust(change):
    global speed
    print(f"initial: {speed}")
    # Update speed and ensure it stays within a defined range (e.g., 0 to 100)
    speed += change
    speed = int(max(0, min(speed, 100)))  # Keep speed between 0 and 100
    print(f"Current speed: {speed}")

def custom_steps(values):
    print(f"New step: {values.tolist()}") 
    #current_step = crawler.get_leg_positions()

    # Debug: Print current step
    #print(f"Current step: {current_step}")
    
    """ new_step = []
    for leg_step in current_step:
        x, y, z = leg_step
        new_step.append([x, y, z + z_offset])
    
    # Debug: Print new step
    print(f"New step: {new_step}") """
    crawler.do_step(values.tolist(),speed)

    sleep(0.1)
    
    # Apply the new step with the z-axis adjust


def handle_input(action,value=0):

    global speed
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
        custom_steps(looking_at_sky)
        #crawler.do_step(stand_step, speed)
    elif action in ('triangle_press', 'y'):
        print("stand")
        #crawler.do_action('turn right', 1, speed
        stand_step = crawler.move_list['stand'][0]
        custom_steps(smelling_ground)
        #crawler.do_step(stand_step, speed)
    elif action in ('circle_press', 'h'):
        print("circle")
        # Adjust Z-axis to simulate standing
        custom_steps(spread_out)  # Example value, adjust as needed
    elif action in ('square_press', 'g'):
        print("compact")
        # Adjust Z-axis to simulate standing
        custom_steps(compact)  # Example value, adjust as needed        

    elif action in ('R1_press', 'u'):
        print("greeting")
        # Adjust Z-axis to simulate standing
        
        custom_steps(wave_1)  
        sleep(0.3)
        custom_steps(wave_2)
        sleep(0.3)
        custom_steps(wave_1)  
        sleep(0.3)
        custom_steps(wave_2)
        sleep(0.3)
        tts.say("hello")
        custom_steps(spread_out)

    elif action in ('L1_press', 't'):
        print("custom 4")
        # Adjust Z-axis to simulate standing
        custom_steps(compact)  # Example value, adjust as needed      
    
    elif action in ('L3_press', '-'):
        # Adjust Z-axis to simulate standing
        speed = 80  # Example value, adjust as needed           
        print(speed)
    
    elif action in ('R3_press', '+'):
        print("compact")
        # Adjust Z-axis to simulate standing
        custom_steps(compact)  # Example value, adjust as needed    
  

    elif action == 'R3_updown':  # For joystick vertical movement
        # Normalize joystick input
        print(f"pose {value}")
        handle_joystick_input(value)  # Pass joystick value to the handler

    elif action == 'R3_leftright':  # For joystick vertical movement
        # Normalize joystick input
        print(f"pose {value}")
        handle_joystick_input(value)  # Pass joystick value to the handler

    elif action == 'L2_press':  # For joystick vertical movement
        # Normalize joystick input
        adjust_speed(value, "L2")

    elif action == 'R2_press':  # For joystick vertical movement
        # Normalize joystick input
        adjust_speed(value, "R2")
        

           

def show_info():
    print("\033[H\033[J", end='')  # clear terminal window
    print(manual)



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
            tts.say("controller connected")
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
