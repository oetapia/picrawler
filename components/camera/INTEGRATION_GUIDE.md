# Vilib Detector Integration Guide

Quick guide for integrating the new VilibDetector module into existing projects.

## What Was Created

Based on `examples/treasure_hunt.py` and `examples/bull_fight.py`, we've created a reusable camera detection module:

```
components/camera/
├── __init__.py              (updated with new exports)
├── vilib_detector.py        (main detection module)
├── README_VILIB.md          (comprehensive documentation)
└── INTEGRATION_GUIDE.md     (this file)

examples/
└── visual_navigation_demo.py (integration example)
```

## Quick Start

### Import the Module

```python
# Basic imports
from components.camera import VilibDetector, DetectionResult

# Convenience functions
from components.camera import create_color_tracker, create_face_tracker
```

### Simple Usage

```python
from components.camera import create_color_tracker
import time

# One-line setup
detector = create_color_tracker('red')

while True:
    result = detector.get_color_detection()
    if result.detected:
        print(f"Found at {result.coordinate}")
    time.sleep(0.1)
```

## Integration Patterns

### Pattern 1: Add to Autonomous Navigator (self_aware)

```python
from self_aware.autonomous_navigator import AutonomousNavigator
from components.camera import VilibDetector

class VisualNavigator(AutonomousNavigator):
    def __init__(self):
        super().__init__()
        self.detector = VilibDetector()
        self.visual_mode = False
    
    def start(self):
        super().start()
        self.detector.start_camera()
        self.detector.enable_color_detection('red')
    
    def navigate_step(self):
        result = self.detector.get_color_detection()
        if result.detected:
            # Visual navigation logic
            direction = self.detector.get_color_direction(result)
            if direction == 'left':
                self.crawler.do_action('turn_left', 1, 80)
            elif direction == 'right':
                self.crawler.do_action('turn_right', 1, 80)
            else:
                self.crawler.do_action('forward', 1, 80)
        else:
            # Fall back to normal navigation
            super().navigate_step()
```

### Pattern 2: Add to Manual Control

```python
from components.camera import VilibDetector
from picrawler import Picrawler

crawler = Picrawler()
detector = VilibDetector()
detector.start_camera()
detector.enable_face_detection()

# Your existing manual control loop
while True:
    # Get visual feedback
    face_result = detector.get_face_detection()
    if face_result.detected:
        print(f"Face at {face_result.coordinate}")
    
    # Your existing keyboard/control code
    # ...
```

### Pattern 3: Background Monitoring with Callbacks

```python
from components.camera import VilibDetector
from picrawler import Picrawler

crawler = Picrawler()
detector = VilibDetector()

def on_color_found(result):
    """This runs automatically when color is detected"""
    print(f"Detected at {result.coordinate}")
    # Add your response logic here

detector.start_camera()
detector.enable_color_detection('blue')
detector.add_callback('color', on_color_found)
detector.start_monitoring()  # Runs in background thread

# Your main code continues...
```

## Real-World Integration Examples

### Example 1: Enhanced Self-Aware Navigator

Location: `examples/visual_navigation_demo.py`

Features:
- Autonomous obstacle avoidance (existing)
- Visual target seeking (new)
- Automatic mode switching
- Statistics tracking

Run with:
```bash
python examples/visual_navigation_demo.py --color red --duration 60
```

### Example 2: Manual Control with Visual Feedback

Add this to your manual control scripts:

```python
from components.camera import VilibDetector

# In your initialization
detector = VilibDetector()
detector.start_camera()
detector.start_display(web=True)
detector.enable_color_detection('green')  # or face, or QR

# In your control loop
result = detector.get_color_detection()
if result.detected:
    # Show visual feedback
    print(f"\rTarget at {result.x:3d}, size {result.width:3d}", end='')
```

### Example 3: QR Code Scanner for Navigation Waypoints

```python
from components.camera import VilibDetector

detector = VilibDetector()
detector.start_camera()
detector.enable_qr_detection()

waypoints = {}

while True:
    qr = detector.get_qr_detection()
    if qr.detected:
        # QR code contains waypoint instructions
        waypoint_data = qr.data
        print(f"Waypoint: {waypoint_data}")
        # Parse and execute waypoint logic
```

## Migration from Examples

### From bull_fight.py

**Before:**
```python
from vilib import Vilib

Vilib.camera_start()
Vilib.color_detect("red")

while True:
    if Vilib.detect_obj_parameter['color_n'] != 0:
        coordinate_x = Vilib.detect_obj_parameter['color_x']
        if coordinate_x < 100:
            # turn left
```

