#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tilt-Aware ToF Distance Sensor Module

Discriminates between floor readings and actual obstacles by considering
the robot's pitch angle. When tilted forward, the front ToF sensor may
point at the floor instead of ahead, causing false obstacle detections.

This module provides geometric compensation and classification to filter
out floor readings while walking.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional


class ReadingType(Enum):
    """Classification of distance sensor readings."""
    CLEAR = "clear"           # No obstacle, safe to proceed
    OBSTACLE = "obstacle"     # Real obstacle detected
    FLOOR = "floor"           # Floor reading (false positive)
    UNCERTAIN = "uncertain"   # Cannot determine, treat with caution


@dataclass
class ClassifiedReading:
    """Result of a classified distance reading."""
    distance: float           # Raw distance in cm
    reading_type: ReadingType # Classification
    confidence: float         # 0.0 to 1.0
    pitch: float              # Pitch angle when reading was taken
    expected_floor_dist: Optional[float] = None  # Calculated floor distance
    reason: str = ""          # Human-readable explanation


# Configuration constants
class TiltAwareConfig:
    """Configuration for tilt-aware distance sensing."""
    
    # Sensor mounting geometry (adjust for your robot)
    SENSOR_HEIGHT_CM = 8.0        # Height of ToF sensor from ground when level
    SENSOR_FORWARD_OFFSET = 5.0   # How far forward the sensor is mounted
    
    # Pitch thresholds
    PITCH_FLOOR_RISK_MIN = 8.0    # deg - below this, unlikely to see floor
    PITCH_FLOOR_RISK_MAX = 35.0   # deg - above this, definitely seeing floor
    
    # Distance thresholds
    FLOOR_DISTANCE_MIN = 10.0     # cm - floor can't be closer than this
    FLOOR_DISTANCE_MAX = 60.0     # cm - floor readings typically in this range
    OBSTACLE_DISTANCE_MIN = 5.0   # cm - emergency stop distance
    CLEAR_DISTANCE = 80.0         # cm - beyond this is clear
    
    # Tolerance for floor distance matching
    FLOOR_MATCH_TOLERANCE = 15.0  # cm - how close to expected floor dist
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.6
    LOW_CONFIDENCE = 0.4


def calculate_expected_floor_distance(pitch_deg: float, 
                                       sensor_height: float = TiltAwareConfig.SENSOR_HEIGHT_CM) -> float:
    """
    Calculate the expected distance to floor given pitch angle.
    
    When robot tilts forward, the ToF sensor points downward.
    Using trigonometry: floor_distance = height / sin(pitch)
    
    Args:
        pitch_deg: Pitch angle in degrees (positive = tilted forward)
        sensor_height: Height of sensor from ground in cm
        
    Returns:
        Expected distance to floor in cm, or 999 if angle too small
    """
    if pitch_deg < 3.0:
        return 999.0  # Nearly level, sensor looking ahead not at floor
    
    # Convert to radians and calculate
    pitch_rad = math.radians(pitch_deg)
    
    # Distance = height / sin(pitch)
    # But we need to account for sensor looking at angle from horizontal
    try:
        floor_dist = sensor_height / math.sin(pitch_rad)
        return max(0, floor_dist)
    except (ValueError, ZeroDivisionError):
        return 999.0


def classify_distance_reading(distance: float, 
                               pitch: float, 
                               roll: float = 0.0,
                               config: TiltAwareConfig = None) -> ClassifiedReading:
    """
    Classify a distance reading as obstacle, floor, or clear.
    
    Uses pitch angle to determine if the ToF sensor is likely seeing
    the floor instead of an actual obstacle.
    
    Args:
        distance: Raw distance reading in cm
        pitch: Current pitch angle in degrees (+ = forward tilt)
        roll: Current roll angle in degrees (for side tilt compensation)
        config: Optional configuration override
        
    Returns:
        ClassifiedReading with type, confidence, and explanation
    """
    if config is None:
        config = TiltAwareConfig()
    
    # Calculate expected floor distance at current pitch
    expected_floor = calculate_expected_floor_distance(pitch, config.SENSOR_HEIGHT_CM)
    
    # Case 1: Very far reading - definitely clear
    if distance > config.CLEAR_DISTANCE:
        return ClassifiedReading(
            distance=distance,
            reading_type=ReadingType.CLEAR,
            confidence=0.95,
            pitch=pitch,
            expected_floor_dist=expected_floor,
            reason="Distance beyond obstacle range"
        )
    
    # Case 2: Emergency close - always treat as obstacle
    if distance < config.OBSTACLE_DISTANCE_MIN:
        return ClassifiedReading(
            distance=distance,
            reading_type=ReadingType.OBSTACLE,
            confidence=0.99,
            pitch=pitch,
            expected_floor_dist=expected_floor,
            reason="Emergency close distance"
        )
    
    # Case 3: Robot is level (not tilted forward) - trust the reading
    if pitch < config.PITCH_FLOOR_RISK_MIN:
        if distance < 30:  # Warning distance
            return ClassifiedReading(
                distance=distance,
                reading_type=ReadingType.OBSTACLE,
                confidence=0.9,
                pitch=pitch,
                expected_floor_dist=expected_floor,
                reason="Short distance while level - real obstacle"
            )
        else:
            return ClassifiedReading(
                distance=distance,
                reading_type=ReadingType.CLEAR,
                confidence=0.85,
                pitch=pitch,
                expected_floor_dist=expected_floor,
                reason="Moderate distance while level"
            )
    
    # Case 4: Robot is tilted forward - check if reading matches floor
    if pitch >= config.PITCH_FLOOR_RISK_MIN:
        
        # Check if distance matches expected floor distance
        floor_diff = abs(distance - expected_floor)
        
        if floor_diff < config.FLOOR_MATCH_TOLERANCE:
            # Distance matches expected floor!
            confidence = config.HIGH_CONFIDENCE
            if floor_diff < 5:
                confidence = 0.95  # Very close match
            
            return ClassifiedReading(
                distance=distance,
                reading_type=ReadingType.FLOOR,
                confidence=confidence,
                pitch=pitch,
                expected_floor_dist=expected_floor,
                reason=f"Distance {distance:.0f}cm matches floor estimate {expected_floor:.0f}cm (pitch={pitch:.1f} deg)"
            )
        
        # Distance doesn't match floor - could be obstacle or uncertain
        if distance < expected_floor * 0.5:
            # Much closer than floor - likely real obstacle
            return ClassifiedReading(
                distance=distance,
                reading_type=ReadingType.OBSTACLE,
                confidence=config.MEDIUM_CONFIDENCE,
                pitch=pitch,
                expected_floor_dist=expected_floor,
                reason=f"Distance {distance:.0f}cm << floor {expected_floor:.0f}cm - likely obstacle"
            )
        
        # Uncertain - could be obstacle at floor level
        return ClassifiedReading(
            distance=distance,
            reading_type=ReadingType.UNCERTAIN,
            confidence=config.LOW_CONFIDENCE,
            pitch=pitch,
            expected_floor_dist=expected_floor,
            reason=f"Tilted reading doesn't clearly match floor or obstacle"
        )
    
    # Default: uncertain
    return ClassifiedReading(
        distance=distance,
        reading_type=ReadingType.UNCERTAIN,
        confidence=0.5,
        pitch=pitch,
        expected_floor_dist=expected_floor,
        reason="Could not classify"
    )


