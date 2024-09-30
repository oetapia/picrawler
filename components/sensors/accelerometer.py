import os
import smbus
import time
import logging

# Initialize I2C
bus = smbus.SMBus(1)  # Use 1 for Raspberry Pi

# Multiplexer I2C address
multiplexer_address = 0x70
MPU6050_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B


# Create 'data' directory if it doesn't exist
data_dir = os.path.join(os.path.dirname(__file__), '../data')
os.makedirs(data_dir, exist_ok=True)

# Set up logging
logging.basicConfig(filename=os.path.join(data_dir, 'accelerometer_log.txt'), level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

# Function to select a channel on the multiplexer
def select_channel(channel):
    if 0 <= channel <= 7:
        bus.write_byte(multiplexer_address, 1 << channel)
    else:
        print("Channel out of range!")

# Wake up the MPU-6050
def wake_mpu6050():
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)

def read_word(register):
    high = bus.read_byte_data(MPU6050_ADDR, register)
    low = bus.read_byte_data(MPU6050_ADDR, register + 1)
    return (high << 8) + low

def read_accel_data():
    ax = read_word(ACCEL_XOUT_H)
    ay = read_word(ACCEL_XOUT_H + 2)
    az = read_word(ACCEL_XOUT_H + 4)
    return ax, ay, az

def convert_to_g(raw_value):
    """Convert raw accelerometer data to 'g' forces."""
    # Handle two's complement for negative numbers
    raw_value = twos_complement(raw_value)
    return raw_value / 16384.0  # Convert to 'g' assuming ±2g setting

def normalize_accel(ax, ay, az):
    """Normalize and adjust for gravity on Z-axis."""
    ax_g = convert_to_g(ax)
    ay_g = convert_to_g(ay)
    az_g = convert_to_g(az) - 1.0  # Adjust for gravity
    return ax_g, ay_g, az_g

def classify_orientation(ax_g, ay_g, az_g, position):
    """Classify orientation based on threshold values for each accelerometer."""
    thresholds = {
        "Front Left": {"ax": 0.3, "ay": 0.3, "az": 0.5},  # Adjusted thresholds
        "Back Right": {"ax": 0.3, "ay": 0.4, "az": 0.3},  # Adjust as necessary
        "Inside": {"ax": 0.2, "ay": 0.2, "az": 0.2}
    }


    baseline = {
        "Front Left": (16484, 1720, 63764),
        "Back Right": (17144, 64176, 628),
        "Inside": (64876, 616, 16612)
    }

    # Calculate deviations from baseline
    ax_dev = ax_g - (baseline[position][0] / 16384.0)
    ay_dev = ay_g - (baseline[position][1] / 16384.0)
    az_dev = az_g - (baseline[position][2] / 16384.0)

    print(f"Deviations -> AX: {ax_dev}, AY: {ay_dev}, AZ: {az_dev}")

    if abs(ax_dev) < thresholds[position]["ax"] and abs(ay_dev) < thresholds[position]["ay"] and abs(az_dev) < thresholds[position]["az"]:
        return f"{position} - At Rest"

    orientation = []

    # Leaning detection
    if ax_dev < -thresholds[position]["ax"]:  # Leaning Forward
        orientation.append("Leaning Forward")
    elif ax_dev > thresholds[position]["ax"]:  # Leaning Backward
        orientation.append("Leaning Backward")

    if ay_dev > thresholds[position]["ay"]:  # Leaning Right
        orientation.append("Leaning Right")
    elif ay_dev < -thresholds[position]["ay"]:  # Leaning Left
        orientation.append("Leaning Left")

    # If orientation detected, return that; otherwise return "Unknown"
    return f"{position} - " + " and ".join(orientation) if orientation else f"{position} - Unknown"



def twos_complement(val, bits=16):
    """Convert raw value to two's complement for the given bit length."""
    if val >= 2**(bits - 1):
        val -= 2**bits
    return val


def main():
    for channel in range(3):  # Assuming you have three sensors on channels 0, 1, and 2
        select_channel(channel)  # Select the channel for the accelerometer
        wake_mpu6050()          # Wake up the MPU-6050
        ax, ay, az = read_accel_data()
        print(f"Channel {channel} -> AX: {ax}, AY: {ay}, AZ: {az}")
        ax_g, ay_g, az_g = normalize_accel(ax, ay, az)
        # Classify orientation based on channel
        if channel == 0:
            orientation = classify_orientation(ax_g, ay_g, az_g, "Inside")  # Front Left Accelerometer
        elif channel == 1:
            orientation = classify_orientation(ax_g, ay_g, az_g, "Back Right")  # Back Right Accelerometer
        else:
            orientation = classify_orientation(ax_g, ay_g, az_g, "Front Left")  # Front Right Accelerometer
    
        
        #orientation = classify_orientation(ax_g, ay_g, az_g)
        print(f"Orientation: {orientation}")
        #logging.info(f"Channel {channel} -> AX: {ax}, AY: {ay}, AZ: {az}")  # Log the data
        time.sleep(1)  # Adjust the sleep time as needed

if __name__ == "__main__":
    while True:
        main()  # Call the main function if this script is run directly
