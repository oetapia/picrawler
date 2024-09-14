import os
import sys
import subprocess
from robot_hat import Servo
from robot_hat.utils import reset_mcu
from time import sleep
from robot_hat import Music, TTS, Pin
from picrawler import Picrawler


# Add the 'components' directory to sys.path
# Adjust this path according to the relative location from 'startup.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../components')))

# Import the 'oled' module from the 'components.display' package
from screens import oled
from sensors import battery_status


# Initialize components
crawler = Picrawler()
pin = Pin("LED")                      # create a Pin object from a digital pin
btn = Pin("SW")                      # create a User Button object from a digital pin
val = pin.value()          
tts = TTS()
music = Music()
print("testing pins",val)


# Sound effect file
intro = '/home/pi/picrawler/components/sounds/intro.wav'
audio_effect = '/home/pi/picrawler/components/sounds/hoot.wav'


def compact():
    crawler.do_step([[60, 0, -30]]*4, 100)
    # Launch another Python script after the reset
    script_path = '/home/pi/picrawler/examples/eyes/imageConvert.py'
        
    try:
        # Use the Python interpreter from the virtual environment
        result = subprocess.run([sys.executable, script_path], check=True, text=True, capture_output=True)
        print("Other script executed successfully.")
        print("Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the other script: {e}")
        print("Error Output:", e.output)
        print("Return Code:", e.returncode)
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



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
    compact()
    # Optionally, print a message to the terminal to indicate completion
    print("Legs reset complete. Exiting.")




def main():
    music.sound_play_threading(intro)
    battery_level, battery_voltage = battery_status.get_battery_state()
    print(f"Battery: {battery_level} {battery_voltage:.1f}")
    oled.update_display(header=f"Battery", text=f'{battery_level} {battery_voltage:.1f}')
    sleep(1)
    reset_legs()
    music.sound_play_threading(audio_effect)
    music.sound_play_threading(audio_effect)

if __name__ == '__main__':
    main()
