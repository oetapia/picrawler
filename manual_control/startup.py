import os
import sys
import subprocess
from robot_hat.utils import reset_mcu
import time 
from robot_hat import Music, TTS, Pin
#from picrawler import Picrawler
# Add the 'components' directory to sys.path



# Import from the 'components' package
# Note: Requires 'pip install -e .' from project root
from components.screens import oled
from components.sensors import battery_status
from components.sounds import library


robot_hat_on = False

btn1 = Pin("SW", Pin.IN, Pin.PULL_UP)  # Initialize the first button with pull-up resistor
btn2 = Pin("RST", Pin.IN, Pin.PULL_UP)  # Initialize the second button with pull-up resistor
tts = TTS()
music = Music()
print("Components initialized.")
service_started = False
last_press_time = 0
debounce_time = 200  # 200 milliseconds debounce time




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
    

def button_handler(pin):
    global last_press_time, service_started
    current_time = time.time() * 1000  # Get current time in milliseconds

  # Debounce logic: Ignore button presses within the debounce time
    if (current_time - last_press_time) > debounce_time:
        if pin.value() == 0 and not service_started:  # Button pressed and service not started
            tts.say("Starting service")
            

            if pin == btn1:
                print("Button 1 pressed")
                tts.say("Starting manual control")
                oled.update_display(header=f"Starting...", text=f'Keyboard control')
                run_script('/home/pi/picrawler/manual_control/scripts/restapi3.py')  # Run script 1
    
            elif pin == btn2:
                print("Button 2 pressed")
                tts.say("Starting automated control")
                oled.update_display(header=f"Starting...", text=f'Autopilot tracking')
                run_script('/home/pi/picrawler/self_aware/autonomous_navigator.py')  # Run script 2

            service_started = True

        elif pin.value() == 1:  # Button released
            print("Button released")

        last_press_time = current_time


def run_script(script_path):
    """
    Run a Python script as a subprocess using the project's virtual environment.
    
    Uses the same Python interpreter that's running this script (sys.executable),
    which will be the venv Python when started via systemd or setup scripts.
    """
    env = os.environ.copy()
    project_root = '/home/pi/picrawler'
    venv_path = os.path.join(project_root, 'venv')
    
    # Set virtual environment paths
    env['VIRTUAL_ENV'] = venv_path
    env['PATH'] = os.path.join(venv_path, 'bin') + ':' + env.get('PATH', '')
    
    # Use the same Python that's running this script
    python_executable = sys.executable
    
    print(f"Running: {script_path}")
    print(f"Python: {python_executable}")
    
    result = subprocess.run(
        [python_executable, script_path], 
        env=env, 
        cwd=project_root,
        check=True, 
        text=True, 
        capture_output=True
    )
    print(f"Executed {script_path} with output: {result.stdout}")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    return result

  



def main():
    global robot_hat_on

    check_robot_hat_status()
    
    if robot_hat_on:
        print("Starting up")
        music.sound_play_threading(library.intro)
        battery_level, battery_voltage = battery_status.get_battery_state()
        time.sleep(2)
        tts.say(f"Battery level {battery_level} running at {battery_voltage:.1f}")
        oled.update_display(header="Battery", text=f'{battery_level} {battery_voltage:.1f}')
        tts.say("Choose function")
           # Attach interrupt to button
        oled.update_display(header=f"Function", text=f'USR: Keyboard control, RST: Autopilot')

        # Attach interrupts to buttons
        btn1.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda pin: button_handler(btn1))
        btn2.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=lambda pin: button_handler(btn2))
        
        
        while True:
            time.sleep(0.2)

    else:
        print("Robot hat off")

if __name__ == '__main__':
    main()
