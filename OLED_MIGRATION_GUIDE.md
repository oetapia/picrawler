# OLED Module Comparison & Migration Guide

## Overview

You have **3 options** for OLED control with your new hardware setup:

1. **Original `oled.py`** - Simple, main bus only
2. **New `oled_mux.py`** - Flexible, supports both main bus AND multiplexer
3. **Keep both** - Use the right one for each situation

## Your New Setup (OLED on Main Bus)

Since you're moving your OLED back to the main I2C bus, here's what you need to know:

### Hardware Connection
```
Raspberry Pi GPIO
├─ SDA (GPIO 2) ──┬── OLED (0x3C) ← Direct connection
│                 ├── MPU6050 (0x68)
│                 └── PCA9548A Multiplexer (0x70)
│                       ├─ Channel 0: VL53L0X #1 (0x29)
│                       └─ Channel 1: VL53L0X #2 (0x29)
└─ SCL (GPIO 3) ──┘
```

## Module Comparison

| Feature | Original `oled.py` | New `oled_mux.py` |
|---------|-------------------|-------------------|
| **Main bus support** | ✅ Yes | ✅ Yes |
| **Multiplexer support** | ❌ No | ✅ Yes |
| **Auto-detect OLED** | ❌ No | ✅ Yes (on mux) |
| **Explicit channel select** | ❌ No | ✅ Yes |
| **Maintains channel state** | N/A | ✅ Yes |
| **Resource cleanup** | ⚠️ Partial | ✅ Complete |
| **Error handling** | ⚠️ Basic | ✅ Comprehensive |
| **Same API** | ✅ Yes | ✅ Yes |

## Code Comparison

### Original `oled.py`

```python
from components.screens import oled

# Initialize (main bus only)
if oled.initialize_display():
    oled.update_display(header="Status", text="Running")
```

**Limitations:**
- ❌ Only works on main I2C bus
- ❌ No multiplexer support
- ❌ Less error handling
- ❌ No cleanup function

### New `oled_mux.py` - Main Bus Mode

```python
from components.screens import oled_mux

# Initialize on MAIN BUS (same as original!)
if oled_mux.initialize_display(use_multiplexer=False):
    oled_mux.update_display(header="Status", text="Running")
    oled_mux.close_display()  # Proper cleanup
```

**Advantages:**
- ✅ Works on main I2C bus (like original)
- ✅ Better error handling
- ✅ Proper resource cleanup
- ✅ Same API as original
- ✅ Can switch to multiplexer mode if needed later

### New `oled_mux.py` - Multiplexer Mode

```python
from components.screens import oled_mux

# Initialize through MULTIPLEXER
if oled_mux.initialize_display(use_multiplexer=True, channel=2):
    oled_mux.update_display(header="Status", text="Running")
    oled_mux.close_display()
```

**Use when:**
- ✅ OLED is connected to multiplexer
- ✅ You want to avoid I2C address conflicts
- ✅ You need more than 2 ToF sensors

## Migration Scenarios

### Scenario 1: You Keep Original `oled.py` (SIMPLEST)

**When to use:** OLED stays on main bus permanently

**Pros:**
- No code changes needed
- Simple and familiar
- Works perfectly for main bus

**Cons:**
- Won't work if you move OLED to multiplexer later
- Less error handling

**Code:**
```python
from components.screens import oled

if oled.initialize_display():
    oled.update_display(header="Robot", text="Ready")
```

### Scenario 2: You Switch to `oled_mux.py` (RECOMMENDED)

**When to use:** You want flexibility for future changes

**Pros:**
- Works on both main bus AND multiplexer
- Better error handling
- Proper cleanup
- Future-proof

**Cons:**
- Need to update imports (one-line change)
- Need to specify `use_multiplexer=False`

**Code:**
```python
from components.screens import oled_mux

if oled_mux.initialize_display(use_multiplexer=False):
    oled_mux.update_display(header="Robot", text="Ready")
    oled_mux.close_display()
```

### Scenario 3: Keep Both Modules

**When to use:** Different scripts need different setups

**Approach:**
- Use `oled.py` in scripts where OLED is on main bus
- Use `oled_mux.py` in scripts where OLED is on multiplexer
- No conflicts - they're separate modules

## Will `oled_mux.py` Affect Your Original Setup?

### Short Answer: **NO** - It won't affect anything!

### Why Not?

1. **`oled_mux.py` is a separate file**
   - Your original `oled.py` is unchanged
   - Both can coexist peacefully
   - You choose which one to import

2. **When `use_multiplexer=False`, it works exactly like the original**
   ```python
   # This behaves EXACTLY like original oled.py
   oled_mux.initialize_display(use_multiplexer=False)
   ```

3. **Same API for display updates**
   ```python
   # These work the same in both modules
   oled_mux.update_display(header="X", text="Y")
   oled.update_display(header="X", text="Y")
   ```

