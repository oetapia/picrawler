# Vilib Detector Module

A clean, reusable interface for vilib-based computer vision detection. This module wraps vilib functionality to make it easy to integrate color detection, face detection, and QR code detection into your Picrawler projects.

## Features

- **Color Detection**: Track red, orange, yellow, green, blue, or purple objects
- **Face Detection**: Detect and track human faces
- **QR Code Detection**: Read QR codes in real-time
- **Photo Capture**: Take photos with the camera
- **Video Recording**: Record, pause, and resume video
- **Callbacks**: Register functions to be called when objects are detected
- **Background Monitoring**: Optional threaded monitoring for continuous detection

## Quick Start

### Basic Color Detection

```python
from components.camera import VilibDetector
import time

# Create detector and start tracking red objects
detector = VilibDetector()
detector.start_camera()
detector.start_display(web=True)
detector.enable_color_detection('red')

try:
    while True:
        result = detector.get_color_detection()
        if result.detected:
            print(f"Red object found at {result.coordinate}, size: {result.size}")
        time.sleep(0.1)
finally:
    detector.stop_camera()
```

### Using Context Manager

```python
from components.camera import VilibDetector
import time

with VilibDetector() as detector:
    detector.start_display(web=True)
    detector.enable_color_detection('blue')
    
    for _ in range(100):
        result = detector.get_color_detection()
        if result.detected:
            print(f"Blue object at {result.coordinate}")
        time.sleep(0.1)
```

### Convenience Functions

```python
from components.camera import create_color_tracker, create_face_tracker
import time

# Quick color tracking
detector = create_color_tracker('green')

while True:
    result = detector.get_color_detection()
    if result.detected:
        print(f"Green object found!")
    time.sleep(0.1)
```

## Integration Examples

### Integration with Self-Aware Navigator

Add visual target seeking to autonomous navigation:

```python
from self_aware.autonomous_navigator import AutonomousNavigator
from components.camera import VilibDetector
from picrawler import Picrawler

class VisualNavigator(AutonomousNavigator):
    def __init__(self, target_color='red'):
        super().__init__()
        self.detector = VilibDetector()
        self.target_color = target_color
        self.visual_mode = False
    
    def start(self):
        """Start navigation with vision"""
        super().start()
        self.detector.start_camera()
        self.detector.start_display(web=True)
        self.detector.enable_color_detection(self.target_color)
    
    def enable_visual_seeking(self):
        """Enable visual target seeking mode"""
        self.visual_mode = True
    
    def disable_visual_seeking(self):
        """Disable visual target seeking mode"""
        self.visual_mode = False
    
    def navigate_step(self):
        """Enhanced navigation with visual seeking"""
        if self.visual_mode:
            # Check for visual target
            result = self.detector.get_color_detection()
            if result.detected:
                direction = self.detector.get_color_direction(result)
                
                if direction == 'left':
                    self.crawler.do_action('turn_left', 1, 80)
                    return
                elif direction == 'right':
                    self.crawler.do_action('turn_right', 1, 80)
                    return
                elif direction == 'center' and result.width > 100:
                    # Target is large and centered - we've reached it!
                    print(f"Reached {self.target_color} target!")
                    self.visual_mode = False
                    return
                else:
                    # Move forward toward target
                    self.crawler.do_action('forward', 1, 80)
                    return
        
        # Fall back to normal obstacle avoidance
        super().navigate_step()
    
    def stop(self):
        """Clean stop with camera shutdown"""
        self.detector.stop_camera()
        super().stop()

# Usage
if __name__ == '__main__':
    nav = VisualNavigator(target_color='red')
    nav.start()
    nav.enable_visual_seeking()
    
    try:
        nav.run(duration=60)
    finally:
        nav.stop()
```

### Integration with Manual Control

Add visual feedback to manual control:

