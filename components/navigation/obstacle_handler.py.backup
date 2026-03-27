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
    avoidance actions. Supports both single and dual (front/rear) distance sensors.
    """
    
    def __init__(self, has_dual_sensors=False):
        """
        Initialize obstacle handler.
        
        Args:
            has_dual_sensors: True if using front+rear sensors (default False)
        """
        self.has_dual_sensors = has_dual_sensors
    
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
            action['steps'] = 3  # Increased from 2 for better safety
            action['secondary_action'] = random.choice(['turn left', 'turn right'])
            action['secondary_steps'] = 1  # Reduced from 2 to minimize leg extension
        
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
            action['action'] = 'backward'
            action['steps'] = 2
            action['secondary_action'] = 'turn right'
            action['secondary_steps'] = 1
        
        elif danger_type == 'right_edge':
            action['action'] = 'backward'
            action['steps'] = 2
            action['secondary_action'] = 'turn left'
            action['secondary_steps'] = 1
        
        elif danger_type.startswith('corner_'):
            # CRITICAL FIX: Back up BEFORE turning even for corners
            # This prevents more legs from extending over the edge
            action['action'] = 'backward'
            action['steps'] = 2
            corner_pos = danger_type.split('_')[1]  # fl, fr, bl, br
            if corner_pos in ['fl', 'bl']:
                action['secondary_action'] = 'turn right'
            else:
                action['secondary_action'] = 'turn left'
            action['secondary_steps'] = 1  # Minimal turn to avoid extending legs
        
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
    
    def is_backward_safe(self, rear_distance, threshold=15):
        """
        Check if it's safe to move backward using rear sensor.
        
        Args:
            rear_distance: Distance reading from rear sensor (cm)
            threshold: Minimum safe distance (default 15cm)
            
        Returns:
            bool: True if backward movement is safe
        """
        return rear_distance > threshold
    
    def decide_dual_sensor_action(self, front_distance, rear_distance, 
                                 consecutive_obstacles, roll_angle=None):
        """
        Decide obstacle avoidance action using both front and rear sensors.
        
        This method provides smarter navigation by considering obstacles
        in both directions before deciding on avoidance maneuvers.
        
        Args:
            front_distance: Front sensor distance in cm
            rear_distance: Rear sensor distance in cm
            consecutive_obstacles: Number of consecutive obstacles
            roll_angle: Optional roll angle from accelerometer (degrees)
            
        Returns:
            dict: Action plan with keys:
                - 'backward_steps': Number of backward steps (0 if unsafe)
                - 'turn_direction': 'turn left' or 'turn right'
                - 'turn_amount': Number of turn steps
                - 'emergency': Boolean indicating emergency condition
                - 'rear_blocked': Boolean indicating rear obstacle present
        """
        action = {
            'backward_steps': 2,
            'turn_direction': 'turn left',
            'turn_amount': 2,
            'emergency': False,
            'rear_blocked': False
        }
        
        # Check rear obstacle
        if rear_distance < DISTANCE_DANGER:
            action['rear_blocked'] = True
            action['backward_steps'] = 0  # Don't back up - obstacle behind!
        elif rear_distance < 25:
            action['rear_blocked'] = True
            action['backward_steps'] = 1  # Only back up a little
        
        # Emergency stop for very close front obstacles
        if front_distance < DISTANCE_DANGER:
            action['emergency'] = True
            # If rear is also blocked, we're trapped - just turn
            if action['rear_blocked']:
                action['backward_steps'] = 0
                action['turn_amount'] = 4  # Aggressive turn
            else:
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
            action['turn_amount'] = 4
        
        return action
    
    def get_best_escape_direction(self, front_distance, rear_distance):
        """
        Determine the best direction to escape when surrounded.
        
        Args:
            front_distance: Front sensor distance in cm
            rear_distance: Rear sensor distance in cm
            
        Returns:
            str: 'forward', 'backward', or 'turn' indicating best escape route
        """
        # If front is significantly more clear, go forward
        if front_distance > rear_distance + 20:
            return 'forward'
        
        # If rear is significantly more clear, go backward
        if rear_distance > front_distance + 20:
            return 'backward'
        
        # Both blocked similarly - turn to find new path
        if front_distance < DISTANCE_SAFE and rear_distance < DISTANCE_SAFE:
            return 'turn'
        
        # Default to forward if both relatively clear
        return 'forward'
