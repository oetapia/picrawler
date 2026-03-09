"""
accel_diagnostic.py - live MPU-6050 accelerometer display

Run this to verify the sensor is wired correctly and to observe
real-time tilt angles and orientation classification.

Usage:
    python accel_diagnostic.py
"""

import smbus
import math
import time

MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

bus = smbus.SMBus(1)


def _wake():
    bus.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0x00)


def _read_block(reg):
    data = bus.read_i2c_block_data(MPU6050_ADDR, reg, 6)
    def s16(hi, lo):
        v = (hi << 8) | lo
        return v - 65536 if v > 32767 else v
    return s16(data[0], data[1]), s16(data[2], data[3]), s16(data[4], data[5])


def _read_accel():
    ax, ay, az = _read_block(ACCEL_XOUT_H)
    return ax / 16384.0, ay / 16384.0, az / 16384.0


def _read_gyro():
    gx, gy, gz = _read_block(GYRO_XOUT_H)
    return gx / 131.0, gy / 131.0, gz / 131.0


def _tilt(ax, ay, az):
    pitch = math.degrees(math.atan2(ax, math.sqrt(ay ** 2 + az ** 2)))
    roll  = math.degrees(math.atan2(ay, math.sqrt(ax ** 2 + az ** 2)))
    return pitch, roll


def _orientation(pitch, roll, threshold=15.0):
    if abs(pitch) < threshold and abs(roll) < threshold:
        return "level"
    states = []
    if pitch > threshold:
        states.append("tilted_forward")
    elif pitch < -threshold:
        states.append("tilted_back")
    if roll > threshold:
        states.append("tilted_right")
    elif roll < -threshold:
        states.append("tilted_left")
    return "+".join(states)


def main():
    print("Waking MPU-6050...")
    _wake()
    time.sleep(0.1)
    print("MPU-6050 Accelerometer Diagnostic - Ctrl+C to exit.\n")

    while True:
        try:
            ax, ay, az   = _read_accel()
            gx, gy, gz   = _read_gyro()
            pitch, roll  = _tilt(ax, ay, az)
            orientation  = _orientation(pitch, roll)

            print("\033[H\033[J", end="")  # clear screen
            print("MPU-6050 Accelerometer Diagnostic\n")
            print(f"  Accel  (g)   X: {ax:+.3f}   Y: {ay:+.3f}   Z: {az:+.3f}")
            print(f"  Gyro (deg/s) X: {gx:+.3f}   Y: {gy:+.3f}   Z: {gz:+.3f}")
            print(f"  Pitch: {pitch:+.1f} deg    Roll: {roll:+.1f} deg")
            print(f"  Orientation: {orientation}")
            print("\nPress Ctrl+C to exit.")

        except Exception as e:
            print(f"  I2C error: {e}")

        time.sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDone.")
