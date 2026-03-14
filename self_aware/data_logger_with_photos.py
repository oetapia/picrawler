#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Data Logger with Synchronized Photo Capture

Combines sensor data logging with image capture for ML dataset creation.
Maintains synchronized CSV files linking photos to sensor readings and actions.
"""

import csv
import time
from datetime import datetime
from pathlib import Path

from self_aware.data_logger import DataLogger
from self_aware.photo_logger import PhotoLogger


class DataLoggerWithPhotos(DataLogger):
    """
    Enhanced data logger with synchronized photo capture.
    
    Combines sensor logging with image capture for ML datasets.
    Creates:
    - sensor_data.csv (all sensor readings, 10 Hz default)
    - photo_manifest.csv (photo metadata, 1-2 Hz default)
    - photos/ directory (JPEG images)
    
    Example:
        logger = DataLoggerWithPhotos(
            capture_photos=True,
            photo_rate_hz=2.0,
            photo_resolution=(320, 240)
        )
        logger.start_photo_capture()
        
        # In navigation loop
        logger.log_entry_with_photo(sensor_data, action_data, context_data)
        
        logger.close()
    """
    
    def __init__(self, log_dir="self_aware/logs", 
                 format="csv",
                 buffer_size=100,
                 capture_photos=True,
                 photo_rate_hz=2.0,
                 photo_resolution=(320, 240)):
        """
        Initialize combined logger.
        
        Args:
            log_dir: Log directory base path
            format: "csv" or "json" for sensor data
            buffer_size: Sensor data buffer size
            capture_photos: Enable photo capture
            photo_rate_hz: Photos per second (1-5 Hz recommended)
            photo_resolution: Photo size tuple (width, height)
        """
        # Initialize base sensor logger with custom filename
        self.log_dir = Path(log_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_dir = self.log_dir / f"session_{timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Store format and buffer settings
        self.format = format.lower()
        self.buffer_size = buffer_size
        
        # Call parent init with session-specific path
        super().__init__(
            log_dir=str(self.session_dir),
            format=format,
            buffer_size=buffer_size
        )
        
        # Override the log file to be in session directory
        filename = f"sensor_data.{self.format}"
        self.log_file = self.session_dir / filename
        
        # Reinitialize CSV with new path
        if self.format == "csv" and self.csv_file:
            self.csv_file.close()
            self._init_csv()
        
        # Add photo capture
        self.capture_photos = capture_photos
        self.photo_logger = None
        self.manifest_file = None
        self.manifest_csv = None
        self.manifest_writer = None
        
        if capture_photos:
            self.photo_logger = PhotoLogger(
                session_dir=str(self.session_dir),
                resolution=photo_resolution,
                capture_rate_hz=photo_rate_hz
            )
            
            # Initialize photo manifest
            self._init_photo_manifest()
        
        print(f"📦 Session created: {self.session_dir}")
    
    def _init_photo_manifest(self):
        """Create CSV manifest linking photos to sensor data."""
        self.manifest_file = self.session_dir / "photo_manifest.csv"
        self.manifest_csv = open(self.manifest_file, 'w', newline='')
        
        manifest_headers = [
            'frame_id',
            'timestamp',
            'filename',
            'sensor_row',
            'label',
            'auto_label',
            'front_distance_cm',
            'rear_distance_cm',
            'floor_danger_count',
            'pitch',
            'roll',
            'action',
            'state'
        ]
        
        self.manifest_writer = csv.DictWriter(
            self.manifest_csv, 
            fieldnames=manifest_headers
        )
        self.manifest_writer.writeheader()
        self.manifest_csv.flush()
    
    def start_photo_capture(self):
        """Start photo capture (call after logger initialization)."""
        if self.photo_logger:
            self.photo_logger.start()
    
    def log_entry_with_photo(self, sensor_data, action_data, 
                             context_data, manual_label=None):
        """
        Log entry with optional photo capture.
        
        Photos are captured at a lower rate (photo_rate_hz) than sensor
        data (typically 10 Hz), so not every log entry will have a photo.
        
        Args:
            sensor_data: Sensor readings dict
                - front_distance or distance: Front distance in cm
                - rear_distance: Rear distance in cm (optional)
                - pitch, roll: Tilt angles
                - floor_fl, floor_fr, floor_bl, floor_br: Floor sensors
            action_data: Action taken dict
                - action: Action name ('forward', 'backward', 'turn_left', etc.)
                - steps: Number of steps
                - speed: Movement speed
            context_data: Robot state dict
                - state: Current state ('exploring', 'avoiding', etc.)
                - previous_state: Previous state
                - consecutive_obstacles: Counter
            manual_label: Optional manual label override
        """
        # Log sensor data (parent class functionality)
        self.log_entry(sensor_data, action_data, context_data)
        
        # Capture photo if enabled (throttled internally)
        if self.photo_logger:
            # Auto-generate label from sensors
            auto_label = self._auto_label(sensor_data, action_data)
            label = manual_label if manual_label else auto_label
            
            # Attempt capture (returns None if throttled)
            photo_metadata = self.photo_logger.capture_if_ready(
                sensor_data=sensor_data,
                label=label
            )
            
            # Log to manifest if photo was captured
            if photo_metadata:
                manifest_entry = {
                    'frame_id': photo_metadata['frame_id'],
                    'timestamp': photo_metadata['timestamp'],
                    'filename': photo_metadata['filename'],
                    'sensor_row': self.entries_logged,
                    'label': label,
                    'auto_label': auto_label,
                    'front_distance_cm': sensor_data.get('front_distance', 
                                                         sensor_data.get('distance', 999.0)),
                    'rear_distance_cm': sensor_data.get('rear_distance', 999.0),
                    'floor_danger_count': sum([
                        sensor_data.get('floor_fl', 0),
                        sensor_data.get('floor_fr', 0),
                        sensor_data.get('floor_bl', 0),
                        sensor_data.get('floor_br', 0)
                    ]),
                    'pitch': sensor_data.get('pitch', 0.0),
                    'roll': sensor_data.get('roll', 0.0),
                    'action': action_data.get('action', 'none'),
                    'state': context_data.get('state', 'unknown')
                }
                
                self.manifest_writer.writerow(manifest_entry)
                self.manifest_csv.flush()
    
    def _auto_label(self, sensor_data, action_data):
        """
        Generate automatic label from sensor readings.
        
        Priority hierarchy:
        1. Floor danger (highest priority)
        2. Close obstacles
        3. Medium obstacles
        4. Clear path
        
        Args:
            sensor_data: Sensor readings
            action_data: Action taken
        
        Returns:
            str: Auto-generated label
        """
        front_dist = sensor_data.get('front_distance', 
                                     sensor_data.get('distance', 999.0))
        floor_danger = sum([
            sensor_data.get('floor_fl', 0),
            sensor_data.get('floor_fr', 0),
            sensor_data.get('floor_bl', 0),
            sensor_data.get('floor_br', 0)
        ])
        
        # Priority-based labeling
        if floor_danger > 0:
            if floor_danger >= 3:
                return "floor_danger_severe"
            else:
                return "floor_danger"
        elif front_dist < 10:
            return "obstacle_very_close"
        elif front_dist < 20:
            return "obstacle_close"
        elif front_dist < 35:
            return "obstacle_medium"
        elif front_dist < 50:
            return "obstacle_far"
        else:
            return "clear_path"
    
    def close(self):
        """Close logger and photo capture."""
        # Stop photos first
        if self.photo_logger:
            self.photo_logger.stop()
            if self.manifest_csv:
                self.manifest_csv.close()
        
        # Close sensor logger
        super().close()
        
        # Print combined stats
        print(f"\n📦 Session Summary")
        print(f"   Location: {self.session_dir}")
        print(f"   Sensor entries: {self.entries_logged}")
        if self.photo_logger:
            photo_stats = self.photo_logger.get_stats()
            print(f"   Photos captured: {photo_stats['frames_captured']}")
            
            # Calculate dataset size
            import os
            sensor_size = self.log_file.stat().st_size / (1024*1024) if self.log_file.exists() else 0
            photos_size = sum(f.stat().st_size for f in self.session_dir.glob('photos/*.jpg')) / (1024*1024)
            print(f"   Dataset size: {sensor_size + photos_size:.2f} MB")


# ============================================================================
# MAIN - For testing
# ============================================================================

def main():
    """Test combined data logger with photos."""
    print("Testing DataLoggerWithPhotos...")
    
    # Create logger
    logger = DataLoggerWithPhotos(
        log_dir="self_aware/logs",
        capture_photos=True,
        photo_rate_hz=2.0,
        photo_resolution=(320, 240)
    )
    
    # Start photo capture
    logger.start_photo_capture()
    
    # Simulate logging
    print("\nSimulating 30 sensor readings with photo capture...")
    for i in range(30):
        sensor_data = {
            'distance': 25.5 + i,
            'front_distance': 25.5 + i,
            'rear_distance': 50.0 - i,
            'pitch': 1.5,
            'roll': -0.8,
            'accel_x': 0.1, 'accel_y': 0.0, 'accel_z': 1.0,
            'gyro_x': 0.0, 'gyro_y': 0.0, 'gyro_z': 0.0,
            'floor_fl': 0, 'floor_fr': 0, 'floor_bl': 0, 'floor_br': 0,
        }
        
        action_data = {
            'action': 'forward',
            'steps': 1,
            'speed': 70,
        }
        
        context_data = {
            'state': 'exploring',
            'previous_state': 'exploring',
            'current_speed': 70,
            'consecutive_obstacles': 0,
            'consecutive_floor_dangers': 0,
            'stuck_counter': 0,
        }
        
        logger.log_entry_with_photo(sensor_data, action_data, context_data)
        time.sleep(0.1)  # 10 Hz sensor rate
    
    # Close
    logger.close()
    
    print("\n✓ Test complete! Check self_aware/logs/ for output.")


if __name__ == '__main__':
    main()
