# Development Workflow Guide

**Project:** PiCrawler Robot  
**Date:** March 17, 2026  
**Purpose:** Complete guide for managing development and production branches

---

## 🌳 Branch Structure

```
Repository: github.com/oetapia/picrawler

├── v3.0 (production) ← Deploy to Raspberry Pi
│   ├── 62 Python files (3.5MB)
│   ├── Production-ready code only
│   └── No diagnostic/test files
│
└── dev (development) ← Active development
    ├── 80 Python files (3.9MB)
    ├── All production code
    ├── 18 diagnostic tools
    └── Development documentation
```

---

## 📋 Quick Reference

| Branch | Purpose | Size | Files | Deploy to Robot? |
|--------|---------|------|-------|------------------|
| **v3.0** | Production | 3.5MB | 62 .py | ✅ Yes |
| **dev** | Development | 3.9MB | 80 .py | ❌ No |

---

## 🚀 Daily Development Workflow

### 1. Start Your Day

```bash
# Switch to dev branch
git checkout dev

# Pull latest changes
git pull origin dev

# Verify you're on dev
git branch --show-current
# Should show: dev
```

### 2. Make Changes

```bash
# Edit files, test, iterate
code components/sensors/new_feature.py

# ⚠️ IMPORTANT: Fix encoding for robot compatibility
python3 tools/fix_encoding.py components/sensors/new_feature.py

# Test with diagnostic tools
python3 components/sensors/sensor_diagnostic.py

# Run production code to verify
python3 components/sensors/accelerometer.py
```

**Note:** Always run `fix_encoding.py` on Python files destined for the robot to ensure ASCII-only encoding.

### 3. Commit to Dev

```bash
# Stage changes (pre-commit hook will auto-fix encoding)
git add components/sensors/new_feature.py

# Commit with descriptive message
git commit -m "Add new sensor feature: [description]"

# Push to dev branch
git push origin dev
```

**Note:** The pre-commit hook automatically runs `fix_encoding.py` on staged Python files.

### 4. When Ready for Production

```bash
# Use migration tool (interactive mode)
python3 tools/pass_to_prod.py

# Or specific file
python3 tools/pass_to_prod.py --file components/sensors/new_feature.py

# Or entire module
python3 tools/pass_to_prod.py --module components/sensors
```

---

## 🔧 Encoding Management

### Why Encoding Matters

The Raspberry Pi robot cannot handle Unicode characters. All Python files must use ASCII-only encoding to prevent `charmap codec` errors.

### Tools Available

```bash
# Check encoding issues (dry-run)
make encoding-check

# Fix encoding issues
make encoding-fix

# Or use the script directly
python3 tools/fix_encoding.py components/sensors/new_file.py

# Fix entire directory
python3 tools/fix_encoding.py components/
```

### Automatic Fixes

The pre-commit git hook automatically:
- Checks all staged Python files for encoding issues
- Fixes Unicode characters automatically
- Re-stages the fixed files
- Continues with the commit

### What Gets Fixed

- **Smart quotes** `" "` → `" "`
- **Emojis** `✅ ❌` → `[EMOJI]`
- **Special symbols** `→` → `->`
- **Bullets** `•` → `*`
- **Degree symbols** `°` → ` deg`

See **AI_CODING_GUIDELINES.md** for complete details.

---

## 🔧 Using Diagnostic Tools

### Available Diagnostics

See **DIAGNOSTIC_TOOLS.md** for complete inventory.

**Quick Tests:**
```bash
# Test accelerometer
python3 components/sensors/accel_diagnostic.py

# Test IR floor sensors
python3 components/sensors/ir_diagnostic.py

# Test ToF distance sensors
python3 components/sensors/tof_diagnostic.py

# Test OLED display
python3 components/screens/oled_diagnostic.py

# Test camera
python3 components/camera/camera_diagnostic.py

# Test I2C multiplexer
python3 components/sensors/pca9548a_diagnostic.py
```