```python
from components.camera import VilibDetector
from picrawler import Picrawler
import readchar

crawler = Picrawler()
detector = VilibDetector()

# Start camera with face detection
detector.start_camera()
detector.start_display(web=True)
detector.enable_face_detection()

print("Manual control with face detection active!")
print("Press 'w/a/s/d' to move, 'f' to toggle face detection, 'q' to quit")

face_enabled = True

try:
    while True:
        # Get face detection status
        if face_enabled:
            result = detector.get_face_detection()
            if result.detected:
                print(f"\rFace detected at {result.coordinate}", end='')
            else:
                print("\rNo face detected        ", end='')
        
        # Handle keyboard input (non-blocking would be better)
        key = readchar.readkey()
        
        if key == 'w':
            crawler.do_action('forward', 1, 80)
        elif key == 's':
            crawler.do_action('backward', 1, 80)
        elif key == 'a':
            crawler.do_action('turn_left', 1, 80)
        elif key == 'd':
            crawler.do_action('turn_right', 1, 80)
        elif key == 'f':
            face_enabled = not face_enabled
            if face_enabled:
                detector.enable_face_detection()
            else:
                detector.disable_face_detection()
            print(f"\nFace detection: {'ON' if face_enabled else 'OFF'}")
        elif key == 'q':
            break
finally:
    detector.stop_camera()
```

### Using Callbacks for Reactive Behavior

```python
from components.camera import VilibDetector
from picrawler import Picrawler
from robot_hat import TTS
import time

crawler = Picrawler()
tts = TTS()
detector = VilibDetector()

def on_color_detected(result):
    """React when color is detected"""
    direction = detector.get_color_direction(result)
    
    if direction == 'left':
        crawler.do_action('turn_left', 1, 60)
    elif direction == 'right':
        crawler.do_action('turn_right', 1, 60)
    elif direction == 'center':
        if result.width > 100:
            tts.say("Target reached!")
        else:
            crawler.do_action('forward', 1, 80)

def on_face_detected(result):
    """React when face is detected"""
    print(f"Hello! Face detected at {result.coordinate}")
    tts.say("Hello human!")

# Setup
detector.start_camera()
detector.start_display(web=True)
detector.enable_color_detection('red')
detector.enable_face_detection()

# Register callbacks
detector.add_callback('color', on_color_detected)
detector.add_callback('face', on_face_detected)

# Start monitoring (runs in background thread)
detector.start_monitoring(interval=0.1)

try:
    # Main loop can do other things
    while True:
        time.sleep(1)
        status = detector.get_detection_status()
        print(f"Status: {status}")
finally:
    detector.stop_camera()
```

## API Reference

### VilibDetector Class

#### Initialization

```python
detector = VilibDetector(vflip=False, hflip=False)
```

**Parameters:**
- `vflip` (bool): Vertical flip of camera image
- `hflip` (bool): Horizontal flip of camera image

#### Camera Control Methods

- `start_camera(vflip=None, hflip=None)` - Start the camera
- `stop_camera()` - Stop camera and all detections
- `start_display(local=False, web=True)` - Start video display

#### Color Detection Methods

- `enable_color_detection(color)` - Enable color detection
  - Colors: 'red', 'orange', 'yellow', 'green', 'blue', 'purple'
- `disable_color_detection()` - Disable color detection
- `get_color_detection()` - Get current detection result (returns DetectionResult)
- `is_color_centered(result, center_min=100, center_max=220)` - Check if color is centered
- `get_color_direction(result, left_threshold=100, right_threshold=220)` - Get direction ('left', 'right', 'center', 'none')

#### Face Detection Methods

- `enable_face_detection()` - Enable face detection
- `disable_face_detection()` - Disable face detection
- `get_face_detection()` - Get current detection result (returns DetectionResult)

#### QR Code Detection Methods

- `enable_qr_detection()` - Enable QR code detection
- `disable_qr_detection()` - Disable QR code detection
- `get_qr_detection()` - Get current detection result (returns DetectionResult with data field)

#### Photo & Video Methods

- `take_photo(name, path='./')` - Capture a photo
- `start_video_recording(name, path='./')` - Start recording
- `pause_video_recording()` - Pause recording
- `resume_video_recording()` - Resume recording
- `stop_video_recording()` - Stop recording

#### Callback Methods

- `add_callback(detection_type, callback)` - Add detection callback
  - Types: 'color', 'face', 'qr'
  - Callback signature: `callback(result: DetectionResult)`
- `remove_callback(detection_type, callback)` - Remove callback
- `start_monitoring(interval=0.05)` - Start background monitoring thread
- `stop_monitoring()` - Stop background monitoring

