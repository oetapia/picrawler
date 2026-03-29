# Photo Dataset Collection for ML Training

Complete system for collecting synchronized photo + sensor datasets during robot navigation. Build custom image classifiers trained on your robot's actual operating environment.

## 📋 Overview

This system captures:
- **Photos** (1-5 Hz) using lightweight `picamera2` (SimpleCamera)
- **Sensor readings** (10 Hz) - distance, accelerometer, floor sensors
- **Robot actions** - forward, turn, backward, etc.
- **Auto-generated labels** - based on sensor readings

**Key Benefits:**
- ✅ **70-80% less CPU** than vilib (5-10% vs 30-40%)
- ✅ **Auto-labeled** data (no manual labeling needed)
- ✅ **Synchronized** photos with exact sensor state
- ✅ **ML-ready** export to PyTorch/TensorFlow formats
- ✅ **Non-blocking** async photo saves
- ✅ **Low storage** (~70 MB/hour @ 320x240, 2 Hz)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Dataset Collection (Navigation + Photos)                   │
├─────────────────────────────────────────────────────────────┤
│  SimpleCamera (picamera2)                                   │
│  ├─ Lightweight photo capture (5-10% CPU)                  │
│  ├─ 320x240 JPEG @ 2 Hz                                    │
│  └─ Async disk writes (non-blocking)                       │
│                                                              │
│  SensorHub                                                   │
│  ├─ Distance sensors (ToF)                                 │
│  ├─ Accelerometer (tilt)                                   │
│  └─ Floor sensors (IR)                                     │
│                                                              │
│  DataLoggerWithPhotos                                       │
│  ├─ Sensor logging (10 Hz)                                 │
│  ├─ Photo capture (2 Hz)                                   │
│  ├─ Auto-labeling                                          │
│  └─ CSV manifest                                           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Output Structure

```
self_aware/logs/session_2026-03-14_04-05-30/
├── sensor_data.csv          # All sensor readings (10 Hz)
├── photo_manifest.csv        # Photo metadata + labels (2 Hz)
├── photos/                   # JPEG images
│   ├── frame_000001.jpg
│   ├── frame_000002.jpg
│   └── ...
├── dataset_report.html       # Visual analysis (optional)
└── dataset_export/           # ML-ready format (optional)
    ├── train/
    │   ├── clear_path/
    │   ├── obstacle_close/
    │   └── floor_danger/
    ├── val/
    └── test/
```

## 🚀 Quick Start

### 1. Collect Dataset (Automated)

Run the robot with photo capture enabled:

```bash
# Quick 30-second test
python examples/collect_dataset_with_photos.py --test

# Collect for 5 minutes (default)
python examples/collect_dataset_with_photos.py

# Collect for 30 minutes with higher photo rate
python examples/collect_dataset_with_photos.py -d 30 -r 3.0

# Lower resolution for faster capture
python examples/collect_dataset_with_photos.py -d 10 --resolution 160 120
```

The robot will navigate autonomously while collecting data.

### 2. Review Dataset

```bash
# List all sessions
python self_aware/dataset_utils.py --list

# Analyze specific session
python self_aware/dataset_utils.py --analyze session_2026-03-14_04-05-30

# Generate HTML report with sample images
python self_aware/dataset_utils.py --report session_2026-03-14_04-05-30
```

### 3. Export for Training

```bash
# Export to PyTorch ImageFolder format
python self_aware/dataset_utils.py --export session_2026-03-14_04-05-30
```

This creates train/val/test splits (70%/15%/15% default) organized by label.

## 🔧 Manual Integration

For custom navigation code:

