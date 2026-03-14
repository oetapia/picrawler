#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Logger for PiCrawler Autonomous Navigation

Logs sensor readings and actions for machine learning training data collection.
Supports CSV and JSON formats with buffered writing for minimal performance impact.
"""

import os
import csv
import json
import time
from datetime import datetime
from collections import deque
from pathlib import Path


class DataLogger:
    """
    Logs sensor data and robot actions for ML training.
    
    Features:
    - Configurable sampling rate (default 10 Hz)
    - CSV or JSON output
    - Buffered writing (minimal I/O impact)
    - Automatic session management
    - Timestamped entries
    """
    
    def __init__(self, log_dir="self_aware/logs", format="csv", buffer_size=100):
        """
        Initialize data logger.
        
        Args:
            log_dir: Directory to save log files
            format: "csv" or "json"
            buffer_size: Number of entries to buffer before writing
        """
        self.log_dir = Path(log_dir)
        self.format = format.lower()
        self.buffer_size = buffer_size
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"session_{timestamp}.{self.format}"
        self.log_file = self.log_dir / filename
        
        # Buffer for batched writes
        self.buffer = deque(maxlen=buffer_size)
        
        # Stats
        self.entries_logged = 0
        self.start_time = time.time()
        
        # CSV writer setup
        self.csv_file = None
        self.csv_writer = None
        self.csv_headers = None
        
        if self.format == "csv":
            self._init_csv()
        
        print(f"📝 Data logger initialized: {self.log_file}")
        print(f"   Format: {self.format.upper()}, Buffer: {buffer_size}, Rate: 10 Hz")
    
    def _init_csv(self):
        """Initialize CSV file with headers."""
        self.csv_headers = [
            'timestamp',
            # Distance sensors (supports both single and dual ToF)
            'front_distance_cm',
            'rear_distance_cm',
            # Accelerometer
            'pitch', 'roll',
            'accel_x', 'accel_y', 'accel_z',
            'gyro_x', 'gyro_y', 'gyro_z',
            # IR floor sensors
            'floor_fl', 'floor_fr', 'floor_bl', 'floor_br',
            # Robot state
            'state', 'previous_state', 'current_speed',
            # Stuck detection context
            'consecutive_obstacles', 'consecutive_floor_dangers', 'stuck_counter',
            # Action taken
            'action', 'action_steps', 'action_speed',
            # Derived features
            'tilt_magnitude', 'floor_danger_count',
        ]
        
        # Write header
        self.csv_file = open(self.log_file, 'w', newline='')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.csv_headers)
        self.csv_writer.writeheader()
        self.csv_file.flush()
    
    def log_entry(self, sensor_data, action_data, context_data):
        """
        Log a single entry.
        
        Args:
            sensor_data: Dict with sensor readings
            action_data: Dict with action information
            context_data: Dict with robot state context
        """
        entry = {
            'timestamp': time.time(),
            
            # Sensors - support both single and dual ToF
            'front_distance_cm': sensor_data.get('front_distance', sensor_data.get('distance', 999.0)),
            'rear_distance_cm': sensor_data.get('rear_distance', 999.0),
            'pitch': sensor_data.get('pitch', 0.0),
            'roll': sensor_data.get('roll', 0.0),
            'accel_x': sensor_data.get('accel_x', 0.0),
            'accel_y': sensor_data.get('accel_y', 0.0),
            'accel_z': sensor_data.get('accel_z', 0.0),
            'gyro_x': sensor_data.get('gyro_x', 0.0),
            'gyro_y': sensor_data.get('gyro_y', 0.0),
            'gyro_z': sensor_data.get('gyro_z', 0.0),
            'floor_fl': sensor_data.get('floor_fl', 0),
            'floor_fr': sensor_data.get('floor_fr', 0),
            'floor_bl': sensor_data.get('floor_bl', 0),
            'floor_br': sensor_data.get('floor_br', 0),
            
            # Context
            'state': context_data.get('state', 'unknown'),
            'previous_state': context_data.get('previous_state', 'unknown'),
            'current_speed': context_data.get('current_speed', 0),
            'consecutive_obstacles': context_data.get('consecutive_obstacles', 0),
            'consecutive_floor_dangers': context_data.get('consecutive_floor_dangers', 0),
            'stuck_counter': context_data.get('stuck_counter', 0),
            
            # Action
            'action': action_data.get('action', 'none'),
            'action_steps': action_data.get('steps', 0),
            'action_speed': action_data.get('speed', 0),
            
            # Derived features
            'tilt_magnitude': (sensor_data.get('pitch', 0)**2 + sensor_data.get('roll', 0)**2)**0.5,
            'floor_danger_count': sum([
                sensor_data.get('floor_fl', 0),
                sensor_data.get('floor_fr', 0),
                sensor_data.get('floor_bl', 0),
                sensor_data.get('floor_br', 0)
            ]),
        }
        
        # Add to buffer
        self.buffer.append(entry)
        self.entries_logged += 1
        
        # Flush buffer if full
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self):
        """Write buffered entries to file."""
        if not self.buffer:
            return
        
        if self.format == "csv":
            self._flush_csv()
        else:
            self._flush_json()
        
        self.buffer.clear()
    
    def _flush_csv(self):
        """Write buffer to CSV file."""
        if self.csv_writer:
            for entry in self.buffer:
                self.csv_writer.writerow(entry)
            self.csv_file.flush()
    
    def _flush_json(self):
        """Write buffer to JSON file."""
        with open(self.log_file, 'a') as f:
            for entry in self.buffer:
                f.write(json.dumps(entry) + '\n')
    
    def close(self):
        """Close logger and flush remaining data."""
        # Flush any remaining entries
        self.flush()
        
        # Close CSV file
        if self.csv_file:
            self.csv_file.close()
        
        # Print stats
        duration = time.time() - self.start_time
        print(f"\n📝 Data logger closed: {self.log_file}")
        print(f"   Total entries: {self.entries_logged}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Average rate: {self.entries_logged/duration:.1f} entries/sec")
    
    def get_stats(self):
        """Get logging statistics."""
        duration = time.time() - self.start_time
        return {
            'entries_logged': self.entries_logged,
            'duration': duration,
            'rate': self.entries_logged / duration if duration > 0 else 0,
            'file_path': str(self.log_file),
            'file_size_mb': self.log_file.stat().st_size / (1024*1024) if self.log_file.exists() else 0
        }


class ThrottledLogger:
    """
    Wrapper around DataLogger that enforces a specific sampling rate.
    
    Ensures we don't log more frequently than desired (e.g., 10 Hz).
    """
    
    def __init__(self, logger, sample_rate_hz=10):
        """
        Initialize throttled logger.
        
        Args:
            logger: DataLogger instance
            sample_rate_hz: Maximum samples per second
        """
        self.logger = logger
        self.sample_interval = 1.0 / sample_rate_hz
        self.last_log_time = 0
    
    def log_entry(self, sensor_data, action_data, context_data):
        """Log entry if enough time has passed since last log."""
        current_time = time.time()
        if current_time - self.last_log_time >= self.sample_interval:
            self.logger.log_entry(sensor_data, action_data, context_data)
            self.last_log_time = current_time
            return True
        return False
    
    def flush(self):
        """Flush underlying logger."""
        self.logger.flush()
    
    def close(self):
        """Close underlying logger."""
        self.logger.close()
    
    def get_stats(self):
        """Get logging statistics."""
        return self.logger.get_stats()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def list_log_files(log_dir="self_aware/logs"):
    """
    List all log files in directory.
    
    Returns:
        List of Path objects
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return []
    
    csv_files = list(log_path.glob("session_*.csv"))
    json_files = list(log_path.glob("session_*.json"))
    return sorted(csv_files + json_files)


