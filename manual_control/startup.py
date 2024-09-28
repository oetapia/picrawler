import os
import sys
import subprocess
from robot_hat.utils import reset_mcu
import time 
from robot_hat import Music, TTS, Pin
#from picrawler import Picrawler
# Add the 'components' directory to sys.path



# Add the 'components' directory to sys.path
# Adjust this path according to the relative location from 'startup.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../components')))

# Import from the 'components.display' package
from screens import oled
from sensors import battery_status
from sounds import library


robot_hat_on = False



def check_robot_hat_status():
    global robot_hat_on

    """
    Checks if the robot HAT is on by monitoring the battery voltage.
    """
    status, voltage = battery_status.get_battery_state()
    if status.startswith("Error") or voltage is None:
        print("Robot HAT is off or disconnected.")
        return False
    else:
        print("Robot HAT is on.")
        robot_hat_on = True
        return True
    



btn = Pin("SW", Pin.IN, Pin.PULL_UP)  # Initialize the button with pull-up resistor
btn2 = Pin("RST", Pin.IN, Pin.PULL_UP)  # Initialize the button with pull-up resistor
tts = TTS()
music = Music()
print("Components initialized.")
service_started = False
last_press_time = 0
debounce_time = 200  # 200 milliseconds debounce time

def button_handler(pin):
    global last_press_time, service_started
    current_time = time.time() * 1000  # Get current time in milliseconds

    # Debounce logic: Ignore button presses within the debounce time
    if (current_time - last_press_time) > debounce_time:
        if pin.value() == 0 and not service_started:  # Button pressed and service not started
            print("first press")
            tts.say("Starting service")
            compact()
            service_started = True
        elif pin.value() == 1:  # Button released
            print("after")
        
        last_press_time = current_time



def run_script(script_path):
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = '/home/pi/picrawler/examples/myenv'  # Adjust as necessary
    result = subprocess.run([sys.executable, script_path], env=env, check=True, text=True, capture_output=True)
    return result

def compact():
    btn.close()
    script_path = '/home/pi/picrawler/examples/eyes/imageConvert.py'
    keyboard_control = '/home/pi/picrawler/manual_control/scripts/keyboard_control.py'

    try:
        result = run_script(script_path)
        tts.say("running eyes")
        print("Image conversion script executed successfully.")
        print("Output:", result.stdout)

        tts.say("running manual control")
        result = run_script(keyboard_control)
        print("Keyboard control script executed successfully.")
        print("Output:", result.stdout)

        btn.close()

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the script: {e}")
        print("Error Output:", e.stderr)
        print("Return Code:", e.returncode)

    except FileNotFoundError as e:
        print(f"File not found error: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")





def main():
    global robot_hat_on

    check_robot_hat_status()
    
    if robot_hat_on:
        print("starting up")
        music.sound_play_threading(library.intro)
        battery_level, battery_voltage = battery_status.get_battery_state()
        time.sleep(2)
        tts.say(f"battery level {battery_level} running at {battery_voltage:.1f}")
        print(f"Battery: {battery_level} {battery_voltage:.1f}")
        time.sleep(1)
        oled.update_display(header=f"Battery", text=f'{battery_level} {battery_voltage:.1f}')
        tts.say("connect remote")
        
        # Attach interrupt to button
        btn.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda pin: button_handler(btn))
        oled.update_display(header=f"Connect", text=f'Bluetooth Remote')
        

        


        while True: 
            time.sleep(0.2)


    else:
        print("robot hat off")

if __name__ == '__main__':
    main()
