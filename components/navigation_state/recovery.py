#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stuck detection and recovery strategies.

Provides algorithms to detect when the robot is stuck and
escape patterns to recover from stuck situations.
"""

import time
import random


# Escape patterns: list of (action, steps) tuples
# These patterns are executed when the robot detects it's stuck
ESCAPE_PATTERNS = [
    [('backward', 2), ('turn left', 3), ('forward', 1)],
    [('backward', 2), ('turn right', 3), ('forward', 1)],
    [('turn left', 4), ('forward', 2)],
    [('turn right', 4), ('forward', 2)],
    [('backward', 3), ('turn left', 2), ('turn right', 2)],
]


class StuckDetector:
    """
    Detects when the robot appears to be stuck and manages recovery.
    
    Tracks various indicators of being stuck:
    - Consecutive obstacle encounters
    - Consecutive floor danger detections
    - Time since last successful movement
    """
    
    def __init__(self, 
                 max_consecutive_obstacles=5,
                 max_consecutive_floor_dangers=4,
                 max_time_without_progress=15):
        """
        Initialize stuck detector.
        
        Args:
            max_consecutive_obstacles: Threshold for consecutive obstacles
            max_consecutive_floor_dangers: Threshold for consecutive floor dangers
            max_time_without_progress: Max seconds without successful movement
        """
        self.max_consecutive_obstacles = max_consecutive_obstacles
        self.max_consecutive_floor_dangers = max_consecutive_floor_dangers
        self.max_time_without_progress = max_time_without_progress
        
        # Tracking counters
        self.consecutive_obstacles = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter = 0
        self.last_successful_move = time.time()
    
    def is_stuck(self):
        """
        Check if robot appears to be stuck.
        
        Returns:
            bool: True if stuck condition detected
        """
        time_since_move = time.time() - self.last_successful_move
        
        return (self.consecutive_obstacles > self.max_consecutive_obstacles or
                self.consecutive_floor_dangers > self.max_consecutive_floor_dangers or
                time_since_move > self.max_time_without_progress)
    
    def record_obstacle(self):
        """Record an obstacle encounter."""
        self.consecutive_obstacles += 1
    
    def record_floor_danger(self):
        """Record a floor danger detection."""
        self.consecutive_floor_dangers += 1
    
    def record_successful_move(self):
        """Record a successful movement."""
        self.last_successful_move = time.time()
        
        # Decay counters on successful movement
        if self.consecutive_obstacles > 0:
            self.consecutive_obstacles -= 1
        if self.consecutive_floor_dangers > 0:
            self.consecutive_floor_dangers -= 1
    
    def increment_stuck_counter(self):
        """Increment the stuck counter."""
        self.stuck_counter += 1
    
    def should_execute_escape(self):
        """
        Check if escape pattern should be executed.
        
        Returns:
            bool: True if escape should be executed
        """
        return self.stuck_counter >= 2
    
    def get_escape_pattern(self):
        """
        Get a random escape pattern.
        
        Returns:
            list: List of (action, steps) tuples
        """
        return random.choice(ESCAPE_PATTERNS)
    
    def reset(self):
        """Reset all tracking counters."""
        self.consecutive_obstacles = 0
        self.consecutive_floor_dangers = 0
        self.stuck_counter = 0
        self.last_successful_move = time.time()
    
    def get_status(self):
        """
        Get current stuck detection status.
        
        Returns:
            dict: Status information
        """
        return {
            'consecutive_obstacles': self.consecutive_obstacles,
            'consecutive_floor_dangers': self.consecutive_floor_dangers,
            'stuck_counter': self.stuck_counter,
            'time_since_move': time.time() - self.last_successful_move,
            'is_stuck': self.is_stuck()
        }
