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

def setup_oled():
    """Initialize the OLED display and return whether it was successful."""
    global oled_present, display
    i2c = busio.I2C(board.SCL, board.SDA)
    try:
        display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        oled_present = True
        return True
    except Exception as e:
        print("OLED display not detected or initialization failed.")
        oled_present = False
        return False

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

    # Initialize OLED
    setup_oled()

    # Define the text for resetting legs
    reset_message = "Resetting legs..."

    if oled_present:
        # If OLED is present, clear the display
        display.fill(0)  # 0 is black
        display.show()
        display.text(reset_message, 0, 0, 1)  # Display "Resetting legs..." at the top
        display.show()

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
        if oled_present:
            # Update the OLED display with the current servo being reset
            display.fill(0)  # Clear the display
            display.text(reset_message, 0, 0, 1)  # Keep the "Resetting legs..." message
            display.text(f"Servo {i} resetting", 0, 20, 1)  # Display which servo is resetting
            display.show()

        print(f"Servo {i} set to zero")
        Servo(i).angle(10)
        sleep(0.1)
        Servo(i).angle(0)
        sleep(0.1)

    # After all servos have been reset, display a message indicating completion
    if oled_present:
        display.fill(0)  # Clear the display
        display.text("Legs reset complete.", 0, 0, 1)
        display.show()

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
