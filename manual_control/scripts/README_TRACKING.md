# Enhanced PiCrawler Autonomous Navigation

A comprehensive rewrite of the autonomous tracking system with smooth movement, sensor fusion, and swappable distance sensors.

## 🎯 Key Features

### Sensor Fusion
- **IR Sensors (per leg)**: Floor edge detection and terrain sensing
- **Accelerometer (MPU-6050)**: Real-time tilt monitoring and dynamic balance correction
- **Distance Sensor**: Obstacle detection with support for multiple sensor types
  - HC-SR04 Ultrasonic (default)
  - VL53L0X Time-of-Flight (up to 120cm)
  - VL53L1X Time-of-Flight (up to 400cm)

### Smooth Movement
- **Gradual speed transitions** - No jarring starts/stops
- **Adaptive speed control** - Adjusts based on terrain tilt and obstacles
- **Dynamic balance correction** - Active compensation for pitch and roll

### Intelligent Navigation
- **Multi-level obstacle detection** - Distance-based early warning system
- **Floor danger analysis** - Per-leg IR sensors detect edges and drops
- **Stuck detection and recovery** - Automatic escape patterns
- **State-based behavior** - Context-aware reactions to environment

## 📁 Files

### New Files
- `tracking.py` - Complete rewrite with enhanced features
- `components/sensors/distance_sensor.py` - Distance sensor abstraction layer

### Reference Files
- `tracking5.py` - Original advanced implementation (preserved for reference)
- `tracking6.py` - Alternative version

## 🚀 Quick Start

### Basic Usage

```bash
cd /path/to/picrawler/manual_control/scripts
python3 tracking.py
```

### Change Distance Sensor Type

Edit the configuration at the top of `tracking.py`:

```python
# Distance sensor configuration (change type here!)
DISTANCE_SENSOR_TYPE = "HC-SR04"  # Options: "HC-SR04", "VL53L0X", "VL53L1X"
```

For VL53L0X or VL53L1X, you may need to install additional libraries:

```bash
# For VL53L0X
pip install VL53L0X

# For VL53L1X
pip install vl53l1x
```

## 🔧 Configuration

All configuration is at the top of `tracking.py`:

```python
# Movement parameters
SPEED_MAX = 80           # Maximum speed
SPEED_NORMAL = 70        # Normal cruising speed
SPEED_CAUTION = 50       # Speed when tilted or cautious
SPEED_MIN = 35           # Minimum speed

# Distance thresholds (cm)
DISTANCE_DANGER = 15     # Emergency stop distance
DISTANCE_WARNING = 25    # Start avoiding distance
DISTANCE_SAFE = 40       # Safe clearance distance

# Tilt thresholds (degrees)
TILT_CAUTION = 10.0      # Start reducing speed
TILT_DANGER = 20.0       # Emergency slow mode

# Balance correction
BALANCE_DEADZONE = 3.0   # Ignore small tilts
BALANCE_MAX_TILT = 25.0  # Maximum compensation angle
BALANCE_SPEED = 60       # Speed for balance adjustments
```

## 🎮 How It Works

### Main Loop Priority

1. **Tilt Check** - Adjust speed based on pitch/roll
2. **Floor Sensors** - Check for edges/drops (highest priority)
3. **Distance Sensor** - Check for obstacles ahead
4. **Stuck Detection** - Check if robot needs escape maneuver
5. **Move Forward** - Execute smooth forward movement
6. **Balance Correction** - Apply dynamic leg adjustments

### State Machine

- **EXPLORING** - Normal navigation mode
- **AVOIDING_OBSTACLE** - Backing up and turning from obstacle
- **AVOIDING_FLOOR_DANGER** - Reacting to edge/drop detection
- **TILT_CORRECTION** - Adjusting for steep terrain
- **STUCK** - Executing escape pattern
- **EMERGENCY** - Emergency stop condition

### Smooth Movement

The `SmoothMotionController` class handles gradual speed transitions:

```python
# Speed changes gradually over time
current_speed: 50 → 55 → 60 → 65 → 70  (target)
```

No more jerky movements when accelerating or decelerating!

### Dynamic Balance

The system actively compensates for tilt by adjusting leg positions:

```
Pitch > 0 (nose down):  Extend front legs, retract back legs
Roll > 0 (tilt right):  Extend left legs, retract right legs
```

This keeps the robot body level even on slopes.

## 🆚 Improvements Over tracking5.py

