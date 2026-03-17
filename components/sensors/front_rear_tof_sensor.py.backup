#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dual VL53L0X ToF Sensors with PCA9548A Multiplexer

This module provides a high-level interface for front and rear VL53L0X ToF sensors
operating through a PCA9548A I2C multiplexer, enabling 360-degree distance awareness.

Hardware Requirements:
    - PCA9548A I2C Multiplexer
    - 2x VL53L0X ToF sensors (front and rear)
    - MPU6050 Accelerometer (optional, on same multiplexer)

Typical Configuration:
    - SD1 (Channel 1): Rear VL53L0X ToF sensor
    - SD2 (Channel 2): Front VL53L0X ToF sensor  
    - SD7 (Channel 7): MPU6050 Accelerometer

Usage:
    from components.sensors.front_rear_tof_sensor import FrontRearToFSensors
    
    # Create dual ToF sensor interface
    sensors = FrontRearToFSensors(
        mux_address=0x70,
        front_channel=2,
        rear_channel=1
    )
    
    # Read distances
    front_dist = sensors.read_front()  # Front distance in cm
    rear_dist = sensors.read_rear()    # Rear distance in cm
    
    # Or use filtered readings
    front_filtered = sensors.read_front_filtered()
    rear_filtered = sensors.read_rear_filtered()
    
    # Check for obstacles
    if sensors.has_front_obstacle(threshold=25):
        print("Obstacle ahead!")
    
    if sensors.has_rear_obstacle(threshold=15):
        print("Obstacle behind!")
    
    # Cleanup when done
    sensors.close()