```python
from self_aware.data_logger_with_photos import DataLoggerWithPhotos
from components.sensors.sensor_fusion import SensorHub
from picrawler import Picrawler

# Initialize
logger = DataLoggerWithPhotos(
    log_dir="self_aware/logs",
    capture_photos=True,
    photo_rate_hz=2.0,              # 2 photos/second
    photo_resolution=(320, 240)      # Good for training
)

logger.start_photo_capture()
sensor_hub = SensorHub()
robot = Picrawler()

try:
    while True:
        # Read sensors
        front_distance = sensor_hub.get_front_distance()
        rear_distance = sensor_hub.get_rear_distance()
        pitch, roll = sensor_hub.get_tilt()
        floor = sensor_hub.get_floor_sensors()
        
        sensor_data = {
            'front_distance': front_distance,
            'rear_distance': rear_distance,
            'pitch': pitch,
            'roll': roll,
            **floor
        }
        
        # Navigate
        if front_distance < 20:
            action = 'turn_left'
            steps = 2
        else:
            action = 'forward'
            steps = 1
        
        action_data = {'action': action, 'steps': steps, 'speed': 70}
        context_data = {'state': 'exploring'}
        
        # Log with photo capture
        logger.log_entry_with_photo(sensor_data, action_data, context_data)
        
        # Execute
        robot.do_action(action, step_num=steps)
        
        time.sleep(0.1)  # 10 Hz loop
        
finally:
    logger.close()
    sensor_hub.close()
```

## 🏷️ Auto-Labeling System

Labels are automatically generated from sensor readings:

| Label | Condition |
|-------|-----------|
| `clear_path` | Distance > 50 cm, no floor danger |
| `obstacle_far` | Distance 35-50 cm |
| `obstacle_medium` | Distance 20-35 cm |
| `obstacle_close` | Distance 10-20 cm |
| `obstacle_very_close` | Distance < 10 cm |
| `floor_danger` | Any floor sensor triggered |
| `floor_danger_severe` | 3+ floor sensors triggered |

### Manual Labels (Optional)

Override auto-labeling with custom labels:

```python
# Manual label
logger.log_entry_with_photo(
    sensor_data, 
    action_data, 
    context_data,
    manual_label="narrow_hallway"  # Custom label
)
```

## 📊 Dataset Analysis

### View Statistics

```python
from self_aware.dataset_utils import analyze_session

stats = analyze_session("self_aware/logs/session_2026-03-14_04-05-30")
print(f"Photos: {stats['photo_count']}")
print(f"Labels: {stats['label_distribution']}")
```

### Generate Report

Creates HTML report with:
- Dataset summary statistics
- Label distribution table
- Sample images from each class

```bash
python self_aware/dataset_utils.py --report session_2026-03-14_04-05-30
# Open: self_aware/logs/session_2026-03-14_04-05-30/dataset_report.html
```

## 🎓 Training Pipeline (Next Steps)

### 1. Load Dataset

```python
from torchvision import datasets, transforms

# After exporting with dataset_utils
train_data = datasets.ImageFolder(
    'self_aware/logs/session_2026-03-14_04-05-30/dataset_export/train',
    transform=transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
)
```

### 2. Train Model

Use standard PyTorch/TensorFlow training:
- Start with pre-trained models (MobileNet, EfficientNet)
- Fine-tune on your collected dataset
- Keep models lightweight for Raspberry Pi

### 3. Deploy

Replace auto-labeling with your trained model:

```python
# Future: Use your trained model
model = load_model('path_classifier.pth')

# Instead of auto-labels, use model predictions
prediction = model(photo)
logger.log_entry_with_photo(..., manual_label=prediction)
```

## ⚙️ Configuration Options

### Photo Resolution

| Resolution | Use Case | Storage/hour | Speed |
|------------|----------|--------------|-------|
| 160x120 | Fast, simple models | ~20 MB | Fastest |
| 320x240 | **Recommended** | ~70 MB | Balanced |
| 640x480 | High detail | ~280 MB | Slower |

### Capture Rate

| Rate | Photos/min | Use Case |
|------|------------|----------|
| 1 Hz | 60 | Conservative, long sessions |
| **2 Hz** | 120 | **Recommended default** |
| 3 Hz | 180 | High variety needed |
| 5 Hz | 300 | Maximum detail |

**Tip:** Higher rates = more data but more storage and processing.

