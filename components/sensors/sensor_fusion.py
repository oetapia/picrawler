#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensor fusion for unified sensor reading and interpretation.

Provides a centralized interface for reading and combining data from
multiple sensors (distance, accelerometer, IR floor sensors).

Includes tilt-aware distance classification to distinguish between
floor readings and actual obstacles.
"""

import time
from collections import deque

from components.sensors.distance_sensor import create_distance_sensor
from components.sensors import accelerometer
# ir_distance is imported lazily in get_floor_sensors() to avoid GPIO conflicts
from components.sensors.tilt_aware_tof import (
    classify_distance_reading,
    classify_rear_distance_reading,
    ClassifiedReading, 
    ReadingType,
    should_trigger_obstacle_avoidance,
    get_display_text
)
from components.utils.config import DISTANCE_SENSOR_TYPE, DISTANCE_SENSOR_CONFIG


class SensorHub:
    """
    Unified sensor interface with fusion capabilities.
    
    Manages all sensor readings and provides debouncing, filtering,
    and combined sensor analysis. Supports both single and dual ToF sensors,
    with proper multiplexer handling for accelerometer access.
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
        
        # Check if using dual ToF sensors with multiplexer
        self.has_dual_tof = (distance_sensor_type == "FRONT_REAR_VL53L0X")
        self.accel_mux_channel = None
        
        # Initialize accelerometer (handle multiplexer case)
        self.accel_available = False
        if self.has_dual_tof and self.distance_sensor:
            # Accelerometer is on multiplexer - access through dual ToF sensor's mux
            try:
                from components.utils.config import ACCEL_CHANNEL
                self.accel_mux_channel = ACCEL_CHANNEL
                self.distance_sensor.mux.select_channel(ACCEL_CHANNEL)
                time.sleep(0.05)
                accelerometer.wake()
                time.sleep(0.1)
                self.accel_available = True
                print(f"[EMOJI] Accelerometer initialized via multiplexer (channel {ACCEL_CHANNEL})")
            except Exception as e:
                print(f"[EMOJI] Accelerometer initialization failed (multiplexer): {e}")
                self.accel_available = False
        else:
            # Standalone accelerometer - direct access
            try:
                accelerometer.wake()
                time.sleep(0.1)
                self.accel_available = True
                print("[EMOJI] Accelerometer initialized (direct access)")
            except Exception as e:
                print(f"[EMOJI] Accelerometer initialization failed: {e}")
                self.accel_available = False
        
        # Floor sensor debouncing - track history to avoid false positives
        self.floor_danger_history = deque(maxlen=3)  # Last 3 readings
        self.floor_danger_threshold = 2  # Need 2/3 readings to confirm danger
    
    def get_distance(self):
        """
        Get filtered distance reading (backward compatible).
        
        For dual ToF sensors, returns front distance.
        For single sensors, returns the sensor reading.
        
        Returns:
            float: Distance in cm (999 if no sensor available)
        """
        if self.distance_sensor is None:
            return 999.0
        
        if self.has_dual_tof:
            return self.distance_sensor.read_front_filtered()
        else:
            return self.distance_sensor.read_filtered()
    
    def get_front_distance(self):
        """
        Get front distance reading (dual sensor aware).
        
        Returns:
            float: Front distance in cm (999 if no sensor available)
        """
        if self.distance_sensor is None:
            return 999.0
        
        if self.has_dual_tof:
            return self.distance_sensor.read_front_filtered()
        else:
            return self.get_distance()
    
    def get_rear_distance(self):
        """
        Get rear distance reading (dual sensor only).
        
        Returns:
            float: Rear distance in cm (999 if not available or single sensor)
        """
        if self.distance_sensor is None or not self.has_dual_tof:
            return 999.0
        
        return self.distance_sensor.read_rear_filtered()
    
    def get_both_distances(self):
        """
        Get both front and rear distances.
        
        Returns:
            tuple: (front_distance, rear_distance) in cm
        """
        return self.get_front_distance(), self.get_rear_distance()
    
    def get_tilt(self):
        """
        Get pitch and roll from accelerometer with multiplexer support.
        
        Returns:
            tuple: (pitch, roll) in degrees, (0.0, 0.0) if unavailable
        """
        if not self.accel_available:
            return 0.0, 0.0
        
        try:
            # Switch to accelerometer channel if using multiplexer
            if self.has_dual_tof and self.accel_mux_channel is not None:
                self.distance_sensor.mux.select_channel(self.accel_mux_channel)
                time.sleep(0.002)  # Small delay for channel switch
            
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
            # Lazy import to avoid GPIO conflicts when ir_distance is not needed
            from components.sensors import ir_distance
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
    
    # ========================================================================
    # TILT-AWARE DISTANCE CLASSIFICATION
    # ========================================================================
    
    def get_classified_distance(self, warning_distance: float = 30.0) -> ClassifiedReading:
        """
        Get distance reading with tilt-aware classification.
        
        Uses pitch angle to determine if the ToF sensor is seeing
        the floor instead of an actual obstacle.
        
        Args:
            warning_distance: Distance threshold for obstacle warnings (cm)
            
        Returns:
            ClassifiedReading with distance, type (obstacle/floor/clear), 
            confidence, and explanation
        """
        distance = self.get_distance()
        pitch, roll = self.get_tilt()
        
        return classify_distance_reading(distance, pitch, roll)
    
    def should_avoid_obstacle(self, warning_distance: float = 30.0) -> tuple:
        """
        Check if obstacle avoidance should be triggered (tilt-aware).
        
        Filters out floor readings when robot is tilted forward.
        
        Args:
            warning_distance: Distance threshold for warnings (cm)
            
        Returns:
            tuple: (should_avoid: bool, classified_reading: ClassifiedReading)
        """
        classified = self.get_classified_distance(warning_distance)
        should_avoid = should_trigger_obstacle_avoidance(classified, warning_distance)
        
        return should_avoid, classified
    
    def get_distance_display_info(self) -> tuple:
        """
        Get display-friendly text for current distance reading.
        
        Returns:
            tuple: (type_text, detail_text) for OLED display
        """
        classified = self.get_classified_distance()
        return get_display_text(classified)
    
    # ========================================================================
    # REAR SENSOR TILT-AWARE CLASSIFICATION
    # ========================================================================
    
    def get_classified_rear_distance(self, warning_distance: float = 25.0) -> ClassifiedReading:
        """
        Get rear distance reading with tilt-aware classification.
        
        Uses pitch angle to determine if the rear ToF sensor is seeing
        the floor instead of an actual obstacle behind.
        
        The rear sensor sees floor when tilted BACKWARD (negative pitch).
        
        Args:
            warning_distance: Distance threshold for obstacle warnings (cm)
            
        Returns:
            ClassifiedReading with distance, type (obstacle/floor/clear), 
            confidence, and explanation
        """
        if not self.has_dual_tof:
            # No rear sensor available
            return ClassifiedReading(
                distance=999.0,
                reading_type=ReadingType.CLEAR,
                confidence=0.0,
                pitch=0.0,
                reason="No rear sensor available"
            )
        
        distance = self.get_rear_distance()
        pitch, roll = self.get_tilt()
        
        return classify_rear_distance_reading(distance, pitch, roll)
    
    def should_avoid_rear_obstacle(self, warning_distance: float = 25.0) -> tuple:
        """
        Check if rear obstacle avoidance should be triggered (tilt-aware).
        
        Filters out floor readings when robot is tilted backward.
        Useful when deciding whether it's safe to back up.
        
        Args:
            warning_distance: Distance threshold for warnings (cm)
            
        Returns:
            tuple: (should_avoid: bool, classified_reading: ClassifiedReading)
        """
        classified = self.get_classified_rear_distance(warning_distance)
        should_avoid = should_trigger_obstacle_avoidance(classified, warning_distance)
        
        return should_avoid, classified
    
    def is_backward_safe_tilt_aware(self, threshold: float = 15.0) -> tuple:
        """
        Check if it's safe to move backward using tilt-aware rear sensor.
        
        Filters out floor readings that occur when tilted backward.
        
        Args:
            threshold: Minimum safe distance (default 15cm)
            
        Returns:
            tuple: (is_safe: bool, classified_reading: ClassifiedReading)
        """
        classified = self.get_classified_rear_distance(threshold)
        
        # Safe if clear, floor reading (filtered), or obstacle is far enough
        is_safe = (
            classified.reading_type == ReadingType.CLEAR or
            classified.reading_type == ReadingType.FLOOR or
            (classified.reading_type == ReadingType.OBSTACLE and classified.distance > threshold)
        )
        
        return is_safe, classified
    
    def get_rear_display_info(self) -> tuple:
        """
        Get display-friendly text for rear distance reading.
        
        Returns:
            tuple: (type_text, detail_text) for OLED display
        """
        classified = self.get_classified_rear_distance()
        return get_display_text(classified, sensor="rear")
