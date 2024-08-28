from robot_hat import get_battery_voltage  # Import the function to get battery voltage
import time

def monitor_battery():
    while True:
        try:
            # Retrieve the battery voltage
            voltage = get_battery_voltage()
            print(f"Battery Voltage: {voltage:.2f}V")
            
            # Provide feedback based on voltage levels
            if voltage > 7.6:
                print("Battery is in good condition.")
            elif voltage > 7.15:
                print("Battery level is moderate.")
            else:
                print("Battery level is low.")
            
            time.sleep(1)  # Delay between readings

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    monitor_battery()
