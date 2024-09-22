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

def main():
    for channel in range(1):  # Assuming you have three sensors on channels 0, 1, and 2
        select_channel(channel)  # Select the channel for the accelerometer
        wake_mpu6050()          # Wake up the MPU-6050
        ax, ay, az = read_accel_data()
        print(f"Channel {channel} -> AX: {ax}, AY: {ay}, AZ: {az}")
        logging.info(f"Channel {channel} -> AX: {ax}, AY: {ay}, AZ: {az}")  # Log the data
        time.sleep(1)  # Adjust the sleep time as needed

if __name__ == "__main__":
    main()  # Call the main function if this script is run directly
