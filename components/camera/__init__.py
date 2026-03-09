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
    create_qr_reader,
    create_object_detector,
    create_traffic_sign_detector,
    create_image_classifier
)

__all__ = [
    'SimpleCamera',
    'VilibDetector',
    'DetectionResult',
    'create_color_tracker',
    'create_face_tracker',
    'create_qr_reader',
    'create_object_detector',
    'create_traffic_sign_detector',
    'create_image_classifier'
]
