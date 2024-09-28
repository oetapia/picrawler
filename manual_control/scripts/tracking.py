import os
import sys
import threading
from picrawler import Picrawler
from vilib import Vilib
from robot_hat import TTS, Music
from robot_hat import Ultrasonic
from robot_hat import Pin
import time

# Add the 'components' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))
from sensors import ir_distance

crawler = Picrawler() 

music = Music()
tts = TTS()
sonar = Ultrasonic(Pin("D2"), Pin("D3"))
color = "red"
alert_distance = 15
speed = 80
obstacle_detected = False

def color_track():
    if Vilib.detect_obj_parameter['color_n'] != 0:
        coordinate_x = Vilib.detect_obj_parameter['color_x']
        tts.say(f"Found {color}!")

        if coordinate_x < 100:
            crawler.do_action('turn left', 1, speed)
        elif coordinate_x > 220:
            crawler.do_action('turn right', 1, speed)
        else:
            crawler.do_action('forward', 2, speed)
    else:
        # If color is not detected, keep moving
        print("Color not detected, continuing to move.")
        crawler.do_action('forward', 1, speed)  # Continue moving forward

def check_proximity_and_obstacles():
    global obstacle_detected
    proximity_status = ir_distance.check_proximity()  # Get the status from the IR sensors
    distance = sonar.read()
    print(f"Distance: {distance}")

    # Update obstacle detection
    obstacle_detected = (distance != -2) and (distance <= alert_distance)

    # Check for floor detection and respond to dangers
    if "danger_front" in proximity_status:  # Danger detected in front
        tts.say("Danger detected in front, moving backward!")
        crawler.do_action('backward', 1, speed)  # Move backward to avoid danger
    elif "danger_back" in proximity_status:  # Danger detected in back
        tts.say("Danger detected behind, moving forward!")
        crawler.do_action('forward', 1, speed)  # Move forward to avoid danger
    else:
        # If no danger detected, handle movement based on obstacle detection
        if obstacle_detected:
            # Check if the obstacle is too close (threshold can be adjusted)
            if distance <= 50:  # Distance threshold for backing away
                tts.say("Obstacle too close, backing up!")
                crawler.do_action('backward', 2, speed)  # Back away from the obstacle
                time.sleep(1)  # Give it a moment to move back
            if distance <= 100:  # Distance threshold for backing away
                tts.say("Obstacle too close, backing up!")
                crawler.do_action('backward', 1, speed)  # Back away from the obstacle
                time.sleep(1)  # Give it a moment to move back    
            tts.say("Obstacle detected, preparing to turn!")
            crawler.do_action('turn left', 3, speed)  # Avoid obstacle
        else:
            color_track()  # Track color if no obstacles

def main():
    Vilib.camera_start()
    Vilib.display()
    Vilib.color_detect(color) 

    while True:
        check_proximity_and_obstacles()  # Continuously check proximity and obstacles
        time.sleep(0.05)  # Adjust sleep time as needed

if __name__ == "__main__":
    main()
