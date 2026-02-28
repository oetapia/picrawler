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



def main():

    global color_tracked
    Vilib.camera_start(vflip=False,hflip=False) #
    Vilib.display(local=True,web=True)
    Vilib.color_detect(color_tracked) 
    

    while True:
        #check_proximity_and_obstacles()  # Continuously check proximity and obstacles
        time.sleep(0.05)  # Adjust sleep time as needed

if __name__ == "__main__":
    main()