### 1. **Smoother Movement**
   - Gradual speed transitions (no sudden changes)
   - Speed ramping controlled by `SmoothMotionController`
   
### 2. **Better Sensor Integration**
   - All sensors checked every loop iteration
   - IR sensors used continuously (not just for scanning)
   - Distance sensor with median filtering for noise reduction

### 3. **Swappable Distance Sensors**
   - Easy switching between HC-SR04, VL53L0X, VL53L1X
   - Abstraction layer handles all sensor differences
   - Automatic sensor validation and error handling

### 4. **Enhanced Balance**
   - Dynamic balance correction between every step
   - Compensates for both pitch and roll simultaneously
   - Proportional response (more tilt = more correction)

### 5. **Simplified Code Structure**
   - Clear separation of concerns
   - Well-documented methods
   - Easier to maintain and extend

### 6. **Better Floor Danger Handling**
   - More nuanced edge detection
   - Smart reaction based on danger type
   - Considers distance sensor when choosing escape route

## 📊 What Was Learned from tracking5.py

### Kept
✅ Per-leg IR sensor mapping  
✅ State machine architecture  
✅ Escape patterns for stuck situations  
✅ TTS announcements  
✅ Accelerometer integration  
✅ Balance compensation logic  

### Improved
🔄 **Movement smoothness** - Added gradual speed transitions  
🔄 **Sensor reading** - Continuous monitoring with filtering  
🔄 **Code organization** - Cleaner class structure  
🔄 **Error handling** - Better sensor failure recovery  

### Added
➕ **Distance sensor abstraction** - Support for multiple sensor types  
➕ **Smooth motion controller** - Professional speed ramping  
➕ **Enhanced balance** - Applied between every step  
➕ **Better documentation** - Comprehensive comments  

## 🐛 Troubleshooting

### Distance Sensor Not Working

```python
# Check sensor initialization output
✓ HC-SR04 initialized on trigger=D2, echo=D3  # Good
✗ Failed to initialize HC-SR04: ...           # Problem
```

**Solutions:**
- Verify pin connections (D2=trigger, D3=echo for HC-SR04)
- Check sensor power supply
- Try different sensor type
- System will fall back to IR-only mode if sensor fails

### Robot Moving Too Fast/Slow

Adjust speed constants in configuration:
```python
SPEED_NORMAL = 70   # Increase or decrease
```

### Too Sensitive to Tilt

Increase tilt thresholds:
```python
TILT_CAUTION = 15.0  # Was 10.0
TILT_DANGER = 30.0   # Was 20.0
```

### Balance Correction Too Aggressive

Reduce balance speed:
```python
BALANCE_SPEED = 40  # Was 60
```

## 🔬 Testing

### Test Distance Sensor Alone

```bash
cd components/sensors
python3 distance_sensor.py
```

### Test IR Sensors

```bash
cd components/sensors
python3 ir_distance.py
```

### Test Accelerometer

```bash
cd components/sensors
python3 accelerometer.py
```

## 🎓 Learning Resources

- **tracking5.py** - Advanced implementation with leg scanning
- **tracking.py** - This enhanced version with smooth movement
- **components/sensors/** - Individual sensor modules
- **picrawler/picrawler.py** - Robot control API

## 📝 Notes

### Pin Configuration

The default pin configuration is:
- **Distance Sensor**: D2 (trigger), D3 (echo)
- **IR Sensors**: D0 (BL), D1 (FR), D2 (BR), D3 (FL)
- **I2C Sensors**: Bus 1, Address 0x68 (MPU-6050), 0x29 (VL53L0X/VL53L1X)

⚠️ **Important**: If using HC-SR04 on D2/D3, the IR sensors on these pins won't work simultaneously.

### Performance Tips

1. **Reduce TTS** - Comment out `announce()` calls for faster reaction
2. **Increase loop delay** - Change `time.sleep(0.1)` to reduce CPU usage
3. **Disable balance** - Comment out `apply_balance()` if not needed
4. **Adjust thresholds** - Tune distances and speeds for your environment

## 🛠️ Future Enhancements

Potential improvements:
- Path planning and mapping
- Multiple distance sensors (front/sides)
- Camera integration for visual navigation
- Speed profiles for different terrain types
- Web interface for remote monitoring
- Data logging and analysis

## 📜 License

Same as main PiCrawler project.

## 👥 Contributing

To improve this system:
1. Test in different environments
2. Tune parameters for your robot
3. Report issues or suggest enhancements
4. Share your configuration tweaks

---

**Happy exploring! 🤖**
