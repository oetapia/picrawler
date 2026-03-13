"""
tof_diagnostic.py - VL53L0X / VL53L1X Time-of-Flight diagnostic

Steps:
  1. Scan I2C bus 1 for any devices.
  2. Check the model-ID register at the standard VL53 address (0x29)
     to distinguish VL53L0X from VL53L1X.
  3. Initialize the detected sensor and stream live distance readings.

Usage:
    python tof_diagnostic.py
"""

import smbus
import time

I2C_BUS      = 1
VL53_ADDR    = 0x29   # default address for both sensors

# Model-ID registers
VL53L0X_MODEL_ID_REG  = 0xC0   # expected value: 0xEE
VL53L1X_MODEL_ID_REG  = 0x010F # expected value: 0xEA (16-bit register address)

VL53L0X_EXPECTED_ID   = 0xEE
VL53L1X_EXPECTED_ID   = 0xEA


# --- I2C scan ----------------------------------------------------------------

def scan_i2c(bus):
    """Return list of I2C addresses that ACK on the bus."""
    found = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            found.append(addr)
        except OSError:
            pass
    return found


# --- Model detection ---------------------------------------------------------

def read_byte_at(bus, addr, reg):
    """Read a single byte from a device register."""
    return bus.read_byte_data(addr, reg)


def read_word_register(bus, addr, reg16):
    """
    Read a single byte using a 16-bit register address.
    Sends the two-byte address then reads one byte (matches ST datasheet protocol).
    """
    hi = (reg16 >> 8) & 0xFF
    lo = reg16 & 0xFF
    bus.write_i2c_block_data(addr, hi, [lo])
    return bus.read_byte(addr)


def detect_model(bus, addr):
    """
    Return 'VL53L0X', 'VL53L1X', or None.
    Tries VL53L1X first (its register address is unambiguous).
    """
    try:
        val = read_word_register(bus, addr, VL53L1X_MODEL_ID_REG)
        if val == VL53L1X_EXPECTED_ID:
            return "VL53L1X", val
    except Exception:
        pass

    try:
        val = read_byte_at(bus, addr, VL53L0X_MODEL_ID_REG)
        if val == VL53L0X_EXPECTED_ID:
            return "VL53L0X", val
    except Exception:
        pass

    return None, None


# --- Live read loops ---------------------------------------------------------

def run_vl53l0x(addr):
    import VL53L0X
    sensor = VL53L0X.VL53L0X(i2c_bus=I2C_BUS, i2c_address=addr)
    sensor.open()
    sensor.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
    print("  Streaming readings - Ctrl+C to stop.\n")
    try:
        while True:
            dist_mm = sensor.get_distance()
            dist_cm = dist_mm / 10.0
            bar = "#" * max(0, min(40, int(dist_cm / 3)))
            print(f"\033[2K\r  {dist_cm:6.1f} cm  |  {bar:<40}", end="", flush=True)
            time.sleep(0.1)
    finally:
        sensor.stop_ranging()
        sensor.close()


def run_vl53l1x(addr):
    import VL53L1X
    sensor = VL53L1X.VL53L1X(i2c_bus=I2C_BUS, i2c_address=addr)
    sensor.open()
    sensor.start_ranging(1)   # 1 = short range mode (~1.3 m)
    print("  Ranging mode: short (up to ~130 cm)")
    print("  Streaming readings - Ctrl+C to stop.\n")
    try:
        while True:
            dist_mm = sensor.get_distance()
            dist_cm = dist_mm / 10.0
            bar = "#" * max(0, min(40, int(dist_cm / 3)))
            print(f"\033[2K\r  {dist_cm:6.1f} cm  |  {bar:<40}", end="", flush=True)
            time.sleep(0.05)
    finally:
        sensor.stop_ranging()
        sensor.close()


# --- Main --------------------------------------------------------------------

def main():
    print("=" * 55)
    print("  VL53L0X / VL53L1X Time-of-Flight Diagnostic")
    print("=" * 55)

    # Step 1 - scan bus
    print(f"\n[1] Scanning I2C bus {I2C_BUS}...")
    bus = smbus.SMBus(I2C_BUS)
    devices = scan_i2c(bus)

    if not devices:
        print("  No I2C devices found. Check wiring (SDA/SCL, power, pull-ups).")
        return

    print(f"  Found {len(devices)} device(s): " +
          ", ".join(f"0x{a:02X}" for a in devices))

    # Step 2 - detect model
    if VL53_ADDR not in devices:
        print(f"\n  No device at 0x{VL53_ADDR:02X} - VL53 sensors default to this address.")
        print("  Detected addresses:", ", ".join(f"0x{a:02X}" for a in devices))
        return

    print(f"\n[2] Detecting sensor model at 0x{VL53_ADDR:02X}...")
    model, model_id = detect_model(bus, VL53_ADDR)
    bus.close()

    if model is None:
        print("  Device present but model-ID did not match VL53L0X or VL53L1X.")
        print("  Confirm the sensor is a VL53L0X (ID=0xEE) or VL53L1X (ID=0xEA).")
        return

    print(f"  Model ID register: 0x{model_id:02X}  =>  {model} detected")

    # Step 3 - live readings
    print(f"\n[3] Initializing {model} and starting live read...")
    try:
        if model == "VL53L0X":
            run_vl53l0x(VL53_ADDR)
        else:
            run_vl53l1x(VL53_ADDR)
    except ImportError as e:
        pkg = "VL53L0X" if model == "VL53L0X" else "vl53l1x"
        print(f"\n  Missing Python package: {e}")
        print(f"  Install with:  pip install {pkg}")
    except Exception as e:
        print(f"\n  Sensor error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDone.")