### Before Hardware Changes
```bash
# Establish baseline
python3 components/sensors/[sensor]_diagnostic.py > baseline.txt

# Make hardware change

# Re-test and compare
python3 components/sensors/[sensor]_diagnostic.py > after.txt
diff baseline.txt after.txt
```

---

## 📦 Migration Tool: pass_to_prod.py

### Overview

The `pass_to_prod.py` script safely migrates production-ready code from `dev` to `v3.0` while automatically excluding development files.

**Automatically Excludes:**
- `*diagnostic*.py` files
- `test_*.py` files
- `*.backup` files
- `*_GUIDE.md` documentation
- `*_TROUBLESHOOTING.md` files
- `__pycache__` directories

### Usage Modes

**1. Interactive Mode (Recommended)**
```bash
python3 tools/pass_to_prod.py

# You'll see menu:
# 1. Specific file
# 2. Entire module
# 3. All production files
# 4. Exit
```

**2. Dry-Run Mode (Preview Only)**
```bash
# Preview what would be migrated
python3 tools/pass_to_prod.py --dry-run --all
python3 tools/pass_to_prod.py --dry-run --module components/sensors
```

**3. Specific File**
```bash
python3 tools/pass_to_prod.py --file components/sensors/accelerometer.py
```

**4. Entire Module**
```bash
python3 tools/pass_to_prod.py --module components/sensors
python3 tools/pass_to_prod.py --module self_aware
```

**5. All Production Files**
```bash
# Migrate everything (use with caution!)
python3 tools/pass_to_prod.py --all
```

### Migration Process

When you run the tool:

1. **Preview** - Shows what will be migrated
2. **Confirmation** - Type 'yes' to proceed
3. **Stash** - Saves uncommitted dev changes
4. **Switch** - Checks out v3.0 branch
5. **Copy** - Migrates files from dev
6. **Commit** - Creates commit on v3.0
7. **Return** - Switches back to dev
8. **Restore** - Restores stashed changes

### Safety Features

✅ **Must be on dev branch** - Won't run from other branches  
✅ **Confirmation required** - No accidental migrations  
✅ **Auto-excludes** - Diagnostic files never migrate  
✅ **Dry-run mode** - Preview without changes  
✅ **Stash/restore** - Preserves uncommitted work

---

## 🎯 Common Scenarios

### Scenario 1: New Sensor Added

```bash
# 1. On dev branch
git checkout dev

# 2. Create and test sensor
code components/sensors/new_sensor.py

# 3. Fix encoding (IMPORTANT for robot!)
python3 tools/fix_encoding.py components/sensors/new_sensor.py

# 4. Test sensor
python3 components/sensors/new_sensor.py

# 5. Create diagnostic tool
code components/sensors/new_sensor_diagnostic.py
python3 tools/fix_encoding.py components/sensors/new_sensor_diagnostic.py
python3 components/sensors/new_sensor_diagnostic.py  # Test diagnostic

# 6. Commit to dev (pre-commit hook will double-check encoding)
git add components/sensors/new_sensor.py
git add components/sensors/new_sensor_diagnostic.py
git commit -m "Add new sensor with diagnostic"
git push origin dev

# 7. Migrate only production file to v3.0
python3 tools/pass_to_prod.py --file components/sensors/new_sensor.py

# 8. Push v3.0 (after migration tool switches back to dev)
git checkout v3.0
git push origin v3.0
git checkout dev
```

**Result:**
- `dev`: Has both new_sensor.py AND new_sensor_diagnostic.py
- `v3.0`: Has only new_sensor.py (production clean)

---

### Scenario 2: Bug Fix in Production Code

```bash
# 1. Fix on dev branch
git checkout dev
code components/navigation/motion_controller.py  # Fix bug
python3 components/navigation/motion_controller.py  # Test fix

# 2. Commit to dev
git add components/navigation/motion_controller.py
git commit -m "Fix: Motion controller speed ramping issue"
git push origin dev

# 3. Migrate to v3.0
python3 tools/pass_to_prod.py --file components/navigation/motion_controller.py

# 4. Push v3.0
git checkout v3.0
git push origin v3.0
git checkout dev
```