## 🔬 Advanced Usage

### Multiple Sessions

Merge multiple sessions for larger datasets:

```python
from self_aware.data_logger import merge_log_files

sessions = [
    'self_aware/logs/session_2026-03-14_04-05-30',
    'self_aware/logs/session_2026-03-14_10-20-15',
    'self_aware/logs/session_2026-03-15_08-30-45',
]

# Export each, then combine in training
for session in sessions:
    export_for_pytorch(session)
```

### Custom Labels by Context

```python
# Label based on environment/task
if current_task == "obstacle_course":
    label_prefix = "course_"
elif current_task == "room_navigation":
    label_prefix = "room_"

custom_label = f"{label_prefix}{auto_label}"
logger.log_entry_with_photo(..., manual_label=custom_label)
```

### Different Environments

Collect datasets in various environments:
- Indoor vs outdoor
- Different lighting conditions
- Various floor types
- Different obstacle types

This improves model generalization.

## 🐛 Troubleshooting

### Camera Not Starting

```python
# Test camera separately
from components.camera.simple_camera import SimpleCamera

camera = SimpleCamera(size=(320, 240))
camera.start()
frame = camera.get_frame()
print(f"Frame size: {len(frame)} bytes")
camera.stop()
```

### Low Photo Count

Check throttling:
- `photo_rate_hz=2.0` means 2 photos/sec max
- Main loop must run faster than photo rate
- Check `photo_manifest.csv` for actual capture times

### Storage Issues

```bash
# Check disk space
df -h

# Estimate storage needs:
# 320x240 JPEG ≈ 10 KB
# 2 Hz × 60 min = 7,200 photos = ~70 MB
```

### Performance Impact

Monitor CPU usage:
```bash
# While collecting
htop  # or top

# picamera2 should use ~5-10% CPU
# Much less than vilib's 30-40%
```

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `photo_logger.py` | Core photo capture (SimpleCamera wrapper) |
| `data_logger_with_photos.py` | Combined sensor + photo logging |
| `dataset_utils.py` | Export, analysis, reporting tools |
| `collect_dataset_with_photos.py` | Example usage script |

## 🎯 Next Steps

1. **Collect Data** - Run `collect_dataset_with_photos.py` for 30+ minutes
2. **Review Quality** - Generate HTML report, check samples
3. **Export Dataset** - Use `dataset_utils.py --export`
4. **Train Model** - Use PyTorch/TensorFlow on exported data
5. **Deploy** - Integrate trained model back into navigation

## 💡 Tips & Best Practices

✅ **DO:**
- Collect in diverse conditions (lighting, obstacles, floors)
- Start with default settings (2 Hz, 320x240)
- Review HTML reports to check label distribution
- Collect 1000+ photos per class minimum
- Use balanced datasets (similar counts per class)

❌ **DON'T:**
- Don't use max resolution (640x480) unless necessary
- Don't collect all data in one environment
- Don't ignore class imbalance
- Don't skip validation step before training

## 🔗 Related Documentation

- `components/camera/README_VILIB.md` - vilib camera features
- `self_aware/README.md` - Autonomous navigation
- `self_aware/README_ML.md` - ML prediction system

## 📝 Example Session

```bash
# 1. Collect 15 minutes of data
python examples/collect_dataset_with_photos.py -d 15

# 2. Check what was collected
python self_aware/dataset_utils.py --list

# 3. Generate report
python self_aware/dataset_utils.py --report session_2026-03-14_04-05-30

# 4. Open report in browser
# Navigate to: self_aware/logs/session_2026-03-14_04-05-30/dataset_report.html

# 5. Export for training
python self_aware/dataset_utils.py --export session_2026-03-14_04-05-30

# 6. Train your model (see PyTorch/TensorFlow docs)

# 7. Deploy and iterate!
```

## 🎉 Success!

You now have a complete system for collecting ML training datasets during autonomous navigation. The collected data can be used to train custom classifiers that understand your robot's specific environment and challenges.

Happy dataset collecting! 🤖📸
