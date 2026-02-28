from picrawler import Picrawler
from robot_hat import Ultrasonic
from robot_hat import Pin
import time

# Initialize hardware
crawler = Picrawler() 
sonar = Ultrasonic(Pin("D2"), Pin("D3"))

# Settings
alert_distance = 20  # Stop and turn when obstacle is this close (cm)
speed = 50

def main():
    print("Starting simple forward movement with obstacle avoidance...")
    print("Testing sensor first...")
    
    # Test sensor for a few readings
    for i in range(5):
        test_distance = sonar.read()
        print(f"Test reading {i+1}: {test_distance} cm")
        time.sleep(0.5)
    
    print("Starting main loop...")
    
    while True:
        try:
            # Check distance
            distance = sonar.read()
            
            if distance == -1:
                # Sensor error - treat as unknown, move cautiously
                print("Sensor error (-1) - moving slowly")
                crawler.do_action('forward', 1, speed//2)  # Move at half speed
            elif distance == -2:
                # No obstacle detected - move forward
                print("Clear path (-2) - moving forward")
                crawler.do_action('forward', 1, speed)
            elif distance <= alert_distance and distance > 0:
                # Obstacle detected - avoid it
                print(f"Obstacle at {distance}cm - avoiding")
                crawler.do_action('backward', 1, speed)  # Back up
                time.sleep(0.3)
                crawler.do_action('turn right', 2, speed)  # Turn right to avoid
                time.sleep(0.3)
            else:
                # Obstacle far away - safe to move forward
                print(f"Obstacle far ({distance}cm) - moving forward")
                crawler.do_action('forward', 1, speed)
            
            time.sleep(0.2)  # Slightly longer delay to give sensor more time
            
        except KeyboardInterrupt:
            print("Stopping robot...")
            crawler.do_action('stop', 1)
            break

if __name__ == "__main__":
    main()
