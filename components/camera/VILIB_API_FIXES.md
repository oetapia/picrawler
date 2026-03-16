# Vilib API Fixes

## Summary
Fixed incorrect vilib API function names in `components/camera/vilib_detector.py` that were causing AttributeError exceptions on Raspberry Pi.

## Date
2026-03-14

## Errors Fixed

### 1. Face Detection API ✅
**Error:**
```
AttributeError: vilib has no attribute 'face_detect_switch', did you mean 'face_detect_func'
```

**Fix:**
- Changed `Vilib.face_detect_switch(True)` → `Vilib.face_detect_func(True)`
- Changed `Vilib.face_detect_switch(False)` → `Vilib.face_detect_func(False)`

**Locations:**
- Line ~268: `enable_face_detection()` method
- Line ~272: `disable_face_detection()` method

### 2. Traffic Sign Detection API ✅
**Error:**
```
AttributeError: vilib has no attribute 'traffic_sign_detect_switch', did you mean 'traffic_detect_switch'
```

**Fix:**
- Changed `Vilib.traffic_sign_detect_switch(True)` → `Vilib.traffic_detect_switch(True)`
- Changed `Vilib.traffic_sign_detect_switch(False)` → `Vilib.traffic_detect_switch(False)`

**Locations:**
- Line ~385: `enable_traffic_sign_detection()` method
- Line ~389: `disable_traffic_sign_detection()` method

### 3. QR Code Detection ⚠️ (Vilib Library Bug)
**Error:**
```
AttributeError: type object 'Vilib' has no attribute 'qrcode_recognize'
Exception in thread vilib at /usr/local/lib/.../vilib.py line 272
```

**Status:** This is a **bug in the vilib library itself**, not in our code.

**Our Code (Correct):**
- Enable: `Vilib.qrcode_detect_switch(True)` ✅
- Disable: `Vilib.qrcode_detect_switch(False)` ✅
- Get data: `Vilib.detect_obj_parameter['qr_data']` ✅

**Vilib Library Bug:**
The vilib library internally tries to call `vilib.qrcode_recognize()` which doesn't exist. This happens inside the vilib threading code when QR detection is enabled.

**Workaround:** Use the `--skip qr` parameter to avoid this test.

## Affected Files
- ✅ `components/camera/vilib_detector.py` - Core detection module (FIXED)
- ✅ `components/camera/camera_diagnostic.py` - Diagnostic tool (FIXED + added --skip feature)

## Testing on Raspberry Pi

### Run All Tests (Skip Broken QR Detection)
```bash
python components/camera/camera_diagnostic.py --skip qr
```

### Run Specific Tests
```bash
# Face detection only
python components/camera/camera_diagnostic.py --mode face

# Traffic sign detection only
python components/camera/camera_diagnostic.py --mode traffic

# Object detection only
python components/camera/camera_diagnostic.py --mode object

# All tests with custom duration
python components/camera/camera_diagnostic.py --skip qr -d 15
```

### Skip Multiple Tests
```bash
# Skip QR and image classification
python components/camera/camera_diagnostic.py --skip qr classify
```

## Correct Vilib API Reference

Based on these fixes and testing, here are the correct vilib API calls:

```python
# Face Detection
Vilib.face_detect_func(True/False)

# Traffic Sign Detection  
Vilib.traffic_detect_switch(True/False)

# QR Code Detection (has library bug - use with caution)
Vilib.qrcode_detect_switch(True/False)
Vilib.detect_obj_parameter['qr_data']

# Object Detection
Vilib.object_detect_switch(True/False)

# Image Classification
Vilib.image_classify_switch(True/False)

# Color Detection
Vilib.color_detect('red'/'orange'/'yellow'/'green'/'blue'/'purple'/'close')
```

## New --skip Parameter

The camera diagnostic tool now supports skipping problematic tests:

```bash
# Skip single test
python components/camera/camera_diagnostic.py --skip qr

# Skip multiple tests  
python components/camera/camera_diagnostic.py --skip qr classify

# Available options: color, face, qr, object, traffic, classify
```

This allows you to:
- Avoid tests that crash due to vilib bugs
- Test only specific functionality
- Speed up diagnostics by skipping unnecessary tests

## Known Issues

### QR Code Detection (Vilib Library Bug)
- **Problem:** Internal vilib library bug calling non-existent `qrcode_recognize()` function
- **Impact:** Crashes the vilib thread when QR detection is enabled
- **Workaround:** Use `--skip qr` parameter
- **Resolution:** Needs to be fixed in the vilib library upstream

## Additional Notes

These errors were likely introduced due to:
1. Changes in the vilib API between versions
2. Inconsistent naming conventions in vilib documentation
3. Bugs in the vilib library implementation itself (QR code)

The fixes align with the actual vilib library implementation as discovered through error messages and testing.
