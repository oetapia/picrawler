# AI Coding Guidelines for PiCrawler

**Critical Instructions for AI Assistants (Q, Claude, ChatGPT, Copilot, etc.)**

---

## 🚨 MANDATORY: Encoding Fix Requirement

### **RULE #1: Always Run fix_encoding.py After Creating/Modifying Python Files**

**Why:** The Raspberry Pi robot cannot handle Unicode characters. All Python files must use ASCII-only characters to prevent `charmap codec` errors during execution on the robot.

### When to Run

Run `tools/fix_encoding.py` after:
- ✅ Creating any new `.py` file
- ✅ Modifying existing `.py` files with Unicode characters
- ✅ Copy-pasting code that may contain smart quotes
- ✅ Generating code with emojis or special symbols
- ✅ Editing docstrings or comments with Unicode

### How to Run

```bash
# Single file
python3 tools/fix_encoding.py path/to/file.py

# Entire directory
python3 tools/fix_encoding.py components/

# Dry-run (preview changes)
python3 tools/fix_encoding.py components/ --dry-run

# Without backup
python3 tools/fix_encoding.py path/to/file.py --no-backup
```

### What It Fixes

The script automatically replaces:
- **Smart quotes** `" "` → `" "`
- **Emojis** `✅ ❌ 🚀` → `[EMOJI]`
- **Special arrows** `→ ←` → `-> <-`
- **Bullets** `•` → `*`
- **Degree symbols** `°` → ` deg`
- **Math symbols** `±` → `+/-`

---

## 🤖 AI Assistant Workflow

### Step-by-Step Process

**1. Before Writing Code:**
```
- Review existing code style
- Note if file is production or diagnostic
- Check for encoding requirements
```

**2. While Writing Code:**
```
- Use standard ASCII quotes: " and '
- Avoid emojis in code or comments
- Use ASCII arrows: -> instead of →
- Use standard bullets: * instead of •
```

**3. After Writing Code:**
```
✅ MANDATORY: Run fix_encoding.py
✅ Test the code
✅ Verify no encoding errors
✅ Commit changes
```

### Example Workflow

```bash
# 1. Create new sensor file
cat > components/sensors/new_sensor.py << 'EOF'
#!/usr/bin/env python3
"""New sensor module with proper encoding"""

class NewSensor:
    def __init__(self):
        print("Initializing sensor")
EOF

# 2. ⚠️ MANDATORY: Run encoding fix
python3 tools/fix_encoding.py components/sensors/new_sensor.py

# 3. Test the file
python3 components/sensors/new_sensor.py

# 4. Commit
git add components/sensors/new_sensor.py
git commit -m "Add new sensor with ASCII encoding"
```

---

## 📋 Pre-Flight Checklist

Before completing ANY task that creates/modifies Python files:

- [ ] All `.py` files have been processed with `fix_encoding.py`
- [ ] No Unicode characters remain in code destined for robot
- [ ] Files have been tested locally if possible
- [ ] Git commit includes encoding-fixed versions

---

## 🎯 File Type Guidelines

### Production Files (Will run on robot)
**Location:** `components/`, `manual_control/`, `self_aware/`, `picrawler/`  
**Encoding:** ✅ **MUST run fix_encoding.py**  
**Reason:** Robot Pi cannot handle Unicode

### Diagnostic Files (Dev-only)
**Location:** `*diagnostic*.py`, `test_*.py`  
**Encoding:** ⚠️ **SHOULD run fix_encoding.py** (best practice)  
**Reason:** Good practice, but won't deploy to robot

### Tool Scripts (Dev machine)
**Location:** `tools/`, `examples/`  
**Encoding:** ℹ️ **OPTIONAL** (if only used on dev machine)  
**Reason:** Dev machines can handle Unicode

---

## 🔧 Quick Reference Commands

### Check for Unicode Issues

```bash
# Find files with Unicode quotes
grep -r '"' components/ --include="*.py"

# Find files with emojis
grep -r '[^\x00-\x7F]' components/ --include="*.py"
```

### Batch Fix All Python Files

```bash
# Fix all components
python3 tools/fix_encoding.py components/

# Fix manual control
python3 tools/fix_encoding.py manual_control/

# Fix self-aware module
python3 tools/fix_encoding.py self_aware/

# Fix everything (use with caution)
find . -name "*.py" -not -path "*/\.*" -exec python3 tools/fix_encoding.py {} \;
```

### Verify Fixes

```bash
# Count backup files (indicates files were fixed)
find components/ -name "*.backup" | wc -l

# Check a file was processed
ls -la components/sensors/sensor.py.backup  # Should exist if processed
```

---

## 💡 Best Practices for AI Assistants

### 1. **Automatic Reminder**
After creating ANY Python file, immediately suggest:
```bash
python3 tools/fix_encoding.py <path_to_new_file>
```

### 2. **Batch Processing**
When creating multiple files, fix them all at once:
```bash
python3 tools/fix_encoding.py components/sensors/
```

### 3. **Include in Response**
Always include encoding fix command in your final response:
```
✅ Files created
⚠️ Run encoding fix: python3 tools/fix_encoding.py components/
✅ Ready for deployment
```

### 4. **Documentation**
When adding code examples to docs, use ASCII-only:
```
GOOD: print("Hello -> World")
BAD:  print("Hello → World")

GOOD: # * Important note
BAD:  # • Important note
```

---

## 🚀 Integration with Development Workflow

### New Feature Development

