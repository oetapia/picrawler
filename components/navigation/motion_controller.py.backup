#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smooth motion controller for gradual speed transitions.

Provides smooth acceleration and deceleration to avoid jerky movements
and improve stability on uneven terrain.
"""

from components.utils.config import SPEED_MIN, SPEED_MAX, SPEED_NORMAL


class SmoothMotionController:
    """
    Handles smooth speed transitions and movement planning.
    
    Instead of instant speed changes, this controller gradually transitions
    between speeds to provide smoother, more stable movement.
    """
    
    def __init__(self, initial_speed=SPEED_NORMAL, speed_change_rate=5):
        """
        Initialize motion controller.
        
        Args:
            initial_speed: Starting speed value
            speed_change_rate: Speed units to change per update
        """
        self.current_speed = initial_speed
        self.target_speed = initial_speed
        self.speed_change_rate = speed_change_rate
        
    def set_target_speed(self, target):
        """
        Set new target speed (will transition smoothly).
        
        Args:
            target: Desired speed value (will be clamped to valid range)
        """
        self.target_speed = max(SPEED_MIN, min(SPEED_MAX, target))
    
    def update(self):
        """
        Smoothly transition current speed towards target.
        
        Call this method regularly to update the speed. The speed will
        gradually approach the target speed based on the change rate.
        
        Returns:
            int: Current speed value after update
        """
        if self.current_speed < self.target_speed:
            self.current_speed = min(self.current_speed + self.speed_change_rate, 
                                    self.target_speed)
        elif self.current_speed > self.target_speed:
            self.current_speed = max(self.current_speed - self.speed_change_rate, 
                                    self.target_speed)
        return int(self.current_speed)
    
    def get_speed(self):
        """
        Get current speed without updating.
        
        Returns:
            int: Current speed value
        """
        return int(self.current_speed)
    
    def emergency_stop(self):
        """Immediately set speed to minimum (emergency condition)."""
        self.current_speed = SPEED_MIN
        self.target_speed = SPEED_MIN
    
    def reset(self, speed=SPEED_NORMAL):
        """
        Reset controller to a specific speed.
        
        Args:
            speed: Speed to reset to (default: SPEED_NORMAL)
        """
        self.current_speed = speed
        self.target_speed = speed
