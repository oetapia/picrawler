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
color = "red"  # Default color
alert_distance = 20  # Increased for better safety margin
speed = 60  # Reduced speed for better control
obstacle_detected = False
last_color_detected = False
search_direction = 1  # 1 for right, -1 for left
qr_code_flag = True  # Flag to control QR code detection
valid_colors = ["red", "green", "blue", "yellow", "orange", "purple"]  # Add supported colors

def qrcode_detect():
    """Detect QR code and extract color information"""
    global qr_code_flag, color
    
    if qr_code_flag == True:
        Vilib.qrcode_detect_switch(True)
        print("Waiting for QR code to set color...")
        tts.say("Show QR code to set color")

    text = None
    while qr_code_flag:
        temp = Vilib.detect_obj_parameter['qr_data']
        if temp != "None" and temp != text: 
            text = temp.lower().strip()  # Convert to lowercase and remove whitespace
            print(f'QR code detected: {text}')
            
            # Check if the detected text is a valid color
            if text in valid_colors:
                color = text
                print(f'Color set to: {color}')
                tts.say(f"Color set to {color}")
                qr_code_flag = False  # Stop QR detection
                return color
            else:
                print(f'Invalid color: {text}. Valid colors are: {", ".join(valid_colors)}')
                tts.say("Invalid color, try again")
        
        time.sleep(0.5)
    
    Vilib.qrcode_detect_switch(False)
    return color

def initialize_color_from_qr():
    """Initialize color detection, optionally from QR code"""
    global color, qr_code_flag
    
    print(f"Default color: {color}")
    
    # Try to get color from QR code first
    detected_color = qrcode_detect()
    
    # Start color detection with the determined color
    Vilib.color_detect(detected_color)
    print(f"Now tracking color: {detected_color}")
    return detected_color
    """Handle color tracking logic"""
    global last_color_detected
    
    if Vilib.detect_obj_parameter['color_n'] != 0:
        coordinate_x = Vilib.detect_obj_parameter['color_x']
        last_color_detected = True
        
        # Only announce color detection occasionally to avoid spam
        if coordinate_x < 100:
            print(f"Turning left to track {color}")
            crawler.do_action('turn left', 1, speed)
        elif coordinate_x > 220:
            print(f"Turning right to track {color}")
            crawler.do_action('turn right', 1, speed)
        else:
            print(f"Moving forward to track {color}")
            crawler.do_action('forward', 1, speed)
        return True
    else:
        last_color_detected = False
        return False

def search_for_color():
    """Search for color when not detected"""
    global search_direction
    
    print("Color not detected, searching...")
    
    # Alternate search direction
    if search_direction == 1:
        crawler.do_action('turn right', 1, speed//2)
        search_direction = -1
    else:
        crawler.do_action('turn left', 1, speed//2)
        search_direction = 1

def handle_obstacle_avoidance():
    """Handle obstacle avoidance with improved logic"""
    distance = sonar.read()
    
    if distance == -2:  # No obstacle detected (clear path)
        print("Clear path ahead")
        return False
    
    print(f"Distance: {distance} cm")
    
    if distance <= alert_distance and distance > 0:
        print(f"Obstacle detected at {distance}cm - avoiding")
        tts.say("Obstacle detected!")
        
        # Back up first
        crawler.do_action('backward', 2, speed)
        time.sleep(0.5)
        
        # Turn to avoid obstacle (alternate between left and right)
        if search_direction == 1:
            crawler.do_action('turn right', 3, speed)
        else:
            crawler.do_action('turn left', 3, speed)
        
        time.sleep(0.5)
        return True
    
    return False

def handle_floor_dangers():
    """Handle floor-based dangers from IR sensors"""
    proximity_status = ir_distance.check_proximity()
    
    if "danger_front" in proximity_status:
        print("Floor danger detected in front!")
        tts.say("Danger ahead!")
        crawler.do_action('backward', 2, speed)
        time.sleep(0.5)
        crawler.do_action('turn right', 2, speed)
        return True
    elif "danger_back" in proximity_status:
        print("Floor danger detected behind!")
        tts.say("Danger behind!")
        crawler.do_action('forward', 2, speed)
        time.sleep(0.5)
        return True
    
    return False

def main_control_loop():
    """Main control logic with proper priority handling"""
    
    while True:
        try:
            # Priority 1: Handle floor dangers (highest priority)
            if handle_floor_dangers():
                time.sleep(0.1)
                continue
            
            # Priority 2: Handle obstacle avoidance
            if handle_obstacle_avoidance():
                time.sleep(0.1)
                continue
            
            # Priority 3: Color tracking or searching
            if not color_track():
                # If color not detected, search for it
                search_for_color()
            
            time.sleep(0.1)  # Small delay for system stability
            
        except KeyboardInterrupt:
            print("Stopping robot...")
            crawler.do_action('stop', 1)
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(0.5)

def main():
    """Initialize and start the robot"""
    try:
        print("Starting robot color tracking system...")
        Vilib.camera_start()
        Vilib.display()
        
        # Initialize color from QR code or use default
        final_color = initialize_color_from_qr()
        
        print(f"Tracking color: {final_color}")
        print(f"Alert distance: {alert_distance} cm")
        print(f"Speed: {speed}")
        
        # Give camera time to stabilize after color detection setup
        time.sleep(2)
        
        main_control_loop()
        
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        # Cleanup
        try:
            crawler.do_action('stop', 1)
            Vilib.camera_close()
        except:
            pass

if __name__ == "__main__":
    main()