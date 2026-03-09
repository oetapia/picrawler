"""
Vilib Detection Module

This module provides a clean interface for vilib-based computer vision detection,
including color detection, face detection, and QR code detection.

Based on examples: treasure_hunt.py and bull_fight.py
"""

from vilib import Vilib
from typing import Dict, Optional, Tuple, List, Callable
import threading
import time


class DetectionResult:
    """Data class for detection results"""
    
    def __init__(self, detected: bool = False, count: int = 0,
                 x: int = 0, y: int = 0, width: int = 0, height: int = 0,
                 data: Optional[str] = None):
        self.detected = detected
        self.count = count
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.data = data
    
    @property
    def coordinate(self) -> Tuple[int, int]:
        """Get (x, y) coordinate tuple"""
        return (self.x, self.y)
    
    @property
    def size(self) -> Tuple[int, int]:
        """Get (width, height) size tuple"""
        return (self.width, self.height)
    
    @property
    def center_x(self) -> int:
        """Get center X coordinate"""
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        """Get center Y coordinate"""
        return self.y + self.height // 2
    
    def __repr__(self):
        if self.detected:
            return f"DetectionResult(count={self.count}, pos=({self.x},{self.y}), size=({self.width}x{self.height}))"
        return "DetectionResult(detected=False)"


