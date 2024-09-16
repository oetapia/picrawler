import os
import sys
import subprocess
from robot_hat.utils import reset_mcu
from time import sleep
from robot_hat import Music, TTS, Pin
#from picrawler import Picrawler




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
    


#if robot_hat_on: 
    # Initialize components
#crawler = Picrawler()
pin = Pin("LED")                      # create a Pin object from a digital pin
btn = Pin("SW")                      # create a User Button object from a digital pin
val = pin.value()          
tts = TTS()
music = Music()
print("Components initialized.")
#else:
 #   print("Cannot initialize components; Robot HAT is off.")

def run_script(script_path):
    env = os.environ.copy()
    env['VIRTUAL_ENV'] = '/home/pi/picrawler/examples/myenv'  # Adjust as necessary
    result = subprocess.run([sys.executable, script_path], env=env, check=True, text=True, capture_output=True)
    return result

def compact():
    script_path = '/home/pi/picrawler/examples/eyes/imageConvert.py'
    keyboard_control = '/home/pi/picrawler/manual_control/scripts/keyboard_control.py'

    try:
        result = run_script(script_path)
        print("Image conversion script executed successfully.")
        print("Output:", result.stdout)

        result = run_script(keyboard_control)
        print("Keyboard control script executed successfully.")
        print("Output:", result.stdout)

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
        music.sound_play_threading(library.intro_g)
        battery_level, battery_voltage = battery_status.get_battery_state()
        print(f"Battery: {battery_level} {battery_voltage:.1f}")
        oled.update_display(header=f"Battery", text=f'{battery_level} {battery_voltage:.1f}')
        sleep(1)
        #reset_legs()
        music.sound_play_threading(library.hoot_g)
        compact()

    else:
        print("robot hat off")    

if __name__ == '__main__':
    main()
