#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensor fusion for unified sensor reading and interpretation.

Provides a centralized interface for reading and combining data from
multiple sensors (distance, accelerometer, IR floor sensors).
"""

import time
from collections import deque

from components.sensors.distance_sensor import create_distance_sensor
from components.sensors import ir_distance, accelerometer
from components.utils.config import DISTANCE_SENSOR_TYPE, DISTANCE_SENSOR_CONFIG


class SensorHub:
    """
    Unified sensor interface with fusion capabilities.
    
    Manages all sensor readings and provides debouncing, filtering,
    and combined sensor analysis.
    """
    
    def __init__(self, distance_sensor_type=DISTANCE_SENSOR_TYPE):
        """
        Initialize sensor hub.
        
        Args:
            distance_sensor_type: Type of distance sensor to use
        """
        # Initialize distance sensor
        sensor_config = DISTANCE_SENSOR_CONFIG.get(distance_sensor_type, {})
        self.distance_sensor = create_distance_sensor(distance_sensor_type, **sensor_config)
        
        # Initialize accelerometer
        try:
            accelerometer.wake()
            time.sleep(0.1)
            self.accel_available = True
        except Exception:
            self.accel_available = False
        
        # Floor sensor debouncing - track history to avoid false positives
        self.floor_danger_history = deque(maxlen=3)  # Last 3 readings
        self.floor_danger_threshold = 2  # Need 2/3 readings to confirm danger
    
    def get_distance(self):
        """
        Get filtered distance reading.
        
        Returns:
            float: Distance in cm (999 if no sensor available)
        """
        if self.distance_sensor is None:
            return 999.0
        return self.distance_sensor.read_filtered()
    
    def get_tilt(self):
        """
        Get pitch and roll from accelerometer.
        
        Returns:
            tuple: (pitch, roll) in degrees, (0.0, 0.0) if unavailable
        """
        if not self.accel_available:
            return 0.0, 0.0
        try:
            return accelerometer.get_tilt()
        except Exception:
            return 0.0, 0.0
    
    def get_floor_sensors(self):
        """
        Read all IR floor sensors.
        
        Returns:
            dict: Sensor readings {'fl': 0/1, 'fr': 0/1, 'bl': 0/1, 'br': 0/1}
        """
        try:
            return ir_distance.read_legs()
        except Exception:
            return {'fl': 0, 'fr': 0, 'bl': 0, 'br': 0}
    
    def check_floor_danger_debounced(self):
        """
        Check floor sensors with debouncing to avoid false positives.
        
        Returns:
            tuple: (danger_type, suggested_action) or (None, None) if safe
                  Only returns confirmed dangers after multiple readings
        """
        from components.navigation.obstacle_handler import ObstacleHandler
        
        handler = ObstacleHandler()
        floor_sensors = self.get_floor_sensors()
        danger_type, suggested_action = handler.analyze_floor_danger(floor_sensors)
        
        # Add current reading to history
        self.floor_danger_history.append((danger_type, suggested_action))
        
        # Only confirm danger if multiple readings agree
        if danger_type:
            # Count how many recent readings show danger
            danger_readings = sum(1 for dt, _ in self.floor_danger_history if dt is not None)
            
            if danger_readings >= self.floor_danger_threshold:
                # Confirmed danger
                self.floor_danger_history.clear()
                return danger_type, suggested_action
        
        return None, None
    
    def has_distance_sensor(self):
        """Check if distance sensor is available."""
        return self.distance_sensor is not None
    
    def has_accelerometer(self):
        """Check if accelerometer is available."""
        return self.accel_available
    
    def close(self):
        """Close sensor connections."""
        if self.distance_sensor and hasattr(self.distance_sensor, 'close'):
            self.distance_sensor.close()
    
    def get_sensor_status(self):
        """
        Get status of all sensors.
        
        Returns:
            dict: Status information for each sensor
        """
        status = {
            'distance_sensor': 'available' if self.has_distance_sensor() else 'unavailable',
            'accelerometer': 'available' if self.has_accelerometer() else 'unavailable',
            'floor_sensors': 'available'  # Always available via IR
        }
        
        if self.has_distance_sensor():
            status['distance_reading'] = self.get_distance()
        
        if self.has_accelerometer():
            pitch, roll = self.get_tilt()
            status['pitch'] = pitch
            status['roll'] = roll
        
        status['floor_readings'] = self.get_floor_sensors()
        
        return status
