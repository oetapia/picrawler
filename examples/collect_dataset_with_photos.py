#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Collection Example with Photos

Demonstrates how to collect ML training data during robot navigation.
Uses DataLoggerWithPhotos to capture:
- Sensor readings (10 Hz)
- Photos (2 Hz)  
- Robot actions
- Auto-generated labels

Run this during normal navigation to build a custom dataset.
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from self_aware.data_logger_with_photos import DataLoggerWithPhotos
from components.sensors.sensor_fusion import SensorHub

try:
    from picrawler import Picrawler
    PICRAWLER_AVAILABLE = True
except:
    PICRAWLER_AVAILABLE = False
    print("⚠️  Picrawler not available - running in simulation mode")


def collect_dataset_while_navigating(duration_minutes=5, 
                                     photo_rate_hz=2.0,
                                     photo_resolution=(320, 240)):
    """
    Collect dataset while robot navigates autonomously.
    
    Args:
        duration_minutes: How long to collect data
        photo_rate_hz: Photos per second (1-5 recommended)
        photo_resolution: Photo size (320x240 recommended for training)
    """
    print("\n" + "="*60)
    print("  DATASET COLLECTION WITH PHOTOS")
    print("="*60)
    print(f"Duration: {duration_minutes} minutes")
    print(f"Photo rate: {photo_rate_hz} Hz")
    print(f"Resolution: {photo_resolution[0]}x{photo_resolution[1]}")
    print("="*60 + "\n")
    
    # Initialize components
    sensor_hub = SensorHub()
    
    if PICRAWLER_AVAILABLE:
        robot = Picrawler()
        print("✓ Robot initialized")
    else:
        robot = None
        print("⚠️  Running without robot (simulation)")
    
    # Initialize logger with photos
    logger = DataLoggerWithPhotos(
        log_dir="self_aware/logs",
        capture_photos=True,
        photo_rate_hz=photo_rate_hz,
        photo_resolution=photo_resolution,
        buffer_size=100
    )
    
    # Start photo capture
    print("Starting photo capture...")
    logger.start_photo_capture()
    time.sleep(1)
    
    print("\n✓ Dataset collection started!")
    print("  Robot will navigate and collect data automatically.")
    print("  Press Ctrl+C to stop early.\n")
    
    # Calculate end time
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    # Navigation state
    state = "exploring"
    consecutive_obstacles = 0
    consecutive_floor_dangers = 0
    
    try:
        iteration = 0
        while time.time() < end_time:
            iteration += 1
            
            # Read sensors
            front_distance = sensor_hub.get_front_distance()
            rear_distance = sensor_hub.get_rear_distance()
            pitch, roll = sensor_hub.get_tilt()
            floor_sensors = sensor_hub.get_floor_sensors()
            
            # Prepare sensor data
            sensor_data = {
                'front_distance': front_distance,
                'rear_distance': rear_distance,
                'distance': front_distance,  # For backward compatibility
                'pitch': pitch,
                'roll': roll,
                'floor_fl': floor_sensors['fl'],
                'floor_fr': floor_sensors['fr'],
                'floor_bl': floor_sensors['bl'],
                'floor_br': floor_sensors['br'],
            }
            
            # Simple navigation logic
            action = 'forward'
            steps = 1
            
            # Check for obstacles
            if front_distance < 20:
                action = 'turn_left'
                steps = 2
                consecutive_obstacles += 1
                state = "avoiding_obstacle"
            elif sum(floor_sensors.values()) > 0:
                action = 'backward'
                steps = 2
                consecutive_floor_dangers += 1
                state = "avoiding_floor_danger"
            else:
                consecutive_obstacles = 0
                consecutive_floor_dangers = 0
                state = "exploring"
            
            # Prepare action data
            action_data = {
                'action': action,
                'steps': steps,
                'speed': 70
            }
            
            # Prepare context
            context_data = {
                'state': state,
                'previous_state': state,
                'current_speed': 70,
                'consecutive_obstacles': consecutive_obstacles,
                'consecutive_floor_dangers': consecutive_floor_dangers,
                'stuck_counter': 0
            }
            
            # Log with photo capture
            logger.log_entry_with_photo(sensor_data, action_data, context_data)
            
            # Execute action (if robot available)
            if robot:
                if action == 'forward':
                    robot.do_action('forward', step_num=steps, speed=70)
                elif action == 'backward':
                    robot.do_action('backward', step_num=steps, speed=70)
                elif action == 'turn_left':
                    robot.do_action('turn left', step_num=steps, speed=50)
            
            # Progress update every 100 iterations
            if iteration % 100 == 0:
                elapsed = time.time() - start_time
                remaining = (end_time - time.time()) / 60
                stats = logger.get_stats()
                print(f"[{elapsed:.0f}s] Entries: {stats['entries_logged']}, "
                      f"Remaining: {remaining:.1f} min")
            
            # Wait for next iteration (10 Hz main loop)
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
    
    finally:
        # Cleanup
        print("\nStopping dataset collection...")
        logger.close()
        sensor_hub.close()
        
        print("\n" + "="*60)
        print("  DATASET COLLECTION COMPLETE")
        print("="*60)
        print("\nNext steps:")
        print("1. Review collected data in self_aware/logs/")
        print("2. Use dataset_utils.py to export for training")
        print("3. Train a custom classifier on your data")
        print("="*60 + "\n")


def quick_test(duration_seconds=30):
    """Quick test - 30 seconds of data collection."""
    print("\n🧪 QUICK TEST MODE (30 seconds)")
    collect_dataset_while_navigating(
        duration_minutes=duration_seconds/60,
        photo_rate_hz=2.0,
        photo_resolution=(320, 240)
    )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Collect ML dataset with synchronized photos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick 30 second test
  python examples/collect_dataset_with_photos.py --test
  
  # Collect for 5 minutes (default)
  python examples/collect_dataset_with_photos.py
  
  # Collect for 30 minutes with higher photo rate
  python examples/collect_dataset_with_photos.py -d 30 -r 3.0
  
  # Lower resolution for faster capture
  python examples/collect_dataset_with_photos.py -d 10 --resolution 160 120

The robot will navigate autonomously while collecting:
- Sensor readings (10 Hz) → sensor_data.csv
- Photos (2 Hz default) → photos/*.jpg
- Auto-generated labels → photo_manifest.csv
        """
    )
    
    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=5.0,
        help='Collection duration in minutes (default: 5)'
    )
    parser.add_argument(
        '-r', '--photo-rate',
        type=float,
        default=2.0,
        help='Photos per second (default: 2.0)'
    )
    parser.add_argument(
        '--resolution',
        type=int,
        nargs=2,
        default=[320, 240],
        metavar=('WIDTH', 'HEIGHT'),
        help='Photo resolution (default: 320 240)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Quick 30 second test'
    )
    
    args = parser.parse_args()
    
    if args.test:
        quick_test()
    else:
        collect_dataset_while_navigating(
            duration_minutes=args.duration,
            photo_rate_hz=args.photo_rate,
            photo_resolution=tuple(args.resolution)
        )


if __name__ == '__main__':
    main()