#### Utility Methods

- `disable_all_detections()` - Disable all detection types
- `get_detection_status()` - Get status dictionary

### DetectionResult Class

Result object returned by detection methods.

**Attributes:**
- `detected` (bool): Whether object was detected
- `count` (int): Number of objects detected
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `width` (int): Width of detected object
- `height` (int): Height of detected object
- `data` (str): Data field (used for QR codes)

**Properties:**
- `coordinate` - Tuple of (x, y)
- `size` - Tuple of (width, height)
- `center_x` - Center X coordinate
- `center_y` - Center Y coordinate

### Convenience Functions

```python
from components.camera import create_color_tracker, create_face_tracker, create_qr_reader

# Create pre-configured detectors
color_detector = create_color_tracker('red')
face_detector = create_face_tracker()
qr_detector = create_qr_reader()
```

## Bull Fight Example Recreation

Here's how to recreate the bull_fight.py example using the new module:

```python
from picrawler import Picrawler
from components.camera import VilibDetector
from robot_hat import Music
from time import sleep

crawler = Picrawler()
music = Music()
detector = VilibDetector()

def main():
    detector.start_camera()
    detector.start_display()
    detector.enable_color_detection('red')
    speed = 80

    try:
        while True:
            result = detector.get_color_detection()
            
            if result.detected:
                music.sound_play_threading('./sounds/talk1.wav')
                direction = detector.get_color_direction(result)
                
                if direction == 'left':
                    crawler.do_action('turn_left', 1, speed)
                elif direction == 'right':
                    crawler.do_action('turn_right', 1, speed)
                else:
                    crawler.do_action('forward', 2, speed)
            else:
                crawler.do_step('stand', speed)
            
            sleep(0.05)
    finally:
        detector.stop_camera()

if __name__ == "__main__":
    main()
```

## Treasure Hunt Example Recreation

```python
from picrawler import Picrawler
from components.camera import VilibDetector
from robot_hat import Music, TTS
from time import sleep
import random

crawler = Picrawler()
music = Music()
tts = TTS()
detector = VilibDetector()

color_list = ["red", "orange", "yellow", "green", "blue", "purple"]

def renew_color_detect():
    color = random.choice(color_list)
    detector.enable_color_detection(color)
    tts.say("Look for " + color)

def main():
    detector.start_camera(vflip=False, hflip=False)
    detector.start_display(local=False, web=True)
    sleep(0.8)
    
    speed = 80
    tts.say("game start")
    sleep(0.05)
    renew_color_detect()
    
    try:
        while True:
            result = detector.get_color_detection()
            
            # Check if target found
            if result.detected and result.width > 100:
                tts.say("well done")
                sleep(0.05)
                renew_color_detect()
            
            # Manual control would go here (keyboard input)
            # For autonomous, use result.x to guide movement
            
            sleep(0.05)
    finally:
        detector.stop_camera()

if __name__ == "__main__":
    main()
```

## Best Practices

1. **Always use try/finally or context manager** to ensure camera is properly closed
2. **Call `start_camera()` before any detection methods**
3. **Use callbacks for reactive behavior** instead of polling in tight loops
4. **Adjust thresholds** (center_min, center_max, etc.) based on your camera resolution
5. **Add delays** (0.05-0.1s) between detection checks to avoid overwhelming the system
6. **Check `result.detected`** before accessing other properties
7. **Use `get_detection_status()`** for debugging

## Troubleshooting

**Camera won't start:**
- Ensure vilib is properly installed
- Check camera permissions
- Verify no other process is using the camera

**Detection not working:**
- Verify detection is enabled with `get_detection_status()`
- Check lighting conditions
- Ensure camera has clear view
- Try adjusting vflip/hflip parameters

**Poor color detection:**
- Ensure good lighting
- Use solid, bright colored objects
- Increase object size threshold for reliability
- Consider background contrast

## Performance Tips

- Use `start_monitoring()` with callbacks instead of tight polling loops
- Set appropriate `interval` in monitoring (0.05s is usually good)
- Disable unused detection types
- Use web display instead of local display when possible
- Process detections in separate thread if doing heavy computation

## License

Part of the Picrawler project. See main project license.