class VilibDetector:
    """
    Main detector class that wraps vilib functionality.
    
    Features:
    - Color detection (red, orange, yellow, green, blue, purple)
    - Face/human detection
    - QR code detection
    - Photo capture
    - Video recording
    - Real-time detection callbacks
    
    Example usage:
        detector = VilibDetector()
        detector.start_camera()
        detector.enable_color_detection('red')
        
        while True:
            result = detector.get_color_detection()
            if result.detected:
                print(f"Red object at {result.coordinate}")
            time.sleep(0.1)
    """
    
    # Available colors for detection
    AVAILABLE_COLORS = ["red", "orange", "yellow", "green", "blue", "purple"]
    
    def __init__(self, vflip: bool = False, hflip: bool = False):
        """
        Initialize the detector.
        
        Args:
            vflip: Vertical flip of camera image
            hflip: Horizontal flip of camera image
        """
        self.vflip = vflip
        self.hflip = hflip
        self.is_camera_running = False
        self.is_display_running = False
        
        # Detection states
        self._color_detection_enabled = False
        self._face_detection_enabled = False
        self._qr_detection_enabled = False
        self._object_detection_enabled = False
        self._traffic_sign_detection_enabled = False
        self._image_classification_enabled = False
        self._current_color = None
        
        # Callback system for real-time notifications
        self._callbacks: Dict[str, List[Callable]] = {
            'color': [],
            'face': [],
            'qr': [],
            'object': [],
            'traffic_sign': [],
            'image_classify': []
        }
        
        # Monitoring thread
        self._monitor_thread = None
        self._monitor_running = False
    
    # ============ Camera Control ============
    
    def start_camera(self, vflip: Optional[bool] = None, hflip: Optional[bool] = None):
        """
        Start the camera.
        
        Args:
            vflip: Override vertical flip setting
            hflip: Override horizontal flip setting
        """
        if self.is_camera_running:
            print("Camera already running")
            return
        
        vflip = vflip if vflip is not None else self.vflip
        hflip = hflip if hflip is not None else self.hflip
        
        Vilib.camera_start(vflip=vflip, hflip=hflip)
        self.is_camera_running = True
        time.sleep(0.2)  # Give camera time to initialize
    
    def stop_camera(self):
        """Stop the camera and all detections."""
        if not self.is_camera_running:
            return
        
        self.stop_monitoring()
        self.disable_all_detections()
        Vilib.camera_close()
        self.is_camera_running = False
    
    def start_display(self, local: bool = False, web: bool = True):
        """
        Start the video display.
        
        Args:
            local: Show on local display
            web: Enable web streaming
        """
        Vilib.display(local=local, web=web)
        self.is_display_running = True
        time.sleep(0.2)
    
    # ============ Color Detection ============
    
    def enable_color_detection(self, color: str):
        """
        Enable color detection for a specific color.
        
        Args:
            color: Color name ('red', 'orange', 'yellow', 'green', 'blue', 'purple')
        
        Raises:
            ValueError: If color is not supported
        """
        if color not in self.AVAILABLE_COLORS:
            raise ValueError(f"Color must be one of {self.AVAILABLE_COLORS}")
        
        Vilib.color_detect(color)
        self._color_detection_enabled = True
        self._current_color = color
    
    def disable_color_detection(self):
        """Disable color detection."""
        Vilib.color_detect('close')
        self._color_detection_enabled = False
        self._current_color = None
    
    def get_color_detection(self) -> DetectionResult:
        """
        Get current color detection result.
        
        Returns:
            DetectionResult with color detection data
        """
        params = Vilib.detect_obj_parameter
        count = params.get('color_n', 0)
        
        if count > 0:
            return DetectionResult(
                detected=True,
                count=count,
                x=params.get('color_x', 0),
                y=params.get('color_y', 0),
                width=params.get('color_w', 0),
                height=params.get('color_h', 0)
            )
        return DetectionResult(detected=False)
    
    def is_color_centered(self, result: DetectionResult, 
                         center_min: int = 100, center_max: int = 220) -> bool:
        """
        Check if detected color is centered in frame.
        
        Args:
            result: DetectionResult from get_color_detection()
            center_min: Minimum X coordinate for "centered"
            center_max: Maximum X coordinate for "centered"
        
        Returns:
            True if color is centered
        """
        if not result.detected:
            return False
        return center_min <= result.x <= center_max
    
    def get_color_direction(self, result: DetectionResult,
                           left_threshold: int = 100,
                           right_threshold: int = 220) -> str:
        """
        Get direction to turn based on color position.
        
        Args:
            result: DetectionResult from get_color_detection()
            left_threshold: X coordinate below which to turn left
            right_threshold: X coordinate above which to turn right
        
        Returns:
            'left', 'right', 'center', or 'none'
        """
        if not result.detected:
            return 'none'
        
        if result.x < left_threshold:
            return 'left'
        elif result.x > right_threshold:
            return 'right'
        else:
            return 'center'
    
    # ============ Face Detection ============
    
    def enable_face_detection(self):
        """Enable face/human detection."""
        Vilib.face_detect_switch(True)
        self._face_detection_enabled = True
    
    def disable_face_detection(self):
        """Disable face/human detection."""
        Vilib.face_detect_switch(False)
        self._face_detection_enabled = False
    
    def get_face_detection(self) -> DetectionResult:
        """
        Get current face detection result.
        
        Returns:
            DetectionResult with face detection data
        """
        params = Vilib.detect_obj_parameter
        count = params.get('human_n', 0)
        
        if count > 0:
            return DetectionResult(
                detected=True,
                count=count,
                x=params.get('human_x', 0),
                y=params.get('human_y', 0),
                width=params.get('human_w', 0),
                height=params.get('human_h', 0)
            )
        return DetectionResult(detected=False)
    
    # ============ QR Code Detection ============
    
    def enable_qr_detection(self):
        """Enable QR code detection."""
        Vilib.qrcode_detect_switch(True)
        self._qr_detection_enabled = True
    
    def disable_qr_detection(self):
        """Disable QR code detection."""
        Vilib.qrcode_detect_switch(False)
        self._qr_detection_enabled = False
    
    def get_qr_detection(self) -> DetectionResult:
        """
        Get current QR code detection result.
        
        Returns:
            DetectionResult with QR code data in the 'data' field
        """
        params = Vilib.detect_obj_parameter
        qr_data = params.get('qr_data', 'None')
        
        if qr_data and qr_data != 'None':
            return DetectionResult(
                detected=True,
                count=1,
                data=qr_data
            )
        return DetectionResult(detected=False)
    
    # ============ Object Detection ============
    
    def enable_object_detection(self):
        """
        Enable object detection (COCO dataset objects).
        Detects common objects like person, car, dog, cat, etc.
        """
        Vilib.object_detect_switch(True)
        self._object_detection_enabled = True
    
    def disable_object_detection(self):
        """Disable object detection."""
        Vilib.object_detect_switch(False)
        self._object_detection_enabled = False
    
    def get_object_detection(self) -> DetectionResult:
        """
        Get current object detection result.
        
        Returns:
            DetectionResult with detected object data
        """
        params = Vilib.detect_obj_parameter
        count = params.get('obj_n', 0)
        
        if count > 0:
            return DetectionResult(
                detected=True,
                count=count,
                x=params.get('obj_x', 0),
                y=params.get('obj_y', 0),
                width=params.get('obj_w', 0),
                height=params.get('obj_h', 0),
                data=params.get('obj_t', 'unknown')  # object type/label
            )
        return DetectionResult(detected=False)
    
    # ============ Traffic Sign Detection ============
    
    def enable_traffic_sign_detection(self):
        """Enable traffic sign detection."""
        Vilib.traffic_sign_detect_switch(True)
        self._traffic_sign_detection_enabled = True
    
    def disable_traffic_sign_detection(self):
        """Disable traffic sign detection."""
        Vilib.traffic_sign_detect_switch(False)
        self._traffic_sign_detection_enabled = False
    
    def get_traffic_sign_detection(self) -> DetectionResult:
        """
        Get current traffic sign detection result.
        
        Returns:
            DetectionResult with traffic sign data
        """
        params = Vilib.detect_obj_parameter
        count = params.get('ts_n', 0)
        
        if count > 0:
            return DetectionResult(
                detected=True,
                count=count,
                x=params.get('ts_x', 0),
                y=params.get('ts_y', 0),
                width=params.get('ts_w', 0),
                height=params.get('ts_h', 0),
                data=params.get('ts_t', 'unknown')  # sign type
            )
        return DetectionResult(detected=False)
    
    # ============ Image Classification ============
    
    def enable_image_classification(self):
        """Enable image classification (ImageNet)."""
        Vilib.image_classify_switch(True)
        self._image_classification_enabled = True
    
    def disable_image_classification(self):
        """Disable image classification."""
        Vilib.image_classify_switch(False)
        self._image_classification_enabled = False
    
    def get_image_classification(self) -> DetectionResult:
        """
        Get current image classification result.
        
        Returns:
            DetectionResult with classification data in 'data' field
        """
        params = Vilib.detect_obj_parameter
        classification = params.get('classify_t', 'None')
        
        if classification and classification != 'None':
            return DetectionResult(
                detected=True,
                count=1,
                data=classification
            )
        return DetectionResult(detected=False)
    
    # ============ Photo & Video ============
    
    def take_photo(self, name: str, path: str = "./") -> bool:
        """
        Capture a photo.
        
        Args:
            name: Photo name (without extension)
            path: Directory path to save photo
        
        Returns:
            True if successful
        """
        return Vilib.take_photo(name, path)
    
    def start_video_recording(self, name: str, path: str = "./"):
        """
        Start video recording.
        
        Args:
            name: Video name (without extension)
            path: Directory path to save video
        """
        Vilib.rec_video_set["name"] = name
        Vilib.rec_video_set["path"] = path
        Vilib.rec_video_run()
        Vilib.rec_video_start()
    
    def pause_video_recording(self):
        """Pause video recording."""
        Vilib.rec_video_pause()
    
    def resume_video_recording(self):
        """Resume video recording."""
        Vilib.rec_video_start()
    
    def stop_video_recording(self):
        """Stop video recording."""
        Vilib.rec_video_stop()
    
    # ============ Callbacks ============
    
    def add_callback(self, detection_type: str, callback: Callable[[DetectionResult], None]):
        """
        Add a callback for detection events.
        
        Args:
            detection_type: 'color', 'face', or 'qr'
            callback: Function to call with DetectionResult when detected
        """
        if detection_type in self._callbacks:
            self._callbacks[detection_type].append(callback)
    
    def remove_callback(self, detection_type: str, callback: Callable):
        """Remove a callback."""
        if detection_type in self._callbacks and callback in self._callbacks[detection_type]:
            self._callbacks[detection_type].remove(callback)
    
    def start_monitoring(self, interval: float = 0.05):
        """
        Start background monitoring thread that triggers callbacks.
        
        Args:
            interval: Polling interval in seconds
        """
        if self._monitor_running:
            return
        
        self._monitor_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring thread."""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
    
    def _monitor_loop(self, interval: float):
        """Internal monitoring loop."""
        last_qr_data = None
        last_classify_data = None
        
        while self._monitor_running:
            try:
                # Check color detection
                if self._color_detection_enabled and self._callbacks['color']:
                    result = self.get_color_detection()
                    if result.detected:
                        for callback in self._callbacks['color']:
                            callback(result)
                
                # Check face detection
                if self._face_detection_enabled and self._callbacks['face']:
                    result = self.get_face_detection()
                    if result.detected:
                        for callback in self._callbacks['face']:
                            callback(result)
                
                # Check QR detection (only trigger on new data)
                if self._qr_detection_enabled and self._callbacks['qr']:
                    result = self.get_qr_detection()
                    if result.detected and result.data != last_qr_data:
                        last_qr_data = result.data
                        for callback in self._callbacks['qr']:
                            callback(result)
                
                # Check object detection
                if self._object_detection_enabled and self._callbacks['object']:
                    result = self.get_object_detection()
                    if result.detected:
                        for callback in self._callbacks['object']:
                            callback(result)
                
                # Check traffic sign detection
                if self._traffic_sign_detection_enabled and self._callbacks['traffic_sign']:
                    result = self.get_traffic_sign_detection()
                    if result.detected:
                        for callback in self._callbacks['traffic_sign']:
                            callback(result)
                
                # Check image classification (only trigger on new data)
                if self._image_classification_enabled and self._callbacks['image_classify']:
                    result = self.get_image_classification()
                    if result.detected and result.data != last_classify_data:
                        last_classify_data = result.data
                        for callback in self._callbacks['image_classify']:
                            callback(result)
                
                time.sleep(interval)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    # ============ Utility Methods ============
    
    def disable_all_detections(self):
        """Disable all detection types."""
        self.disable_color_detection()
        self.disable_face_detection()
        self.disable_qr_detection()
        if self._object_detection_enabled:
            self.disable_object_detection()
        if self._traffic_sign_detection_enabled:
            self.disable_traffic_sign_detection()
        if self._image_classification_enabled:
            self.disable_image_classification()
    
    def get_detection_status(self) -> Dict[str, bool]:
        """
        Get status of all detection types.
        
        Returns:
            Dictionary with detection enabled status
        """
        return {
            'camera': self.is_camera_running,
            'display': self.is_display_running,
            'color': self._color_detection_enabled,
            'face': self._face_detection_enabled,
            'qr': self._qr_detection_enabled,
            'object': self._object_detection_enabled,
            'traffic_sign': self._traffic_sign_detection_enabled,
            'image_classify': self._image_classification_enabled,
            'monitoring': self._monitor_running,
            'current_color': self._current_color
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start_camera()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_camera()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.stop_camera()
        except:
            pass


# ============ Convenience Functions ============

def create_color_tracker(color: str, vflip: bool = False, hflip: bool = False) -> VilibDetector:
    """
    Create a detector configured for color tracking.
    
    Args:
        color: Color to track
        vflip: Vertical flip
        hflip: Horizontal flip
    
    Returns:
        Configured VilibDetector instance
    """
    detector = VilibDetector(vflip=vflip, hflip=hflip)
    detector.start_camera()
    detector.start_display(web=True)
    detector.enable_color_detection(color)
    return detector


def create_face_tracker(vflip: bool = False, hflip: bool = False) -> VilibDetector:
    """
    Create a detector configured for face tracking.
    
    Args:
        vflip: Vertical flip
        hflip: Horizontal flip
    
    Returns:
        Configured VilibDetector instance
    """
    detector = VilibDetector(vflip=vflip, hflip=hflip)
    detector.start_camera()
    detector.start_display(web=True)
    detector.enable_face_detection()
    return detector


def create_qr_reader(vflip: bool = False, hflip: bool = False) -> VilibDetector:
    """
    Create a detector configured for QR code reading.
    
    Args:
        vflip: Vertical flip
        hflip: Horizontal flip
    
    Returns:
        Configured VilibDetector instance
    """
    detector = VilibDetector(vflip=vflip, hflip=hflip)
    detector.start_camera()
    detector.start_display(web=True)
    detector.enable_qr_detection()
    return detector


def create_object_detector(vflip: bool = False, hflip: bool = False) -> VilibDetector:
    """
    Create a detector configured for object detection (default).
    
    Args:
        vflip: Vertical flip
        hflip: Horizontal flip
    
    Returns:
        Configured VilibDetector instance
    """
    detector = VilibDetector(vflip=vflip, hflip=hflip)
    detector.start_camera()
    detector.start_display(web=True)
    detector.enable_object_detection()
    return detector


def create_traffic_sign_detector(vflip: bool = False, hflip: bool = False) -> VilibDetector:
    """
    Create a detector configured for traffic sign detection.
    
    Args:
        vflip: Vertical flip
        hflip: Horizontal flip
    
    Returns:
        Configured VilibDetector instance
    """
    detector = VilibDetector(vflip=vflip, hflip=hflip)
    detector.start_camera()
    detector.start_display(web=True)
    detector.enable_traffic_sign_detection()
    return detector


def create_image_classifier(vflip: bool = False, hflip: bool = False) -> VilibDetector:
    """
    Create a detector configured for image classification.
    
    Args:
        vflip: Vertical flip
        hflip: Horizontal flip
    
    Returns:
        Configured VilibDetector instance
    """
    detector = VilibDetector(vflip=vflip, hflip=hflip)
    detector.start_camera()
    detector.start_display(web=True)
    detector.enable_image_classification()
    return detector
