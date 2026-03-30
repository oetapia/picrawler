"""
Sensors module for PiCrawler.

Provides access to all sensor components including:
- Accelerometer (MPU6050)
- Distance sensors (ToF VL53L0X, ultrasonic)
- IR floor sensors
- Tilt-aware ToF classification
- Sensor fusion

Note: ir_distance is NOT auto-imported because it claims GPIO pins immediately.
Import it explicitly only when needed:
    from components.sensors import ir_distance
"""

from . import accelerometer
# from . import ir_distance  # Removed: causes GPIO conflict if imported when not needed

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
