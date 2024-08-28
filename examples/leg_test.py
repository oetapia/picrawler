from robot_hat import Servo
import time
from datetime import datetime

def sweep_servo(pin, start_angle, end_angle, step, log_file):
    """
    Sweeps the servo from start_angle to end_angle in increments of step
    and logs the position and movement time.

    :param pin: Pin number for the servo
    :param start_angle: Starting angle (in degrees)
    :param end_angle: Ending angle (in degrees)
    :param step: Step increment (in degrees)
    :param log_file: File object to write log entries
    """
    servo = Servo(pin)
    
    current_angle = start_angle
    while current_angle <= end_angle:
        # Log start time
        start_time = time.time()
        
        # Move the servo to the current angle
        servo.angle(current_angle)
        
        # Wait for the servo to reach the position
        time.sleep(1)  # Adjust if needed based on the servo's speed
        
        # Log end time and calculate duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Write log entry
        log_file.write(f"Pin {pin}: Moved to {current_angle} degrees\n")
        log_file.write(f"Pin {pin}: Movement time = {duration:.2f} seconds\n")
        
        # Move to the next angle
        current_angle += step

def main():
    # Prompt user for the pin number
    pin = int(input("Enter the pin number for the servo: ").strip())
    
    # Get current date and time for unique log file name
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    
    # Define the start, end, and step for the sweep
    start_angle = -90
    end_angle = 90
    step = 10  # Increment step size, adjust as needed
    
    # Create a unique log file name with date and pin number
    log_filename = f'servo_sweep_log_pin{pin}_{date_str}.txt'
    
    # Open a log file in write mode
    with open(log_filename, 'w') as log_file:
        # Log the start of the test
        log_file.write(f"Starting sweep test for servo on pin {pin}\n")
        log_file.write(f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        sweep_servo(pin, start_angle, end_angle, step, log_file)
        # Log the end of the test
        log_file.write(f"Sweep test completed for servo on pin {pin}\n")
        log_file.write(f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()