```bash
# 1. Create feature on dev branch
git checkout dev
code components/navigation/new_feature.py

# 2. ⚠️ MANDATORY: Fix encoding
python3 tools/fix_encoding.py components/navigation/new_feature.py

# 3. Test locally
python3 components/navigation/new_feature.py

# 4. Commit
git add components/navigation/new_feature.py
git commit -m "Add new navigation feature (ASCII encoded)"

# 5. Migrate to production
python3 tools/pass_to_prod.py --file components/navigation/new_feature.py
```

### Bug Fix

```bash
# 1. Fix bug
git checkout dev
code components/sensors/accelerometer.py

# 2. ⚠️ MANDATORY: Fix encoding
python3 tools/fix_encoding.py components/sensors/accelerometer.py

# 3. Test
python3 components/sensors/accelerometer.py

# 4. Commit and migrate
git add components/sensors/accelerometer.py
git commit -m "Fix accelerometer calibration (ASCII encoded)"
python3 tools/pass_to_prod.py --file components/sensors/accelerometer.py
```

---

## ⚠️ Common Pitfalls

### ❌ Don't Do This:
```python
# Using smart quotes (from copy-paste)
print("Hello World")  # ← These are Unicode quotes!

# Using emojis
status = "✅ Success"  # ← Will break on robot!

# Using Unicode symbols
direction = "Move → Forward"  # ← Will break on robot!
```

### ✅ Do This Instead:
```python
# Using standard ASCII quotes
print("Hello World")  # ← Standard quotes

# Using ASCII equivalents
status = "[OK] Success"  # ← ASCII-safe

# Using ASCII arrows
direction = "Move -> Forward"  # ← ASCII-safe
```

---

## 📊 Verification Matrix

| File Type | Run fix_encoding.py? | Deploy to Robot? | Priority |
|-----------|---------------------|------------------|----------|
| components/*.py | ✅ **MANDATORY** | Yes | 🔴 Critical |
| manual_control/*.py | ✅ **MANDATORY** | Yes | 🔴 Critical |
| self_aware/*.py | ✅ **MANDATORY** | Yes | 🔴 Critical |
| picrawler/*.py | ✅ **MANDATORY** | Yes | 🔴 Critical |
| *diagnostic*.py | ⚠️ **RECOMMENDED** | No | 🟡 Medium |
| test_*.py | ⚠️ **RECOMMENDED** | No | 🟡 Medium |
| tools/*.py | ℹ️ **OPTIONAL** | No | 🟢 Low |
| examples/*.py | ℹ️ **OPTIONAL** | Maybe | 🟢 Low |

---

## 🎓 Training Examples

### Example 1: Creating New Sensor

**Task:** Create a new ultrasonic sensor module

**AI Response Should Include:**

```python
# File: components/sensors/ultrasonic_sensor.py
# (code here)
```

**Then IMMEDIATELY suggest:**
```bash
# ⚠️ IMPORTANT: Fix encoding for robot compatibility
python3 tools/fix_encoding.py components/sensors/ultrasonic_sensor.py

# Verify the file
python3 components/sensors/ultrasonic_sensor.py
```

### Example 2: Updating Multiple Files

**Task:** Update all sensor files with new logging

**AI Response Should Include:**

1. Make changes to files
2. Then run batch encoding fix:
```bash
# ⚠️ IMPORTANT: Fix encoding for ALL modified sensors
python3 tools/fix_encoding.py components/sensors/

# This will fix:
# - accelerometer.py
# - distance_sensor.py
# - ir_distance.py
# (and all others in the directory)
```

### Example 3: Copy-Paste from Documentation

**Task:** Add code from external docs

**AI Should:**
1. ✅ Review code for Unicode characters
2. ✅ Replace smart quotes with standard quotes
3. ✅ Remove emojis
4. ✅ Run fix_encoding.py to catch anything missed

---

## 🔍 Self-Check Questions for AI

Before completing a task, ask:

1. ✅ Did I create or modify any `.py` files?
2. ✅ Are these files destined for the robot?
3. ✅ Did I run `fix_encoding.py` on them?
4. ✅ Did I mention this in my response?
5. ✅ Did I verify the files are ASCII-clean?

**If any answer is NO, go back and fix it!**

---

## 📝 Template Response

When creating Python files, include this in your response:

```markdown
## Files Created

1. `components/sensors/new_sensor.py` - New sensor module
2. `components/sensors/new_sensor_diagnostic.py` - Diagnostic tool

## ⚠️ IMPORTANT: Encoding Fix Required

Please run the following command to ensure robot compatibility:

```bash
python3 tools/fix_encoding.py components/sensors/
```

This will:
- Replace Unicode quotes with ASCII quotes
- Remove emojis and special characters
- Create backups of original files

## Next Steps

1. Run encoding fix (command above)
2. Test the sensor: `python3 components/sensors/new_sensor.py`
3. Commit changes: `git add . && git commit -m "Add new sensor"`
4. Migrate to production: `python3 tools/pass_to_prod.py --file components/sensors/new_sensor.py`
```

---

## 🎯 Summary

### The Golden Rule for AI Assistants:

**"If it's Python code that will run on the robot, run fix_encoding.py on it!"**

### Quick Command:
```bash
python3 tools/fix_encoding.py <file_or_directory>
```

### Remember:
- ✅ Always suggest this command
- ✅ Include it in task completion
- ✅ Verify it's been run before marking task complete
- ✅ Explain WHY it's necessary (robot limitation)

---

**Last Updated:** March 17, 2026  
**For:** AI Assistants working on PiCrawler project  
**Priority:** 🔴 **CRITICAL** - Encoding fixes are mandatory for robot deployment

**Questions?** See `tools/fix_encoding.py` source code or `DEV_WORKFLOW.md`