4. **The initialization code does the same thing**
   
   **Original `oled.py`:**
   ```python
   i2c = busio.I2C(board.SCL, board.SDA)
   display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
   ```
   
   **`oled_mux.py` with `use_multiplexer=False`:**
   ```python
   # Same exact code when multiplexer is disabled!
   i2c = busio.I2C(board.SCL, board.SDA)
   display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
   ```

## Recommended Approach for Your Setup

Since you're moving OLED to the main bus, I recommend:

### Option A: Keep Using Original `oled.py` (Easiest)

**No changes needed!** Your existing code will work perfectly.

```python
# Your existing code - NO CHANGES NEEDED
from components.screens import oled

if oled.initialize_display():
    oled.update_display(header="Status", text="Active")
```

### Option B: Migrate to `oled_mux.py` (Better Long-term)

**One-line change per file:**

```python
# Before
from components.screens import oled
if oled.initialize_display():
    oled.update_display(header="Status", text="Active")

# After (just change import and add use_multiplexer=False)
from components.screens import oled_mux
if oled_mux.initialize_display(use_multiplexer=False):
    oled_mux.update_display(header="Status", text="Active")
    oled_mux.close_display()  # Add cleanup
```

**Benefits:**
- ✅ Better error handling
- ✅ Proper resource cleanup
- ✅ Can easily switch to multiplexer later if needed
- ✅ More robust and maintainable

## Testing Your Setup

### Step 1: Verify OLED is on Main Bus

```bash
# Should show OLED at 0x3C (or 0x3D)
i2cdetect -y 1
```

Expected output:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --  ← OLED
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --  ← MPU6050
70: 70 -- -- -- -- -- -- --                          ← Multiplexer
```

### Step 2: Test Original Module (if keeping it)

```bash
python3 -c "from components.screens import oled; oled.initialize_display()"
```

### Step 3: Test New Module on Main Bus

```bash
python3 test_oled_main_bus.py
```

### Step 4: Choose Your Approach

- **Keep original** → No changes needed! ✅
- **Migrate to new** → Update imports in your code

## Example: Updating Your Application

### Find Files Using OLED

```bash
# Find all Python files that import oled
grep -r "from components.screens import oled" . --include="*.py"
grep -r "import components.screens.oled" . --include="*.py"
```

### Update Each File

**If you choose to migrate:**

```bash
# Example: Update a file
sed -i.bak 's/from components.screens import oled/from components.screens import oled_mux as oled/g' your_file.py
```

Or manually edit each file:

```python
# Change this line:
from components.screens import oled

# To this:
from components.screens import oled_mux as oled
```

Then add initialization parameter:
```python
# Change this:
oled.initialize_display()

# To this:
oled.initialize_display(use_multiplexer=False)
```

## Summary Table

| Your Choice | Pros | Cons | Effort |
|-------------|------|------|--------|
| **Keep original `oled.py`** | ✅ No changes<br>✅ Works perfectly<br>✅ Simple | ⚠️ Main bus only<br>⚠️ Less robust | ⭐ None |
| **Switch to `oled_mux.py`** | ✅ Future-proof<br>✅ Better errors<br>✅ Cleanup<br>✅ Both modes | ⚠️ Need to update imports | ⭐⭐ Low |
| **Keep both available** | ✅ Maximum flexibility<br>✅ Use right tool for job | ⚠️ Two modules to maintain | ⭐ None |

## Quick Reference Cards

### Original Module (`oled.py`)
```python
from components.screens import oled

# Initialize
oled.initialize_display()

# Update
oled.update_display(
    header="Title",
    text="Message",
    icon='rectangle'
)
```

### New Module on Main Bus (`oled_mux.py`)
```python
from components.screens import oled_mux

# Initialize on main bus
oled_mux.initialize_display(use_multiplexer=False)

# Update (same API!)
oled_mux.update_display(
    header="Title",
    text="Message",
    icon='rectangle'
)

# Cleanup
oled_mux.close_display()
```

### New Module with Multiplexer (`oled_mux.py`)
```python
from components.screens import oled_mux

# Initialize through multiplexer (auto-detect channel)
oled_mux.initialize_display(use_multiplexer=True)

# Or specify channel
oled_mux.initialize_display(use_multiplexer=True, channel=2)

# Update (same API!)
oled_mux.update_display(
    header="Title",
    text="Message"
)

# Cleanup
oled_mux.close_display()
```

## Recommendation

For your setup (OLED on main bus), I recommend:

1. **Short term:** Keep using original `oled.py` - it works perfectly! ✅
2. **Long term:** Consider migrating to `oled_mux.py` for better robustness
3. **Flexibility:** Keep both modules available - use the right tool for each situation

**Bottom line:** The new module **won't break anything** - it's completely optional and fully compatible with your setup!

---

**Last Updated:** March 13, 2026  
**Your Setup:** OLED on main I2C bus (direct connection)  
**Recommendation:** Keep original `oled.py` or migrate gradually
