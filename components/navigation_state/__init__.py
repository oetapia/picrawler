"""
Navigation state management for PiCrawler.

Provides state definitions and recovery strategies used across
different navigation modes.
"""

from .states import RobotState
from .recovery import StuckDetector, ESCAPE_PATTERNS

__all__ = ['RobotState', 'StuckDetector', 'ESCAPE_PATTERNS']
