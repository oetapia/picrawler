#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obstacle avoidance strategies and maneuvers.

Provides logic for handling obstacles detected by distance sensors
and floor dangers detected by IR sensors.
"""

import random
from components.utils.config import DISTANCE_DANGER, DISTANCE_SAFE


class ObstacleHandler:
    """
    Handles obstacle detection and avoidance maneuvers.
    
    Provides methods to react to obstacles detected by distance sensors
    and floor dangers detected by IR sensors, deciding appropriate
    avoidance actions.
    """
    
    def __init__(self):
        """Initialize obstacle handler."""
        pass
    
    def decide_obstacle_action(self, distance, consecutive_obstacles, 
                              roll_angle=None):
        """
        Decide what action to take for a detected obstacle.
        
        Args:
            distance: Distance to obstacle in cm
            consecutive_obstacles: Number of consecutive obstacles encountered
            roll_angle: Optional roll angle from accelerometer (degrees)
            
        Returns:
            dict: Action plan with keys:
                - 'backward_steps': Number of backward steps
                - 'turn_direction': 'turn left' or 'turn right'
                - 'turn_amount': Number of turn steps
                - 'emergency': Boolean indicating emergency condition
        """
        action = {
            'backward_steps': 2,
            'turn_direction': 'turn left',
            'turn_amount': 2,
            'emergency': False
        }
        
        # Emergency stop for very close obstacles
        if distance < DISTANCE_DANGER:
            action['emergency'] = True
            action['backward_steps'] = 3
        
        # Use accelerometer to pick best turn direction if available
        if roll_angle is not None:
            if roll_angle > 3:
                action['turn_direction'] = 'turn left'
            elif roll_angle < -3:
                action['turn_direction'] = 'turn right'
            else:
                action['turn_direction'] = random.choice(['turn left', 'turn right'])
        else:
            action['turn_direction'] = random.choice(['turn left', 'turn right'])
        
        # More aggressive turning if stuck
        if consecutive_obstacles > 3:
            action['turn_amount'] = 3
        
        return action
    
    def decide_floor_danger_action(self, danger_type, distance_ahead=None):
        """
        Decide what action to take for floor danger.
        
        Args:
            danger_type: Type of floor danger detected
            distance_ahead: Optional distance sensor reading (cm)
            
        Returns:
            dict: Action plan with keys:
                - 'action': Primary action to take
                - 'steps': Number of steps for primary action
                - 'secondary_action': Optional follow-up action
                - 'secondary_steps': Steps for secondary action
                - 'emergency': Boolean indicating emergency condition
        """
        action = {
            'action': None,
            'steps': 0,
            'secondary_action': None,
            'secondary_steps': 0,
            'emergency': False
        }
        
        if danger_type == 'airborne':
            action['emergency'] = True
            action['action'] = 'compact'  # Special compact pose
            return action
        
        # Handle edge dangers
        if danger_type == 'front_edge':
            action['action'] = 'backward'
            action['steps'] = 2
            action['secondary_action'] = random.choice(['turn left', 'turn right'])
            action['secondary_steps'] = 2
        
        elif danger_type == 'back_edge':
            # Only move forward if distance sensor says it's safe
            if distance_ahead is not None and distance_ahead > DISTANCE_SAFE:
                action['action'] = 'forward'
                action['steps'] = 2
            else:
                # Can't go forward - turn around
                action['action'] = 'turn right'
                action['steps'] = 4
        
        elif danger_type == 'left_edge':
            action['action'] = 'turn right'
            action['steps'] = 2
        
        elif danger_type == 'right_edge':
            action['action'] = 'turn left'
            action['steps'] = 2
        
        elif danger_type.startswith('corner_'):
            # Corner dangers
            corner_pos = danger_type.split('_')[1]  # fl, fr, bl, br
            if corner_pos in ['fl', 'bl']:
                action['action'] = 'turn right'
            else:
                action['action'] = 'turn left'
            action['steps'] = 2
        
        return action
    
    def analyze_floor_danger(self, floor_sensors):
        """
        Analyze floor sensor readings and determine danger type.
        
        Args:
            floor_sensors: Dict with keys 'fl', 'fr', 'bl', 'br' (0 or 1)
            
        Returns:
            tuple: (danger_type, suggested_action)
                danger_type: String describing the danger
                suggested_action: Suggested action string or None
        """
        fl = floor_sensors.get('fl', 0)
        fr = floor_sensors.get('fr', 0)
        bl = floor_sensors.get('bl', 0)
        br = floor_sensors.get('br', 0)
        
        danger_count = fl + fr + bl + br
        
        if danger_count == 0:
            return None, None
        
        if danger_count == 4:
            return 'airborne', None
        
        # Front danger
        if fl and fr:
            return 'front_edge', 'backward'
        
        # Back danger
        if bl and br:
            return 'back_edge', 'forward'
        
        # Side dangers
        if fl and bl:
            return 'left_edge', 'turn right'
        if fr and br:
            return 'right_edge', 'turn left'
        
        # Corner dangers
        if fl:
            return 'corner_fl', 'turn right'
        if fr:
            return 'corner_fr', 'turn left'
        if bl:
            return 'corner_bl', 'turn right'
        if br:
            return 'corner_br', 'turn left'
        
        return 'unknown', None