"""

import time


class FrontRearToFSensors:
    """
    Front and Rear VL53L0X ToF sensors with PCA9548A multiplexer.
    
    Provides a clean interface for dual ToF sensors, handling multiplexer
    channel switching and sensor communication automatically.
    """
    
    def __init__(self, mux_address=0x70, front_channel=2, rear_channel=1,
                 i2c_bus=1, history_size=5):
        """
        Initialize dual ToF sensors with multiplexer.
        
        Args:
            mux_address: I2C address of PCA9548A multiplexer (default 0x70)
            front_channel: Multiplexer channel for front ToF (default 2)
            rear_channel: Multiplexer channel for rear ToF (default 1)
            i2c_bus: I2C bus number (default 1)
            history_size: Number of readings to keep for filtering (default 5)
        
        Raises:
            ImportError: If required libraries are not available
            RuntimeError: If sensor initialization fails
        """
        self.mux_address = mux_address
        self.front_channel = front_channel
        self.rear_channel = rear_channel
        self.i2c_bus = i2c_bus
        
        # Import required libraries
        try:
            import VL53L0X
            from components.sensors.pca9548a_mux import PCA9548A
            self.VL53L0X = VL53L0X
            self.PCA9548A = PCA9548A
        except ImportError as e:
            raise ImportError(
                f"Required libraries not available: {e}\n"
                "Install with: pip install VL53L0X"
            )
        
        # Reading history for filtering
        self.history_size = history_size
        self.front_history = []
        self.rear_history = []
        self.last_valid_front = 999
        self.last_valid_rear = 999
        
        # Initialize hardware
        self.mux = None
        self.front_tof = None
        self.rear_tof = None
        self.initialized = False
        
        self._initialize_hardware()
    
    def _initialize_hardware(self):
        """Initialize multiplexer and ToF sensors."""
        try:
            # Initialize multiplexer
            self.mux = self.PCA9548A(bus_number=self.i2c_bus, address=self.mux_address)
            print(f"[EMOJI] PCA9548A multiplexer initialized at 0x{self.mux_address:02X}")
            
            # Initialize front ToF
            print(f"  Initializing front ToF on channel {self.front_channel}...")
            self.mux.select_channel(self.front_channel)
            time.sleep(0.05)
            self.front_tof = self.VL53L0X.VL53L0X(i2c_bus=self.i2c_bus, i2c_address=0x29)
            self.front_tof.open()
            self.front_tof.start_ranging(self.VL53L0X.Vl53l0xAccuracyMode.BETTER)
            print(f"[EMOJI] Front ToF initialized")
            
            # Initialize rear ToF
            print(f"  Initializing rear ToF on channel {self.rear_channel}...")
            self.mux.select_channel(self.rear_channel)
            time.sleep(0.05)
            self.rear_tof = self.VL53L0X.VL53L0X(i2c_bus=self.i2c_bus, i2c_address=0x29)
            self.rear_tof.open()
            self.rear_tof.start_ranging(self.VL53L0X.Vl53l0xAccuracyMode.BETTER)
            print(f"[EMOJI] Rear ToF initialized")
            
            self.initialized = True
            print("[EMOJI] Dual ToF sensors ready")
            
        except Exception as e:
            self.initialized = False
            raise RuntimeError(f"Failed to initialize ToF sensors: {e}")
    
    def read_front(self):
        """
        Read front distance sensor.
        
        Returns:
            float: Distance in cm, or 999 if error/out of range
        """
        if not self.initialized or self.front_tof is None:
            return 999
        
        try:
            # Switch to front ToF channel
            self.mux.select_channel(self.front_channel)
            time.sleep(0.002)  # Small delay for channel switch
            
            # Read distance in mm, convert to cm
            distance_mm = self.front_tof.get_distance()
            distance_cm = distance_mm / 10.0
            
            # Filter invalid readings
            if 2 <= distance_cm <= 120:  # VL53L0X valid range
                self.last_valid_front = distance_cm
                return distance_cm
            return self.last_valid_front
            
        except Exception as e:
            print(f"Front ToF read error: {e}")
            return self.last_valid_front
    
    def read_rear(self):
        """
        Read rear distance sensor.
        
        Returns:
            float: Distance in cm, or 999 if error/out of range
        """
        if not self.initialized or self.rear_tof is None:
            return 999
        
        try:
            # Switch to rear ToF channel
            self.mux.select_channel(self.rear_channel)
            time.sleep(0.002)  # Small delay for channel switch
            
            # Read distance in mm, convert to cm
            distance_mm = self.rear_tof.get_distance()
            distance_cm = distance_mm / 10.0
            
            # Filter invalid readings
            if 2 <= distance_cm <= 120:  # VL53L0X valid range
                self.last_valid_rear = distance_cm
                return distance_cm
            return self.last_valid_rear
            
        except Exception as e:
            print(f"Rear ToF read error: {e}")
            return self.last_valid_rear
    
    def read_front_filtered(self):
        """
        Read front distance with median filtering to reduce noise.
        
        Returns:
            float: Filtered distance in cm
        """
        reading = self.read_front()
        
        # Add to history
        self.front_history.append(reading)
        if len(self.front_history) > self.history_size:
            self.front_history.pop(0)
        
        # Return median of history
        if len(self.front_history) >= 3:
            sorted_history = sorted(self.front_history)
            return sorted_history[len(sorted_history) // 2]
        return reading
    
    def read_rear_filtered(self):
        """
        Read rear distance with median filtering to reduce noise.
        
        Returns:
            float: Filtered distance in cm
        """
        reading = self.read_rear()
        
        # Add to history
        self.rear_history.append(reading)
        if len(self.rear_history) > self.history_size:
            self.rear_history.pop(0)
        
        # Return median of history
        if len(self.rear_history) >= 3:
            sorted_history = sorted(self.rear_history)
            return sorted_history[len(sorted_history) // 2]
        return reading
    
    def read_both(self, filtered=True):
        """
        Read both front and rear distances.
        
        Args:
            filtered: If True, use filtered readings (default True)
        
        Returns:
            tuple: (front_distance, rear_distance) in cm
        """
        if filtered:
            return self.read_front_filtered(), self.read_rear_filtered()
        else:
            return self.read_front(), self.read_rear()
    
    def has_front_obstacle(self, threshold=25):
        """
        Check if there's an obstacle in front.
        
        Args:
            threshold: Distance threshold in cm (default 25)
        
        Returns:
            bool: True if obstacle detected within threshold
        """
        return self.read_front_filtered() < threshold
    
    def has_rear_obstacle(self, threshold=25):
        """
        Check if there's an obstacle behind.
        
        Args:
            threshold: Distance threshold in cm (default 25)
        
        Returns:
            bool: True if obstacle detected within threshold
        """
        return self.read_rear_filtered() < threshold
    
    def get_closest_obstacle(self):
        """
        Get the closest obstacle from either sensor.
        
        Returns:
            tuple: (distance, direction) where direction is 'front' or 'rear'
        """
        front = self.read_front_filtered()
        rear = self.read_rear_filtered()
        
        if front < rear:
            return front, 'front'
        else:
            return rear, 'rear'
    
    def is_clear(self, front_threshold=40, rear_threshold=20):
        """
        Check if both front and rear are clear.
        
        Args:
            front_threshold: Front clearance threshold in cm (default 40)
            rear_threshold: Rear clearance threshold in cm (default 20)
        
        Returns:
            bool: True if both sensors show clear path
        """
        front = self.read_front_filtered()
        rear = self.read_rear_filtered()
        return front > front_threshold and rear > rear_threshold
    
    def close(self):
        """Stop ranging and close both sensors."""
        print("Closing ToF sensors...")
        
        # Close front ToF
        if self.front_tof:
            try:
                self.mux.select_channel(self.front_channel)
                time.sleep(0.01)
                self.front_tof.stop_ranging()
                self.front_tof.close()
                print("  [EMOJI] Front ToF closed")
            except Exception as e:
                print(f"  Front ToF cleanup error: {e}")
        
        # Close rear ToF
        if self.rear_tof:
            try:
                self.mux.select_channel(self.rear_channel)
                time.sleep(0.01)
                self.rear_tof.stop_ranging()
                self.rear_tof.close()
                print("  [EMOJI] Rear ToF closed")
            except Exception as e:
                print(f"  Rear ToF cleanup error: {e}")
        
        # Close multiplexer
        if self.mux:
            try:
                self.mux.close()
                print("  [EMOJI] Multiplexer closed")
            except Exception as e:
                print(f"  Multiplexer cleanup error: {e}")
        
        self.initialized = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
        return False


def main():
    """Test dual ToF sensors."""
    print("Dual ToF Sensor Test")
    print("=" * 60)
    
    try:
        # Create sensor interface
        sensors = FrontRearToFSensors(
            mux_address=0x70,
            front_channel=2,
            rear_channel=1
        )
        
        print("\nReading distances (Ctrl+C to exit)...\n")
        
        while True:
            front, rear = sensors.read_both(filtered=True)
            
            # Create visual bars
            front_bar = "#" * int(min(40, front / 3))
            rear_bar = "#" * int(min(40, rear / 3))
            
            print(f"Front: {front:6.1f} cm [{front_bar:<40}]")
            print(f"Rear:  {rear:6.1f} cm [{rear_bar:<40}]")
            
            # Check for obstacles
            if sensors.has_front_obstacle(25):
                print("  [EMOJI]  Front obstacle detected!")
            if sensors.has_rear_obstacle(15):
                print("  [EMOJI]  Rear obstacle detected!")
            
            print()
            time.sleep(0.2)
    
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'sensors' in locals():
            sensors.close()
        print("\nTest complete")


if __name__ == "__main__":
    main()
