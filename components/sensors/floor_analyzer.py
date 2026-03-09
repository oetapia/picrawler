#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Floor danger analysis for IR sensors.

Analyzes IR floor sensor readings to detect edges, drops, and other
floor-related dangers.
"""


def analyze_floor_danger(floor_sensors):
    """
    Analyze floor sensor readings and determine danger type.
    
    This function interprets the pattern of IR sensor activations to
    determine what type of floor danger is present and suggest an
    appropriate response action.
    
    Args:
        floor_sensors: Dict with keys 'fl', 'fr', 'bl', 'br' 
                      Values are 0 (floor detected) or 1 (no floor/danger)
        
    Returns:
        tuple: (danger_type, suggested_action)
            danger_type: String describing the danger or None if safe
            suggested_action: Suggested action string or None
    
    Danger Types:
        - 'airborne': All sensors detect no floor
        - 'front_edge': Both front sensors detect edge
        - 'back_edge': Both back sensors detect edge
        - 'left_edge': Both left sensors detect edge
        - 'right_edge': Both right sensors detect edge
        - 'corner_XX': Single corner sensor detects edge (XX = fl/fr/bl/br)
        - 'unknown': Pattern doesn't match known dangers
    
    Example:
        >>> sensors = {'fl': 1, 'fr': 1, 'bl': 0, 'br': 0}
        >>> analyze_floor_danger(sensors)
        ('front_edge', 'backward')
    """
    fl = floor_sensors.get('fl', 0)
    fr = floor_sensors.get('fr', 0)
    bl = floor_sensors.get('bl', 0)
    br = floor_sensors.get('br', 0)
    
    danger_count = fl + fr + bl + br
    
    # No danger detected
    if danger_count == 0:
        return None, None
    
    # All sensors triggered - robot is airborne or all legs off ground
    if danger_count == 4:
        return 'airborne', None
    
    # Front edge - both front sensors
    if fl and fr:
        return 'front_edge', 'backward'
    
    # Back edge - both back sensors
    if bl and br:
        return 'back_edge', 'forward'
    
    # Left edge - both left sensors
    if fl and bl:
        return 'left_edge', 'turn right'
    
    # Right edge - both right sensors
    if fr and br:
        return 'right_edge', 'turn left'
    
    # Individual corner dangers
    if fl:
        return 'corner_fl', 'turn right'
    if fr:
        return 'corner_fr', 'turn left'
    if bl:
        return 'corner_bl', 'turn right'
    if br:
        return 'corner_br', 'turn left'
    
    # Unknown pattern
    return 'unknown', None


def is_floor_safe(floor_sensors):
    """
    Quick check if floor is safe.
    
    Args:
        floor_sensors: Dict with sensor readings
        
    Returns:
        bool: True if all sensors detect floor (safe)
    """
    return sum(floor_sensors.values()) == 0


def get_danger_severity(danger_type):
    """
    Get severity level of a floor danger.
    
    Args:
        danger_type: String danger type
        
    Returns:
        str: 'critical', 'high', 'medium', or 'low'
    """
    if danger_type is None:
        return 'low'
    
    if danger_type == 'airborne':
        return 'critical'
    
    if danger_type in ['front_edge', 'back_edge']:
        return 'high'
    
    if danger_type in ['left_edge', 'right_edge']:
        return 'high'
    
    if danger_type.startswith('corner_'):
        return 'medium'
    
    return 'low'
