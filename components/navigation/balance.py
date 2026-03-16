#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Balance calculations and leg position management.

Provides functions to compute leg positions that compensate for
tilt and maintain robot balance on uneven terrain.
"""

from components.utils.config import (
    LEG_EXTENDED, 
    LEG_NEUTRAL, 
    LEG_RETRACTED,
    BALANCE_MAX_TILT
)


def lerp(a, b, t):
    """
    Linear interpolation between two 3D points.
    
    Args:
        a: Starting point [x, y, z]
        b: Ending point [x, y, z]
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        list: Interpolated point [x, y, z]
    """
    return [a[i] + t * (b[i] - a[i]) for i in range(3)]


def compute_balance_pose(pitch, roll):
    """
    Calculate leg positions to compensate for tilt.
    
    This function determines how each leg should be positioned to counter
    the robot's current tilt. When the robot tilts forward, front legs
    extend down while back legs retract up, and vice versa.
    
    Args:
        pitch: Pitch angle in degrees (positive = nose down)
        roll: Roll angle in degrees (positive = tilt right)
        
    Returns:
        list: Four leg positions [[x,y,z], [x,y,z], [x,y,z], [x,y,z]]
              Order: [Front-Left, Front-Right, Back-Left, Back-Right]
    
    Example:
        >>> pitch, roll = 10.0, -5.0  # Nose down, tilt left
        >>> pose = compute_balance_pose(pitch, roll)
        >>> # Front legs will extend, back legs retract
        >>> # Left legs extend more than right to counter left tilt
    """
    # Sign matrix: how each leg should move to counter tilt
    # [FL, FR, BL, BR]
    pitch_signs = [+1, +1, -1, -1]  # pitch > 0 (nose down): extend front
    roll_signs = [+1, -1, +1, -1]   # roll > 0 (tilt right): extend left
    
    # Normalize tilt to -1..+1 range
    pitch_factor = max(-1.0, min(1.0, pitch / BALANCE_MAX_TILT))
    roll_factor = max(-1.0, min(1.0, roll / BALANCE_MAX_TILT))
    
    pose = []
    for i in range(4):
        # Combine pitch and roll corrections
        factor = pitch_signs[i] * pitch_factor + roll_signs[i] * roll_factor
        factor = max(-1.0, min(1.0, factor))
        
        if factor >= 0.0:
            # Extend leg (push down)
            pose.append(lerp(LEG_NEUTRAL, LEG_EXTENDED, factor))
        else:
            # Retract leg (pull up)
            pose.append(lerp(LEG_RETRACTED, LEG_NEUTRAL, factor + 1.0))
    
    return pose


def get_neutral_pose():
    """
    Get neutral standing pose for all legs.
    
    Returns:
        list: Four legs in neutral position
    """
    return [list(LEG_NEUTRAL) for _ in range(4)]


def get_compact_pose():
    """
    Get compact pose with legs tucked in.
    
    Useful for emergency situations or when airborne.
    
    Returns:
        list: Four legs in compact position
    """
    compact = [[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]]
    return compact