---

### Scenario 3: Major Module Update

```bash
# 1. Update entire sensors module on dev
git checkout dev
# ... make changes to multiple sensor files ...
# ... test each sensor ...

# 2. Commit all changes
git add components/sensors/
git commit -m "Update: Complete sensors module refactor"
git push origin dev

# 3. Preview migration
python3 tools/pass_to_prod.py --dry-run --module components/sensors

# 4. Migrate entire module
python3 tools/pass_to_prod.py --module components/sensors

# 5. Push v3.0
git checkout v3.0
git push origin v3.0
git checkout dev
```

---

### Scenario 4: Deploy to Raspberry Pi

```bash
# On Raspberry Pi

# First time setup
cd ~
git clone https://github.com/oetapia/picrawler.git
cd picrawler
git checkout v3.0

# Regular updates
cd ~/picrawler
git checkout v3.0
git pull origin v3.0

# Run autonomous mode
python3 self_aware/autonomous_navigator.py
```

---

## 📊 Branch Comparison

### What's in Each Branch?

**v3.0 (Production):**
```
✅ components/ (62 production .py files)
✅ manual_control/ (production scripts)
✅ self_aware/ (autonomous navigator)
✅ picrawler/ (factory core)
❌ No diagnostic files
❌ No test files
❌ No backup files
❌ No verbose documentation
```

**dev (Development):**
```
✅ Everything from v3.0
✅ 18 diagnostic tools
✅ Development guides
✅ Test scripts
✅ Backup files for reference
✅ Full documentation
```

### File Count

```bash
# Check production files
git checkout v3.0
find components manual_control self_aware -name "*.py" | wc -l
# Output: 62 files

# Check dev files
git checkout dev
find components manual_control self_aware -name "*.py" | wc -l
# Output: 80 files (62 production + 18 development)
```

---

## 🔍 Verification Commands

### Verify Branch Status

```bash
# Check current branch
git branch --show-current

# Check branch file count
find components manual_control self_aware -name "*.py" | wc -l

# Check for diagnostic files
find . -name "*diagnostic*.py" | wc -l
# v3.0: Should be 0
# dev: Should be 11

# Check branch size
du -sh components manual_control self_aware
# v3.0: ~3.5MB
# dev: ~3.9MB
```

### Verify Clean Production

```bash
# On v3.0, these should return 0
git checkout v3.0
find . -name "*.backup" | wc -l
find . -name "*diagnostic*" | wc -l
find . -name "test_*.py" | wc -l
find . -name "*_GUIDE.md" | wc -l
```

---

## ⚠️ Important Rules

### DO:
✅ **Always develop on dev branch**  
✅ **Run fix_encoding.py on all Python files for robot**  
✅ **Test with diagnostic tools before migrating**  
✅ **Use pass_to_prod.py for migrations**  
✅ **Preview with --dry-run first**  
✅ **Keep diagnostic files in dev only**  
✅ **Commit to dev frequently**  
✅ **Deploy v3.0 to robot**

### DON'T:
❌ **Never develop directly on v3.0**  
❌ **Never manually copy files between branches**  
❌ **Never commit diagnostic files to v3.0**  
❌ **Never deploy dev branch to robot**  
❌ **Never skip testing before migration**  
❌ **Never commit Unicode characters to robot code**

---

## 🐛 Troubleshooting

### "Must be on dev branch"
```bash
# Solution: Switch to dev
git checkout dev
```

### "No files to migrate"
```bash
# Check if file exists
ls -la components/sensors/myfile.py

# Verify file is not a diagnostic
# (diagnostic files are auto-excluded)
```

### "Failed to checkout v3.0"
```bash
# Check if v3.0 branch exists
git branch -a | grep v3.0

# If missing, create it
git checkout -b v3.0 origin/v3.0
```

### "Uncommitted changes"
```bash
# Migration tool auto-stashes, but you can manually:
git stash
# Run migration
git stash pop
```

