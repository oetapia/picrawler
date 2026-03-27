#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot navigation state definitions.

Defines the various states a robot can be in during autonomous navigation.
"""

from enum import Enum


class RobotState(Enum):
    """
    Enumeration of possible robot navigation states.
    
    States:
        EXPLORING: Normal forward exploration
        AVOIDING_OBSTACLE: Actively avoiding a detected obstacle
        AVOIDING_FLOOR_DANGER: Avoiding floor edge/drop detected by IR sensors
        TILT_CORRECTION: Correcting dangerous tilt angle
        STUCK: Detected stuck condition, executing recovery
        EMERGENCY: Emergency stop condition
    """
    EXPLORING = "exploring"
    AVOIDING_OBSTACLE = "avoiding_obstacle"
    AVOIDING_FLOOR_DANGER = "avoiding_floor_danger"
    TILT_CORRECTION = "tilt_correction"
    STUCK = "stuck"
    EMERGENCY = "emergency"
