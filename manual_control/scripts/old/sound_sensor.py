from robot_hat import Ultrasonic
from robot_hat import Pin
import time

# Initialize sensor
sonar = Ultrasonic(Pin("D2"), Pin("D3"))

def test_sensor():
    print("=== Ultrasonic Sensor Diagnostic ===")
    print("Pin D2 (Trigger) and Pin D3 (Echo)")
    print("Sensor should return:")
    print("  -2 = No obstacle detected (clear path)")
    print("  -1 = Sensor error/timeout")
    print("  Positive number = Distance in cm")
    print("\nTesting sensor readings (Ctrl+C to stop)...")
    print("-" * 50)
    
    reading_count = 0
    error_count = 0
    clear_count = 0
    valid_readings = []
    
    try:
        while True:
            distance = sonar.read()
            reading_count += 1
            
            if distance == -1:
                error_count += 1
                print(f"Reading {reading_count}: ERROR (-1)")
            elif distance == -2:
                clear_count += 1
                print(f"Reading {reading_count}: CLEAR (-2)")
            else:
                valid_readings.append(distance)
                print(f"Reading {reading_count}: {distance} cm")
            
            # Show statistics every 10 readings
            if reading_count % 10 == 0:
                print(f"\n--- Statistics after {reading_count} readings ---")
                print(f"Errors (-1): {error_count} ({error_count/reading_count*100:.1f}%)")
                print(f"Clear (-2): {clear_count} ({clear_count/reading_count*100:.1f}%)")
                print(f"Valid distances: {len(valid_readings)} ({len(valid_readings)/reading_count*100:.1f}%)")
                if valid_readings:
                    print(f"Distance range: {min(valid_readings)} - {max(valid_readings)} cm")
                print("-" * 50)
            
            time.sleep(0.5)  # Half second between readings
            
    except KeyboardInterrupt:
        print(f"\n=== Final Statistics ===")
        print(f"Total readings: {reading_count}")
        print(f"Errors (-1): {error_count} ({error_count/reading_count*100:.1f}%)")
        print(f"Clear (-2): {clear_count} ({clear_count/reading_count*100:.1f}%)")
        print(f"Valid distances: {len(valid_readings)} ({len(valid_readings)/reading_count*100:.1f}%)")
        
        if error_count == reading_count:
            print("\n❌ SENSOR PROBLEM: All readings returned -1")
            print("Check:")
            print("  1. Wiring connections (D2=Trigger, D3=Echo)")
            print("  2. Power supply to sensor")
            print("  3. Sensor hardware")
        elif error_count > reading_count * 0.8:
            print(f"\n⚠️  HIGH ERROR RATE: {error_count/reading_count*100:.1f}% errors")
            print("Sensor may be unreliable")
        else:
            print("\n✅ Sensor appears to be working")

if __name__ == "__main__":
    test_sensor()