**After:**
```python
from components.camera import VilibDetector

detector = VilibDetector()
detector.start_camera()
detector.enable_color_detection('red')

while True:
    result = detector.get_color_detection()
    if result.detected:
        direction = detector.get_color_direction(result)
        if direction == 'left':
            # turn left
```

### From treasure_hunt.py

**Before:**
```python
from vilib import Vilib
import random

color = random.choice(color_list)
Vilib.color_detect(color)

if Vilib.detect_obj_parameter['color_n'] != 0 and \
   Vilib.detect_obj_parameter['color_w'] > 100:
    # target found
```

**After:**
```python
from components.camera import VilibDetector
import random

detector = VilibDetector()
detector.start_camera()

color = random.choice(color_list)
detector.enable_color_detection(color)

result = detector.get_color_detection()
if result.detected and result.width > 100:
    # target found
```

## Key Features for Integration

### 1. DetectionResult Object
Clean interface replaces raw parameter dictionary:
- `result.detected` - boolean
- `result.coordinate` - tuple (x, y)
- `result.size` - tuple (width, height)
- `result.width`, `result.height` - individual dimensions
- `result.data` - for QR codes

### 2. Helper Methods
- `get_color_direction(result)` - returns 'left', 'right', 'center', 'none'
- `is_color_centered(result)` - boolean check
- `get_detection_status()` - debugging info

### 3. Context Manager Support
```python
with VilibDetector() as detector:
    detector.enable_color_detection('blue')
    # Automatic cleanup
```

### 4. Callback System
React to detections automatically:
```python
detector.add_callback('color', my_handler_function)
detector.start_monitoring()  # Background thread
```

### 5. Multiple Detection Types
Enable multiple simultaneously:
```python
detector.enable_color_detection('red')
detector.enable_face_detection()
detector.enable_qr_detection()
```

## Best Practices

1. **Always clean up**
   ```python
   try:
       detector.start_camera()
       # your code
   finally:
       detector.stop_camera()
   ```

2. **Check detected flag**
   ```python
   result = detector.get_color_detection()
   if result.detected:  # Always check first
       print(result.coordinate)
   ```

3. **Use appropriate delays**
   ```python
   while True:
       result = detector.get_color_detection()
       # process result
       time.sleep(0.05)  # Don't hammer the detector
   ```

4. **Disable unused detections**
   ```python
   detector.disable_face_detection()  # Save processing
   ```

5. **Use callbacks for continuous monitoring**
   ```python
   # Better than polling in tight loop
   detector.add_callback('color', handler)
   detector.start_monitoring()
   ```

## Testing Your Integration

### Quick Test

```python
from components.camera import VilibDetector

with VilibDetector() as detector:
    detector.start_display(web=True)
    detector.enable_color_detection('red')
    
    print("Show a red object to the camera...")
    for i in range(50):
        result = detector.get_color_detection()
        if result.detected:
            print(f"✓ Detected at {result.coordinate}, size {result.size}")
        else:
            print("✗ Not detected")
        time.sleep(0.2)
```

### Check Installation

```python
# Verify imports work
from components.camera import VilibDetector, DetectionResult
from components.camera import create_color_tracker

print("✓ VilibDetector module installed correctly")

# Check vilib dependency
try:
    from vilib import Vilib
    print("✓ vilib dependency available")
except ImportError:
    print("✗ vilib not installed - run: pip install vilib")
```

## Troubleshooting

### Import Error
```
ImportError: cannot import name 'VilibDetector'
```
**Solution:** Make sure you're in the project root directory

### Camera Won't Start
```
Camera already in use
```
**Solution:** Stop other camera processes, or call `detector.stop_camera()` first

### No Detection
**Check:**
1. Camera is started: `detector.start_camera()`
2. Detection is enabled: `detector.enable_color_detection('red')`
3. Lighting conditions are good
4. Object is in frame and large enough

### Poor Performance
**Solutions:**
1. Disable unused detection types
2. Increase polling interval (0.1s instead of 0.05s)
3. Use callbacks instead of polling
4. Reduce display resolution if needed

## Next Steps

1. **Try the demo**: `python examples/visual_navigation_demo.py`
2. **Read full docs**: See `components/camera/README_VILIB.md`
3. **Integrate into your project**: Use patterns above
4. **Extend functionality**: Add your own callbacks and logic

## Support

- Full API documentation: `components/camera/README_VILIB.md`
- Example code: `examples/visual_navigation_demo.py`
- Original examples: `examples/treasure_hunt.py`, `examples/bull_fight.py`

---

**Summary**: This module wraps vilib to provide a clean, reusable interface for computer vision that can be easily integrated into autonomous navigation and manual control systems.
