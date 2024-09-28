from robot_hat import Pin, TTS
import time

# Initialize the proximity sensors on digital pins D0 and D1
proximity_back = Pin("D0", Pin.IN)
proximity_front = Pin("D1", Pin.IN)

tts = TTS()

def check_proximity():
    front = proximity_front.value()
    back = proximity_back.value()
    
    if front == 0 and back == 0:  # Both sensors detect the floor
        return "floor_both"  # Indicating floor is detected on both sides
    elif front == 0:
        tts.say("danger front")
        return "danger_front"  # Floor detected on back but danger in front
    elif back == 0:
        tts.say("danger back")
        return "danger_back"  # Floor detected on front but danger in back
    else:
        return "airborne"  # No floor detected

def main():
    while True:
        proximity_status = check_proximity()
        print(proximity_status)  # Print the status
        time.sleep(1)  # Adjust the sleep time as needed

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped.")