def merge_log_files(log_files, output_file="merged_dataset.csv"):
    """
    Merge multiple CSV log files into one.
    
    Args:
        log_files: List of file paths
        output_file: Output merged file path
    """
    import pandas as pd
    
    dfs = []
    for log_file in log_files:
        print(f"Loading {log_file}...")
        df = pd.read_csv(log_file)
        dfs.append(df)
    
    merged_df = pd.concat(dfs, ignore_index=True)
    merged_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Merged {len(log_files)} files → {output_file}")
    print(f"  Total samples: {len(merged_df)}")
    return merged_df


def print_log_summary(log_dir="self_aware/logs"):
    """Print summary of all log files."""
    log_files = list_log_files(log_dir)
    
    if not log_files:
        print(f"No log files found in {log_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"Log Files Summary ({len(log_files)} files)")
    print(f"{'='*60}")
    
    total_size = 0
    for log_file in log_files:
        size_mb = log_file.stat().st_size / (1024*1024)
        total_size += size_mb
        print(f"  {log_file.name:40} {size_mb:6.2f} MB")
    
    print(f"{'='*60}")
    print(f"Total size: {total_size:.2f} MB")
    print(f"{'='*60}\n")


# ============================================================================
# MAIN - For testing
# ============================================================================

def main():
    """Test data logger."""
    print("Testing DataLogger...")
    
    # Create logger
    logger = DataLogger(log_dir="self_aware/logs", format="csv", buffer_size=10)
    throttled = ThrottledLogger(logger, sample_rate_hz=10)
    
    # Simulate logging
    print("\nSimulating 50 samples at various rates...")
    for i in range(50):
        sensor_data = {
            'distance': 25.5 + i,
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
        
        throttled.log_entry(sensor_data, action_data, context_data)
        time.sleep(0.05)  # 20 Hz attempts, but throttled to 10 Hz
    
    # Get stats
    stats = throttled.get_stats()
    print(f"\n✓ Logging complete!")
    print(f"  Entries: {stats['entries_logged']}")
    print(f"  Rate: {stats['rate']:.1f} Hz")
    print(f"  File: {stats['file_path']}")
    
    # Close
    throttled.close()
    
    # Show summary
    print_log_summary()


if __name__ == '__main__':
    main()
