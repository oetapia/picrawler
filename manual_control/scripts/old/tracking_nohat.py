import os
import sys
import threading
from picrawler import Picrawler
from vilib import Vilib
import time


crawler = Picrawler() 

flag_color = False
qr_code_flag = False
color_tracked = "red"


def qrcode_detect():
    global qr_code_flag, last_qr_code
    Vilib.qrcode_detect_switch(True)  # Start QR code detection
    message = "Waiting for QR code"
    print(message)

    text = None
    while qr_code_flag:  # Keep detecting as long as the flag is True
        temp = Vilib.detect_obj_parameter['qr_data']
        if temp != "None" and temp != text:
            text = temp         
            last_qr_code = text  # Store the latest detected QR code
            print(f'QR code: {last_qr_code}')
        time.sleep(0.5)
    
    Vilib.qrcode_detect_switch(False)  # Stop QR code detection

def qr_code_thread_func():
    global qr_code_flag, qrcode_thread  # Access global flags and thread variable
    qr_code_flag = not qr_code_flag  # Toggle QR code detection flag
    
    if qr_code_flag:
        if qrcode_thread is None or not qrcode_thread.is_alive():
            qrcode_thread = threading.Thread(target=qrcode_detect)
            qrcode_thread.setDaemon(True)  # Make it a daemon thread
            qrcode_thread.start()
    else:
        if qrcode_thread is not None and qrcode_thread.is_alive():
            # Wait for thread to finish
            qr_code_flag = False  # Set the flag to False to exit the thread loop
            qrcode_thread.join()
            print('QR code detection stopped.')
   


def color_track(color="red"):
    if Vilib.detect_obj_parameter['color_n'] != 0:
        coordinate_x = Vilib.detect_obj_parameter['color_x']
        tts.say(f"Spotted {color}!")

        if coordinate_x < 100:
            crawler.do_action('turn left', 1, speed)
        elif coordinate_x > 220:
            crawler.do_action('turn right', 1, speed)
        else:
            tts.say(f"Chasing {color}!")
            crawler.do_action('forward', 2, speed)

""" def color_track(color="red"):
    if Vilib.detect_obj_parameter['color_n'] != 0:
        coordinate_x = Vilib.detect_obj_parameter['color_x']
        color_width = Vilib.detect_obj_parameter['color_w']
        color_height = Vilib.detect_obj_parameter['color_h']
        
        # Calculate the area of the detected color
        color_area = color_width * color_height
        
        # Assuming the screen size is known, for example, 640x480 (can be adjusted)
        screen_width = 640
        screen_height = 480
        screen_area = screen_width * screen_height

        # Check if the detected color occupies 20% or more of the screen
        if color_area >= (0.2 * screen_area):
            print("[Color Detect] Found target color!")
            tts.say(f"Found {color} occupying {color_area} pixels!")

            # Stop movement and wait for 5 seconds
            crawler.do_action('stop', 0, speed)  # Stop the Picrawler
            time.sleep(5)  # Pause for 5 seconds

            # Start QR code detection
            qr_code_thread_func()

            # Allow for QR code detection for a period of time (e.g., 5 seconds)
            time.sleep(5)  # QR code detection period
            qr_code_flag = False  # Stop QR code detection
            
            # If no QR code detected, use the last known QR code
            if last_qr_code:
                print(f"No new QR code detected. Using last QR code: {last_qr_code}")
            else:
                print("No QR code detected.")

            # Resume movement after QR code detection
            crawler.do_action('forward', 1, speed)  # Continue moving forward
        else:
            print("[Color Detect] Detected color is too small.")
    else:
        print('Color Detect: None') """



def main():

    global color_tracked
    Vilib.camera_start(vflip=False,hflip=False) #
    Vilib.display(local=True,web=False)
    #qr_code_thread_func() # start checking for color in QR
    qrcode_detect()
    Vilib.color_detect(color_tracked) 
    

    while True:
        #check_proximity_and_obstacles()  # Continuously check proximity and obstacles
        time.sleep(0.05)  # Adjust sleep time as needed

if __name__ == "__main__":
    main()
