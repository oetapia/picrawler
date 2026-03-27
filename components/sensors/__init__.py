"""
Sensors module for PiCrawler.

Provides access to all sensor components including:
- Accelerometer (MPU6050)
- Distance sensors (ToF VL53L0X, ultrasonic)
- IR floor sensors
- Tilt-aware ToF classification
- Sensor fusion
"""

from . import accelerometer
from . import ir_distance

# Tilt-aware ToF classification
from .tilt_aware_tof import (
    ReadingType, 
    ClassifiedReading, 
    TiltAwareConfig,
    classify_distance_reading,
    classify_rear_distance_reading,
    calculate_expected_floor_distance,
    should_trigger_obstacle_avoidance,
    get_display_text
)

# Sensor fusion hub
from .sensor_fusion import SensorHub

__all__ = [
    'accelerometer',
    'ir_distance',
    'SensorHub',
    'ReadingType',
    'ClassifiedReading',
    'TiltAwareConfig',
    'classify_distance_reading',
    'classify_rear_distance_reading',
    'calculate_expected_floor_distance',
    'should_trigger_obstacle_avoidance',
    'get_display_text',
]
