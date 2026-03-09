import smbus
import math
import time

MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

_bus = None

def _get_bus():
    global _bus
    if _bus is None:
        _bus = smbus.SMBus(1)
    return _bus

def wake():
    """Wake the MPU-6050 from sleep mode."""
    _get_bus().write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0x00)

def _read_raw_block(reg):
    data = _get_bus().read_i2c_block_data(MPU6050_ADDR, reg, 6)
    def s16(hi, lo):
        v = (hi << 8) | lo
        return v - 65536 if v > 32767 else v
    return s16(data[0], data[1]), s16(data[2], data[3]), s16(data[4], data[5])

def read_accel():
    """Returns (ax, ay, az) in g.  ±2 g full-scale (default)."""
    ax, ay, az = _read_raw_block(ACCEL_XOUT_H)
    return ax / 16384.0, ay / 16384.0, az / 16384.0

def read_gyro():
    """Returns (gx, gy, gz) in deg/s.  ±250 °/s full-scale (default)."""
    gx, gy, gz = _read_raw_block(GYRO_XOUT_H)
    return gx / 131.0, gy / 131.0, gz / 131.0

def get_tilt():
    """Returns (pitch, roll) in degrees derived from accelerometer."""
    ax, ay, az = read_accel()
    pitch = math.degrees(math.atan2(ax, math.sqrt(ay ** 2 + az ** 2)))
    roll  = math.degrees(math.atan2(ay, math.sqrt(ax ** 2 + az ** 2)))
    return pitch, roll

def get_orientation(tilt_threshold=15.0):
    """
    Classify robot posture from tilt angles.

    Returns one of: "level", "tilted_forward", "tilted_back",
    "tilted_right", "tilted_left", or a combined string like
    "tilted_forward+tilted_right".

    tilt_threshold: degrees from level that counts as tilted (default 15).
    """
    pitch, roll = get_tilt()

    if abs(pitch) < tilt_threshold and abs(roll) < tilt_threshold:
        return "level"

    states = []
    if pitch > tilt_threshold:
        states.append("tilted_forward")
    elif pitch < -tilt_threshold:
        states.append("tilted_back")
    if roll > tilt_threshold:
        states.append("tilted_right")
    elif roll < -tilt_threshold:
        states.append("tilted_left")

    return "+".join(states)

def is_stable(threshold=10.0):
    """Returns True when the robot is roughly level (within *threshold* degrees)."""
    pitch, roll = get_tilt()
    return abs(pitch) < threshold and abs(roll) < threshold


def main():
    wake()
    time.sleep(0.1)
    while True:
        ax, ay, az = read_accel()
        pitch, roll = get_tilt()
        orientation  = get_orientation()
        print(f"Accel(g): X={ax:+.3f} Y={ay:+.3f} Z={az:+.3f} | "
              f"Pitch={pitch:+.1f}° Roll={roll:+.1f}° | {orientation}")
        time.sleep(1)

if __name__ == "__main__":
    main()
