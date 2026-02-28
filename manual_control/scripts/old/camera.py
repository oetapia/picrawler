from vilib import Vilib
from time import sleep, strftime, localtime
import threading
import signal
import readchar
from os import environ

USERNAME = environ.get('USER', 'unknown')
PICTURE_PATH = f"/home/{USERNAME}/Pictures/"

flag_face = False
flag_color = False
qr_code_flag = False
running = True

color_list = ['close', 'red', 'orange', 'yellow', 'green', 'blue', 'purple']

MANUAL = '''
Input key to call the function!
    q: Quit program
    p: Take photo
    1: Color detect : red
    2: Color detect : orange
    3: Color detect : yellow
    4: Color detect : green
    5: Color detect : blue
    6: Color detect : purple
    0: Switch off Color detect
    r: Scan the QR code
    f: Switch ON/OFF face detect
    s: Display detected object information
'''

def handle_exit(signum, frame):
    """Handle graceful exit on CTRL+C."""
    global running
    print("\nExiting program...")
    running = False

def face_detect(flag):
    """Toggle face detection on or off."""
    print(f"Face Detect: {'ON' if flag else 'OFF'}")
    Vilib.face_detect_switch(flag)

def take_photo():
    """Take a photo and save it to the specified directory."""
    _time = strftime('%Y-%m-%d-%H-%M-%S', localtime())
    name = f'photo_{_time}'
    Vilib.take_photo(name, PICTURE_PATH)
    print(f'Photo saved as {PICTURE_PATH}{name}.jpg')

def object_show():
    """Display detected object information."""
    if flag_color:
        if Vilib.detect_obj_parameter['color_n'] == 0:
            print('Color Detect: None')
        else:
            color_coordinate = (Vilib.detect_obj_parameter['color_x'], Vilib.detect_obj_parameter['color_y'])
            color_size = (Vilib.detect_obj_parameter['color_w'], Vilib.detect_obj_parameter['color_h'])
            print(f"[Color Detect] Coordinate: {color_coordinate}, Size: {color_size}")
    if flag_face:
        if Vilib.detect_obj_parameter['human_n'] == 0:
            print('Face Detect: None')
        else:
            human_coordinate = (Vilib.detect_obj_parameter['human_x'], Vilib.detect_obj_parameter['human_y'])
            human_size = (Vilib.detect_obj_parameter['human_w'], Vilib.detect_obj_parameter['human_h'])
            print(f"[Face Detect] Coordinate: {human_coordinate}, Size: {human_size}")

def handle_input(key):
    """Handle user input and trigger the corresponding action."""
    global flag_face, flag_color, qr_code_flag, running
    if key == 'q':
        print("Quit")
        running = False
    elif key == 'p':
        take_photo()
    elif key in '0123456':
        index = int(key)
        if index == 0:
            flag_color = False
            Vilib.color_detect('close')
        else:
            flag_color = True
            Vilib.color_detect(color_list[index])
        print(f'Color detect: {color_list[index]}')
    elif key == 'f':
        flag_face = not flag_face
        face_detect(flag_face)
    elif key == 'r':
        if not qr_code_flag:
            qr_code_flag = True
            print("QR Code Detection: ON")
            Vilib.qrcode_detect_switch(True)
        else:
            qr_code_flag = False
            print("QR Code Detection: OFF")
            Vilib.qrcode_detect_switch(False)
    elif key == 's':
        object_show()

def qr_code_loop():
    """Poll for QR codes when QR code detection is enabled."""
    global qr_code_flag
    while running:
        if qr_code_flag:
            text = Vilib.detect_obj_parameter['qr_data']
            if text != "None":
                print(f"QR Code: {text}")
        sleep(0.5)

def main():
    """Main function to run the program."""
    global running
    Vilib.camera_start(vflip=False, hflip=False)
    Vilib.display(local=True, web=True)
    print(MANUAL)
    signal.signal(signal.SIGINT, handle_exit)  # Capture CTRL+C

    qr_thread = threading.Thread(target=qr_code_loop)
    qr_thread.setDaemon(True)
    qr_thread.start()

    try:
        while running:
            key = readchar.readkey()
            handle_input(key)
            sleep(0.02)
    finally:
        Vilib.qrcode_detect_switch(False)  # Ensure QR code detection is off
        Vilib.display(local=False, web=False)  # Turn off camera display
        print("Cleaned up resources.")

if __name__ == "__main__":
    main()
