# Diagnostic System TODO

**Project:** PiCrawler Robot Diagnostics  
**Date:** March 17, 2026  
**Status:** Foundation complete, 9 diagnostics pending

---

## 📊 Current Status

### ✅ Completed (Foundation)

- [x] **Base Classes** (`components/diagnostics/`)
  - [x] `BaseDiagnostic` - Standard base class with formatting, tracking, export
  - [x] `DiagnosticResult` - Data class for test results
  - [x] `SimpleDiagnostic` - Template for quick diagnostic creation

- [x] **Main Launcher** (`components/diagnostic.py`)
  - [x] Interactive menu system with 5 categories
  - [x] Command-line interface (--test, --suite, --all, --list)
  - [x] Test suites (sensors, motion, all)
  - [x] Result tracking and summaries
  - [x] Colored output formatting

- [x] **Existing Diagnostics** (6 available)
  - [x] Accelerometer (MPU-6050) - `accel_diagnostic.py`
  - [x] IR Floor Sensors - `ir_diagnostic.py`
  - [x] ToF Distance Sensors - `tof_diagnostic.py`
  - [x] I2C Multiplexer (PCA9548A) - `pca9548a_diagnostic.py`
  - [x] OLED Display - `oled_diagnostic.py`
  - [x] Camera & Detection - `camera_diagnostic.py`

---

## 🔜 Missing Diagnostics (9 Pending)

### High Priority (4 diagnostics)

#### 1. Battery Monitor Diagnostic
**File:** `components/sensors/battery_diagnostic.py`  
**ID:** `battery`  
**Category:** sensors

**Purpose:**
- Test battery voltage monitoring system
- Verify ADC readings from battery_status.py
- Check voltage thresholds and warnings

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.sensors.battery_status import BatteryStatus

class BatteryDiagnostic(BaseDiagnostic):
    def __init__(self):
        super().__init__("Battery Monitor", "Real-time voltage monitoring")
```

**Tests to Implement:**
1. **Initialization Test**
   - Initialize BatteryStatus class
   - Verify ADC connection
   - Check I2C communication

2. **Voltage Reading Test**
   - Read current battery voltage
   - Display voltage in V and percentage
   - Check if within safe range (6.0V - 8.4V typical)

3. **Live Monitoring Test** (10-30 seconds)
   - Stream voltage readings with timestamps
   - Calculate voltage stability (std deviation)
   - Display ASCII bar chart of voltage level
   - Show charge estimate (%)

4. **Threshold Test**
   - Test low voltage warning (< 6.5V)
   - Test critical voltage alarm (< 6.0V)
   - Verify warning system works

**Expected Output:**
```
======================================================================
  BATTERY MONITOR DIAGNOSTIC
======================================================================

[STEP 1] Initializing battery monitor...
  [OK] ADC initialized at address 0x48
  [OK] Battery voltage: 7.8V (65% charge)

[STEP 2] Live voltage monitoring (30s)...
  7.82V |████████████████████░░░░░░| 65%  [00:00]
  7.81V |████████████████████░░░░░░| 65%  [00:05]
  7.80V |████████████████████░░░░░░| 65%  [00:10]
  ...

[STEP 3] Threshold validation...
  [OK] Normal range (7.80V > 6.5V warning threshold)
  [OK] Above critical (7.80V > 6.0V critical threshold)

----------------------------------------------------------------------
RESULT: [OK] PASS - Battery monitor operational
Duration: 35.2s
----------------------------------------------------------------------
```

---

#### 2. Motion Controller Diagnostic
**File:** `components/navigation/motion_diagnostic.py`  
**ID:** `motion`  
**Category:** motion

**Purpose:**
- Test motion controller state machine
- Verify movement transitions
- Check speed ramping and interpolation

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.navigation.motion_controller import MotionController
```

**Tests to Implement:**
1. **Initialization Test**
   - Initialize MotionController
   - Verify default state (IDLE)
   - Check servo connections

2. **State Transition Test**
   - Test IDLE → WALKING transition
   - Test WALKING → RUNNING transition
   - Test transitions to TURNING, BACKING
   - Verify state machine integrity

3. **Movement Test** (requires hardware)
   - Execute forward movement (5 steps)
   - Execute backward movement (5 steps)
   - Execute left turn (90°)
   - Execute right turn (90°)
   - Measure actual vs expected movement

4. **Speed Ramping Test**
   - Test acceleration from stop to walk
   - Test acceleration from walk to run
   - Test deceleration from run to stop
   - Verify smooth interpolation

