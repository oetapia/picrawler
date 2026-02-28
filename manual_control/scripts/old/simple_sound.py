from robot_hat import Ultrasonic
from robot_hat import Pin
import time

# Initialize sensor
sonar = Ultrasonic(Pin("D2"), Pin("D3"))

print("Simple sensor logger - Press Ctrl+C to stop")
print("D2=Trigger, D3=Echo")

while True:
    try:
        distance = sonar.read()
        print(f"{distance}")
        time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopped")
        break
