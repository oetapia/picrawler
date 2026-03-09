#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Distance Sensor Abstraction Layer
Supports multiple distance sensor types: HC-SR04, VL53L0X, VL53L1X
"""

from robot_hat import Pin
import time


class DistanceSensor:
    """Abstract base class for distance sensors"""
    
    def __init__(self):
        self.sensor = None
        self.sensor_type = None
        self.last_valid_reading = 999
        self.reading_history = []
        self.history_size = 5
        
    def read(self):
        """Read distance in cm. Returns 999 if error or out of range."""
        raise NotImplementedError("Subclasses must implement read()")
    
    def read_filtered(self):
        """Read distance with median filtering to reduce noise"""
        reading = self.read()
        
        # Add to history
        self.reading_history.append(reading)
        if len(self.reading_history) > self.history_size:
            self.reading_history.pop(0)
        
        # Return median of history
        if len(self.reading_history) >= 3:
            sorted_history = sorted(self.reading_history)
            return sorted_history[len(sorted_history) // 2]
        return reading
    
    def get_sensor_type(self):
        """Return the type of sensor"""
        return self.sensor_type


class UltrasonicSensor(DistanceSensor):
    """HC-SR04 Ultrasonic distance sensor"""
    
    def __init__(self, trigger_pin, echo_pin):
        super().__init__()
        self.sensor_type = "HC-SR04"
        try:
            from robot_hat import Ultrasonic
            self.sensor = Ultrasonic(trigger_pin, echo_pin)
            print(f"✓ {self.sensor_type} initialized on trigger={trigger_pin.id()}, echo={echo_pin.id()}")
        except Exception as e:
            print(f"✗ Failed to initialize {self.sensor_type}: {e}")
            self.sensor = None
    
    def read(self):
        """Read distance in cm"""
        if self.sensor is None:
            return 999
        
        try:
            distance = self.sensor.read()
            # Filter invalid readings
            if distance <= 0 or distance == -2:
                return self.last_valid_reading
            if 2 <= distance <= 400:  # HC-SR04 valid range
                self.last_valid_reading = distance
                return distance
            return self.last_valid_reading
        except Exception as e:
            print(f"Ultrasonic read error: {e}")
            return self.last_valid_reading


class VL53L0XSensor(DistanceSensor):
    """VL53L0X Time-of-Flight distance sensor (up to ~120cm)"""
    
    def __init__(self, i2c_address=0x29):
        super().__init__()
        self.sensor_type = "VL53L0X"
        try:
            import VL53L0X
            self.sensor = VL53L0X.VL53L0X(i2c_bus=1, i2c_address=i2c_address)
            self.sensor.open()
            self.sensor.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)
            print(f"✓ {self.sensor_type} initialized on I2C address 0x{i2c_address:02X}")
        except Exception as e:
            print(f"✗ Failed to initialize {self.sensor_type}: {e}")
            print("   Install with: pip install VL53L0X")
            self.sensor = None
    
    def read(self):
        """Read distance in cm"""
        if self.sensor is None:
            return 999
        
        try:
            distance_mm = self.sensor.get_distance()
            distance_cm = distance_mm / 10.0
            
            # Filter invalid readings
            if 2 <= distance_cm <= 120:  # VL53L0X valid range
                self.last_valid_reading = distance_cm
                return distance_cm
            return self.last_valid_reading
        except Exception as e:
            print(f"VL53L0X read error: {e}")
            return self.last_valid_reading
    
    def close(self):
        """Stop ranging and close sensor"""
        if self.sensor:
            try:
                self.sensor.stop_ranging()
                self.sensor.close()
            except:
                pass


class VL53L1XSensor(DistanceSensor):
    """VL53L1X Time-of-Flight distance sensor (up to ~400cm)"""
    
    def __init__(self, i2c_address=0x29):
        super().__init__()
        self.sensor_type = "VL53L1X"
        try:
            import VL53L1X
            self.sensor = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=i2c_address)
            self.sensor.open()
            self.sensor.start_ranging(1)  # 1 = short distance mode
            print(f"✓ {self.sensor_type} initialized on I2C address 0x{i2c_address:02X}")
        except Exception as e:
            print(f"✗ Failed to initialize {self.sensor_type}: {e}")
            print("   Install with: pip install vl53l1x")
            self.sensor = None
    
    def read(self):
        """Read distance in cm"""
        if self.sensor is None:
            return 999
        
        try:
            distance_mm = self.sensor.get_distance()
            distance_cm = distance_mm / 10.0
            
            # Filter invalid readings
            if 2 <= distance_cm <= 400:  # VL53L1X valid range
                self.last_valid_reading = distance_cm
                return distance_cm
            return self.last_valid_reading
        except Exception as e:
            print(f"VL53L1X read error: {e}")
            return self.last_valid_reading
    
    def close(self):
        """Stop ranging and close sensor"""
        if self.sensor:
            try:
                self.sensor.stop_ranging()
                self.sensor.close()
            except:
                pass


def create_distance_sensor(sensor_type="HC-SR04", **kwargs):
    """
    Factory function to create the appropriate distance sensor.
    
    Args:
        sensor_type: "HC-SR04", "VL53L0X", or "VL53L1X"
        **kwargs: Sensor-specific parameters
            For HC-SR04: trigger_pin, echo_pin (Pin objects)
            For VL53L0X/VL53L1X: i2c_address (default 0x29)
    
    Returns:
        DistanceSensor instance or None if initialization failed
    
    Examples:
        # HC-SR04 Ultrasonic
        sensor = create_distance_sensor("HC-SR04", 
                                       trigger_pin=Pin("D2"), 
                                       echo_pin=Pin("D3"))
        
        # VL53L0X Time-of-Flight
        sensor = create_distance_sensor("VL53L0X", i2c_address=0x29)
        
        # VL53L1X Time-of-Flight
        sensor = create_distance_sensor("VL53L1X", i2c_address=0x29)
    """
    sensor_type = sensor_type.upper()
    
    if sensor_type == "HC-SR04":
        trigger_pin = kwargs.get('trigger_pin')
        echo_pin = kwargs.get('echo_pin')
        if not trigger_pin or not echo_pin:
            print("Error: HC-SR04 requires trigger_pin and echo_pin")
            return None
        return UltrasonicSensor(trigger_pin, echo_pin)
    
    elif sensor_type == "VL53L0X":
        i2c_address = kwargs.get('i2c_address', 0x29)
        return VL53L0XSensor(i2c_address)
    
    elif sensor_type == "VL53L1X":
        i2c_address = kwargs.get('i2c_address', 0x29)
        return VL53L1XSensor(i2c_address)
    
    else:
        print(f"Unknown sensor type: {sensor_type}")
        print("Supported types: HC-SR04, VL53L0X, VL53L1X")
        return None


def main():
    """Test distance sensor"""
    print("Distance Sensor Test")
    print("=" * 50)
    
    # Try to create sensor (defaults to HC-SR04)
    sensor = create_distance_sensor("HC-SR04", 
                                   trigger_pin=Pin("D2"), 
                                   echo_pin=Pin("D3"))
    
    if sensor is None:
        print("Failed to initialize sensor")
        return
    
    print(f"\nTesting {sensor.get_sensor_type()}")
    print("Press Ctrl+C to exit\n")
    
    try:
        while True:
            distance = sensor.read()
            filtered = sensor.read_filtered()
            print(f"Distance: {distance:6.1f} cm  |  Filtered: {filtered:6.1f} cm")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nTest stopped")
    finally:
        if hasattr(sensor, 'close'):
            sensor.close()


if __name__ == "__main__":
    main()