5. **Recovery Test**
   - Test emergency stop
   - Test resume after stop
   - Verify state recovery

**Expected Output:**
```
======================================================================
  MOTION CONTROLLER DIAGNOSTIC
======================================================================

[STEP 1] Initializing motion controller...
  [OK] Controller initialized
  [OK] Current state: IDLE
  [OK] 12 servos connected

[STEP 2] State transition test...
  [OK] IDLE → WALKING (transition time: 0.5s)
  [OK] WALKING → RUNNING (transition time: 0.3s)
  [OK] RUNNING → TURNING_LEFT (transition time: 0.4s)
  [OK] All transitions valid

[STEP 3] Movement execution test...
  [i] Testing forward movement (5 steps)...
  [OK] Forward: 5 steps completed in 2.1s
  [i] Testing backward movement (5 steps)...
  [OK] Backward: 5 steps completed in 2.3s

[STEP 4] Speed ramping test...
  [OK] Acceleration curve: smooth (0.1s ramp time)
  [OK] Deceleration curve: smooth (0.1s ramp time)

----------------------------------------------------------------------
RESULT: [OK] PASS - Motion controller operational
Duration: 12.8s
----------------------------------------------------------------------
```

---

#### 3. Sensor Fusion Diagnostic
**File:** `components/sensors/sensor_fusion_diagnostic.py`  
**ID:** `fusion`  
**Category:** sensors

**Purpose:**
- Test multi-sensor integration
- Verify sensor fusion logic
- Check data synchronization

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.sensors.sensor_fusion import SensorFusion
```

**Tests to Implement:**
1. **Initialization Test**
   - Initialize all sensors (accel, IR, ToF)
   - Verify data streams
   - Check fusion algorithm ready

2. **Data Synchronization Test**
   - Collect simultaneous readings from all sensors
   - Check timestamp alignment
   - Verify data rate consistency (10 Hz)

3. **Fusion Logic Test**
   - Test floor danger detection (IR + accel tilt)
   - Test obstacle detection (ToF + IR)
   - Test balance calculation (accel + gyro)
   - Verify combined state output

4. **Edge Case Test**
   - Test with one sensor missing
   - Test with conflicting sensor data
   - Test fusion fallback modes

**Expected Output:**
```
======================================================================
  SENSOR FUSION DIAGNOSTIC
======================================================================

[STEP 1] Initializing sensor fusion...
  [OK] Accelerometer initialized
  [OK] IR sensors (4) initialized
  [OK] ToF sensors initialized
  [OK] Fusion algorithm ready

[STEP 2] Data synchronization test (5s)...
  [OK] Sample rate: 10.2 Hz (target: 10 Hz)
  [OK] Timestamp jitter: 2.3ms (acceptable)
  [OK] Data alignment: synchronized

[STEP 3] Fusion logic test...
  [OK] Floor danger: SAFE (all IR idle, tilt=0.5°)
  [OK] Obstacle: NONE (ToF distances > 30cm)
  [OK] Balance: LEVEL (pitch=0.5°, roll=0.3°)
  [OK] Combined state: OPERATIONAL

[STEP 4] Edge case handling...
  [i] Simulating ToF sensor failure...
  [OK] Fallback to IR-only mode activated
  [i] Simulating conflicting data...
  [OK] Conflict resolution: prioritized ToF over IR

----------------------------------------------------------------------
RESULT: [OK] PASS - Sensor fusion operational
Duration: 18.5s
----------------------------------------------------------------------
```

---

#### 4. Obstacle Handler Diagnostic
**File:** `components/navigation/obstacle_diagnostic.py`  
**ID:** `obstacle`  
**Category:** motion

**Purpose:**
- Test obstacle detection logic
- Verify avoidance strategies
- Check decision-making algorithm

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.navigation.obstacle_handler import ObstacleHandler
```

**Tests to Implement:**
1. **Initialization Test**
   - Initialize ObstacleHandler
   - Verify sensor integration
   - Check avoidance strategies loaded

2. **Detection Test**
   - Test front obstacle detection (< 20cm)
   - Test side obstacle detection
   - Test rear obstacle detection
   - Measure detection accuracy

3. **Strategy Selection Test**
   - Scenario: Front obstacle → Test TURN_LEFT/RIGHT
   - Scenario: Side obstacle → Test ADJUST_PATH
   - Scenario: Rear obstacle → Test MOVE_FORWARD
   - Scenario: Surrounded → Test STOP

4. **Avoidance Execution Test** (simulated)
   - Execute turn avoidance
   - Execute path adjustment
   - Execute backup maneuver
   - Verify completion

