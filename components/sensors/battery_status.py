from robot_hat import get_battery_voltage
import time

def get_battery_state():
    """
    Returns the current state of the battery.
    """
    try:
        voltage = get_battery_voltage()
        if voltage > 7.4:
            return "Good", voltage
        elif voltage > 7.15:
            return "Moderate", voltage
        else:
            return "Low", voltage
    except Exception as e:
        return f"Error: {e}", None

def monitor_battery():
    """
    Continuously monitors and prints the battery voltage and condition.
    """
    while True:
        status, voltage = get_battery_state()
        print(f"Battery Voltage: {voltage:.2f}V")
        print(status)
        time.sleep(1)  # Delay between readings

if __name__ == "__main__":
    monitor_battery()
