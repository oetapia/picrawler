import os
import sys
import subprocess
from robot_hat.utils import reset_mcu
from time import sleep
from robot_hat import Servo, Music, TTS, Pin
from picrawler import Picrawler




# Add the 'components' directory to sys.path
# Adjust this path according to the relative location from 'startup.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))

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
    


#
crawler = Picrawler()
pin = Pin("LED")                      # create a Pin object from a digital pin
val = pin.value(0)    
tts = TTS()
music = Music()
print("Components initialized.")
#else:
 #   print("Cannot initialize components; Robot HAT is off.")


def reset_legs():
    # Reset MCU
    reset_mcu()
    # Define the text for resetting legs
    reset_message = "Resetting legs..."
    oled.update_display(header=f"Action", text=f'{reset_message}')
    reset_message = "Resetting legs"
    print(reset_message)
    tts.say("Resetting legs")
    pin.value(0.5)                         # set the digital pin on

    for i in range(12):
        # Update the OLED display with the current servo being reset
        oled.update_display(header=f"Resetting", text=f'Servo {i}')
        print(f"Servo {i} set to zero")
        Servo(i).angle(10)
        sleep(0.1)
        Servo(i).angle(0)
        sleep(0.1)

    # After all servos have been reset, display a message indicating completion
    oled.update_display(header=f"Completed", text=f'Legs reset')
    pin.value(0)                         # set the digital pin to low level
    # Optionally, print a message to the terminal to indicate completion
    print("Legs reset complete. Exiting.")
    pin.close() 



def main():
    global robot_hat_on

    check_robot_hat_status()
    
    if robot_hat_on:
        reset_legs()

    else:
        print("robot hat off")    

if __name__ == '__main__':
    main()
