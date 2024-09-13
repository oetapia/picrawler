import os
import sys
import subprocess
from robot_hat import Servo
from robot_hat.utils import reset_mcu
from time import sleep
from robot_hat import Music, TTS
import board
import busio
import adafruit_ssd1306
import argparse


# Add the 'components' directory to sys.path
# Adjust this path according to the relative location from 'startup.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../components')))

# Import the 'oled' module from the 'components.display' package
from screens import oled



def main():
    global oled_present  # Declare that we are using the global variable

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Run startup.py or check status.')
    parser.add_argument('--status', action='store_true', help='Check the current mode of operation')
    args = parser.parse_args()

    if args.status:
        # Initialize OLED to determine the mode
        setup_oled()
        # Print the mode of operation
        if oled_present:
            print("The system is running in robot_hat mode with OLED display.")
        else:
            print("The system is running without robot_hat mode (OLED display not present).")
        return  # Exit the script after displaying the mode

    # Continue with the existing startup.py functionality


    # Define the text for resetting legs
    reset_message = "Resetting legs..."
    oled.update_display(header=f"Action", text=f'{reset_message}')

    # Reset MCU
    reset_mcu()
    sleep(0.2)

    # Initialize TTS
    tts = TTS()

    MANUAL = '''
    Legs getting reset
    '''

    print(MANUAL)
    tts.say("Resetting legs")

    for i in range(12):
        # Update the OLED display with the current servo being reset
        oled.update_display(header=f"Action", text=f'Servo {i} resetting')
        print(f"Servo {i} set to zero")
        Servo(i).angle(10)
        sleep(0.1)
        Servo(i).angle(0)
        sleep(0.1)

    # After all servos have been reset, display a message indicating completion
    oled.update_display(header=f"Action", text=f'Legs reset complete')
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

    # Optionally, print a message to the terminal to indicate completion
    print("Legs reset complete. Exiting.")

if __name__ == '__main__':
    main()