### Accidentally committed diagnostic to v3.0
```bash
# Remove from v3.0
git checkout v3.0
git rm components/sensors/diagnostic_file.py
git commit -m "Remove diagnostic file from production"
git push origin v3.0

# Diagnostic still safe in dev branch
git checkout dev
ls components/sensors/diagnostic_file.py
```

---

## 📝 Best Practices

### 1. Test Before Migrating
```bash
# Always run diagnostic first
python3 components/sensors/sensor_diagnostic.py

# Then test production code
python3 components/sensors/sensor.py

# Only then migrate
python3 tools/pass_to_prod.py --file components/sensors/sensor.py
```

### 2. Small, Incremental Migrations
```bash
# GOOD: Migrate one feature at a time
python3 tools/pass_to_prod.py --file components/sensors/new_sensor.py

# RISKY: Migrate everything at once
# python3 tools/pass_to_prod.py --all  (use sparingly)
```

### 3. Keep Dev Branch Updated
```bash
# Daily sync
git checkout dev
git pull origin dev
```

### 4. Document Changes
```bash
# Good commit messages
git commit -m "Add: New distance sensor with ToF support"
git commit -m "Fix: IR sensor calibration threshold"
git commit -m "Update: Motion controller speed ramping"
```

### 5. Use Dry-Run
```bash
# Always preview large migrations
python3 tools/pass_to_prod.py --dry-run --module components/sensors
```

---

## 📚 Related Documentation

- **AI_CODING_GUIDELINES.md** - Critical encoding requirements for AI assistants
- **DIAGNOSTIC_TOOLS.md** - Complete diagnostic tools inventory
- **PRODUCTION_SETUP_V3.md** - Production deployment guide
- **CUSTOM_MODULES_MANIFEST.md** - Complete file inventory
- **V4_MIGRATION_GUIDE.md** - Future migration template
- **tools/fix_encoding.py** - Encoding fix script source

---

## 🎓 Learning Path

### For New Developers

1. **Week 1: Explore dev branch**
   ```bash
   git checkout dev
   python3 components/sensors/accel_diagnostic.py
   python3 components/sensors/ir_diagnostic.py
   ```

2. **Week 2: Make small changes**
   ```bash
   # Edit a file, test it
   code components/utils/display.py
   python3 components/utils/display.py
   ```

3. **Week 3: Use migration tool**
   ```bash
   # Dry-run first
   python3 tools/pass_to_prod.py --dry-run --file components/utils/display.py
   # Then real migration
   python3 tools/pass_to_prod.py --file components/utils/display.py
   ```

4. **Week 4: Deploy to robot**
   ```bash
   # On Raspberry Pi
   cd ~/picrawler
   git pull origin v3.0
   ```

---

## 🔗 Quick Command Reference

```bash
# Branch management
git checkout dev              # Switch to development
git checkout v3.0             # Switch to production
git branch --show-current     # Check current branch

# Encoding Management (NEW!)
make encoding-check           # Check for encoding issues
make encoding-fix             # Fix encoding issues
python3 tools/fix_encoding.py components/  # Fix specific directory
make clean                    # Remove backup files

# Development
python3 components/sensors/[sensor]_diagnostic.py  # Test sensor
git add .                     # Stage changes
git commit -m "Message"       # Commit (auto-fixes encoding)
git push origin dev           # Push to dev

# Migration
python3 tools/pass_to_prod.py                      # Interactive
python3 tools/pass_to_prod.py --dry-run --all      # Preview all
python3 tools/pass_to_prod.py --file path/to/file  # Migrate file
python3 tools/pass_to_prod.py --module components/sensors  # Migrate module

# Verification
find . -name "*.py" | wc -l   # Count Python files
du -sh components/            # Check size
git status                    # Check status
```

---

**Last Updated:** March 17, 2026  
**Branch:** dev  
**Status:** Active development workflow

**Questions?** Review DIAGNOSTIC_TOOLS.md or check git history.