def should_trigger_obstacle_avoidance(classified: ClassifiedReading, 
                                       warning_distance: float = 30.0) -> bool:
    """
    Determine if obstacle avoidance should be triggered.
    
    Args:
        classified: ClassifiedReading result
        warning_distance: Distance threshold for warnings
        
    Returns:
        True if obstacle avoidance should be triggered
    """
    # Always avoid confirmed obstacles
    if classified.reading_type == ReadingType.OBSTACLE:
        return classified.distance < warning_distance
    
    # Never avoid clear readings
    if classified.reading_type == ReadingType.CLEAR:
        return False
    
    # Skip floor readings
    if classified.reading_type == ReadingType.FLOOR:
        return False
    
    # For uncertain readings, be cautious if close
    if classified.reading_type == ReadingType.UNCERTAIN:
        # More conservative threshold for uncertain readings
        return classified.distance < warning_distance * 0.7
    
    return False


def get_display_text(classified: ClassifiedReading) -> Tuple[str, str]:
    """
    Get display-friendly text for OLED.
    
    Args:
        classified: ClassifiedReading result
        
    Returns:
        Tuple of (type_text, detail_text)
    """
    type_map = {
        ReadingType.CLEAR: "CLEAR",
        ReadingType.OBSTACLE: "OBSTACLE",
        ReadingType.FLOOR: "FLOOR(skip)",
        ReadingType.UNCERTAIN: "CHECKING",
    }
    
    type_text = type_map.get(classified.reading_type, "UNKNOWN")
    
    if classified.reading_type == ReadingType.FLOOR:
        detail_text = f"{classified.distance:.0f}cm @{classified.pitch:.0f}deg"
    elif classified.reading_type == ReadingType.OBSTACLE:
        detail_text = f"{classified.distance:.0f}cm AVOID!"
    elif classified.reading_type == ReadingType.CLEAR:
        detail_text = f">{classified.distance:.0f}cm OK"
    else:
        detail_text = f"{classified.distance:.0f}cm ?"
    
    return type_text, detail_text


# ============================================================================
# TESTING
# ============================================================================

def test_classification():
    """Test the classification logic with various scenarios."""
    print("Testing Tilt-Aware ToF Classification")
    print("=" * 50)
    
    test_cases = [
        # (distance, pitch, expected_type, description)
        (100, 0, ReadingType.CLEAR, "Far reading, level"),
        (25, 0, ReadingType.OBSTACLE, "Close reading, level - obstacle"),
        (3, 0, ReadingType.OBSTACLE, "Emergency close"),
        (25, 15, ReadingType.FLOOR, "Tilted forward, floor distance"),
        (30, 20, ReadingType.FLOOR, "More tilt, matches floor"),
        (15, 15, ReadingType.OBSTACLE, "Tilted but much closer than floor"),
        (50, 5, ReadingType.CLEAR, "Slight tilt, moderate distance"),
    ]
    
    for distance, pitch, expected, desc in test_cases:
        result = classify_distance_reading(distance, pitch)
        status = "[EMOJI]" if result.reading_type == expected else "[EMOJI]"
        print(f"{status} {desc}")
        print(f"  Input: {distance}cm, pitch={pitch} deg")
        print(f"  Got: {result.reading_type.value} ({result.confidence:.0%})")
        print(f"  Reason: {result.reason}")
        print()


if __name__ == "__main__":
    test_classification()
