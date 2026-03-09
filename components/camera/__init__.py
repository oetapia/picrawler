"""
Camera components for Picrawler

Provides camera interfaces and computer vision detection capabilities.
"""

from .simple_camera import SimpleCamera
from .vilib_detector import (
    VilibDetector,
    DetectionResult,
    create_color_tracker,
    create_face_tracker,
    create_qr_reader
)

__all__ = [
    'SimpleCamera',
    'VilibDetector',
    'DetectionResult',
    'create_color_tracker',
    'create_face_tracker',
    'create_qr_reader'
]