**Expected Output:**
```
======================================================================
  OBSTACLE HANDLER DIAGNOSTIC
======================================================================

[STEP 1] Initializing obstacle handler...
  [OK] Handler initialized
  [OK] Sensors integrated (ToF + IR)
  [OK] 4 avoidance strategies loaded

[STEP 2] Detection test...
  [i] Place obstacle in front (<20cm)...
  [OK] Front obstacle detected at 15cm
  [i] Place obstacle on left side...
  [OK] Left obstacle detected at 18cm

[STEP 3] Strategy selection test...
  Scenario: FRONT_OBSTACLE
    [OK] Selected: TURN_RIGHT (confidence: 0.85)
  Scenario: LEFT_OBSTACLE
    [OK] Selected: ADJUST_PATH_RIGHT (confidence: 0.90)
  Scenario: SURROUNDED
    [OK] Selected: STOP (confidence: 1.00)

[STEP 4] Avoidance execution (simulated)...
  [OK] Turn avoidance: completed in 1.2s
  [OK] Path adjustment: completed in 0.8s
  [OK] All maneuvers successful

----------------------------------------------------------------------
RESULT: [OK] PASS - Obstacle handler operational
Duration: 25.3s
----------------------------------------------------------------------
```

---

### Medium Priority (3 diagnostics)

#### 5. Balance System Diagnostic
**File:** `components/navigation/balance_diagnostic.py`  
**ID:** `balance`  
**Category:** motion

**Purpose:**
- Test balance pose calculation
- Verify tilt compensation
- Check servo angle adjustments

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.navigation.balance import BalanceController
```

**Tests to Implement:**
1. **Initialization Test**
2. **Static Balance Test** - Level surface balance
3. **Tilt Compensation Test** - Handling 5°, 10°, 15° tilts
4. **Dynamic Balance Test** - Balance while moving

---

#### 6. Recovery System Diagnostic
**File:** `components/navigation_state/recovery_diagnostic.py`  
**ID:** `recovery`  
**Category:** motion

**Purpose:**
- Test stuck detection algorithm
- Verify recovery strategies
- Check timeout handling

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.navigation_state.recovery import RecoverySystem
```

**Tests to Implement:**
1. **Initialization Test**
2. **Stuck Detection Test** - Detect no movement despite commands
3. **Recovery Strategy Test** - Test WIGGLE, BACKUP, REORIENT
4. **Timeout Handling Test** - Verify failure after max attempts

---

#### 7. Sound System Diagnostic
**File:** `components/sounds/sound_diagnostic.py`  
**ID:** `sound`  
**Category:** peripherals

**Purpose:**
- Test audio playback system
- Verify TTS (text-to-speech)
- Check audio library access

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.sounds.audio_manager import AudioManager
```

**Tests to Implement:**
1. **Initialization Test**
2. **Audio Playback Test** - Play sound effects
3. **TTS Test** - Generate and play speech
4. **Volume Control Test** - Test volume levels

---

### Low Priority (2 diagnostics)

#### 8. PS4 Controller Diagnostic
**File:** `components/sensors/ps4_diagnostic.py`  
**ID:** `ps4`  
**Category:** peripherals

**Purpose:**
- Test PS4 controller pairing
- Verify button input reading
- Check joystick calibration

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.sensors.ps4_control import PS4Controller
```

**Tests to Implement:**
1. **Pairing Test** - Detect and pair controller
2. **Button Test** - Test all button inputs
3. **Joystick Test** - Calibrate and test analog sticks
4. **Connection Stability Test** - Monitor signal strength

---

#### 9. Web Server API Diagnostic
**File:** `components/server/server_diagnostic.py`  
**ID:** `server`  
**Category:** peripherals

**Purpose:**
- Test Flask REST API endpoints
- Verify WebSocket communication
- Check streaming performance

**Requirements:**
```python
from components.diagnostics import BaseDiagnostic
from components.server.flask import create_app
```

**Tests to Implement:**
1. **Server Start Test** - Start Flask server
2. **Endpoint Test** - Test GET/POST endpoints
3. **WebSocket Test** - Test real-time data streaming
4. **Performance Test** - Measure response times

---

## 🏗️ Implementation Guide

### Using the Base Classes

All new diagnostics should inherit from `BaseDiagnostic`:

```python
#!/usr/bin/env python3
"""
component_diagnostic.py - Brief description

Tests: What it tests
Usage: python component_diagnostic.py
"""

from components.diagnostics import BaseDiagnostic

class ComponentDiagnostic(BaseDiagnostic):
    def __init__(self):
        super().__init__("Component Name", "Brief description")
        self.component = None
    
    def test_initialization(self) -> bool:
        """Test component initialization"""
        self.print_step(1, "Initializing component...")
        try:
            # Initialize your component
            self.component = YourComponent()
            self.print_success("Component initialized")
            return True
        except Exception as e:
            self.print_error(f"Failed: {e}")
            return False
    
    def test_basic_operation(self) -> bool:
        """Test basic operation"""
        self.print_step(2, "Testing basic operation...")
        # Your test logic here
        self.print_success("Basic operation working")
        return True
    
    def test_live_stream(self, duration: int = 10) -> bool:
        """Stream live data"""
        self.print_step(3, f"Live readings ({duration}s)...")
        # Streaming logic here
        self.print_success(f"Completed {duration}s of streaming")
        return True
    
    def run_test(self) -> bool:
        """Main test execution"""
        self.print_header()
        
        if not self.test_initialization():
            self.add_result("Initialization", False, "Failed to initialize")
            self.print_summary(False, "Initialization failed")
            return False
        self.add_result("Initialization", True, "Component initialized")
        
        if not self.test_basic_operation():
            self.add_result("Basic Operation", False, "Basic operation failed")
            self.print_summary(False, "Basic operation failed")
            return False
        self.add_result("Basic Operation", True, "Basic operation working")
        
        if not self.test_live_stream():
            self.add_result("Live Stream", False, "Streaming failed")
            self.print_summary(False, "Live streaming failed")
            return False
        self.add_result("Live Stream", True, "Streaming successful")
        
        self.print_summary(True, "All tests passed")
        return True

def main():
    diagnostic = ComponentDiagnostic()
    success = diagnostic.execute()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

### Registering New Diagnostics

After creating a new diagnostic, register it in `components/diagnostic.py`:

```python
def _register_diagnostics(self):
    self.diagnostics = {
        # ... existing diagnostics ...
        
        'your_id': {
            'name': 'Your Component Name',
            'module': 'components.category.your_diagnostic',
            'category': 'sensors',  # or displays, camera, motion, peripherals
            'available': self._check_file_exists('components/category/your_diagnostic.py'),
            'description': 'Brief description of what it tests'
        },
    }
```

---

## 📝 Testing Checklist

For each new diagnostic:

- [ ] Inherits from `BaseDiagnostic`
- [ ] Has proper docstring with usage info
- [ ] Implements `run_test()` method
- [ ] Uses standard formatting methods (print_step, print_success, etc.)
- [ ] Adds results with `add_result()`
- [ ] Prints final summary with `print_summary()`
- [ ] Has `main()` function for standalone execution
- [ ] Registered in `components/diagnostic.py`
- [ ] Tests independently: `python3 components/category/diagnostic.py`
- [ ] Tests via launcher: `python3 components/diagnostic.py --test id`
- [ ] Handles errors gracefully
- [ ] Works with Ctrl+C interruption

---

## 🎯 Priority Workflow

**Phase 1: High Priority (Week 1-2)**
```bash
# Create these first
1. components/sensors/battery_diagnostic.py
2. components/navigation/motion_diagnostic.py
3. components/sensors/sensor_fusion_diagnostic.py
4. components/navigation/obstacle_diagnostic.py
```

**Phase 2: Medium Priority (Week 3)**
```bash
5. components/navigation/balance_diagnostic.py
6. components/navigation_state/recovery_diagnostic.py
7. components/sounds/sound_diagnostic.py
```

**Phase 3: Low Priority (Week 4)**
```bash
8. components/sensors/ps4_diagnostic.py
9. components/server/server_diagnostic.py
```

---

## 📚 References

- **Base Classes:** `components/diagnostics/base.py`
- **Main Launcher:** `components/diagnostic.py`
- **Existing Examples:**
  - Simple pattern: `components/sensors/accel_diagnostic.py`
  - Complex pattern: `components/camera/camera_diagnostic.py`
  - Multi-step: `components/sensors/tof_diagnostic.py`

- **Documentation:**
  - `DIAGNOSTIC_TOOLS.md` - Complete diagnostic inventory
  - `DEV_WORKFLOW.md` - Development workflow guide
  - `CUSTOM_MODULES_MANIFEST.md` - File structure

---

**Last Updated:** March 17, 2026  
**Status:** 6 diagnostics complete, 9 pending  
**Next:** Start with battery_diagnostic.py (high priority)
