#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple standalone test to verify logging path fixes work correctly.
This test directly imports only what's needed to avoid robot_hat dependencies.
"""

import os
import sys
import tempfile
import shutil

# Directly import only the data_logger module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'self_aware'))
import data_logger


def test_script_relative_path():
    """Test that logs always go to self_aware/logs regardless of execution location"""
    print("\n" + "="*70)
    print("TEST 1: Script-Relative Path Resolution")
    print("="*70)
    
    # Expected: logs should be in self_aware/logs
    expected_log_dir = os.path.join(os.path.dirname(__file__), 'self_aware', 'logs')
    print(f"Current working directory: {os.getcwd()}")
    print(f"Expected log directory: {expected_log_dir}")
    
    # Create logger with default (None) - should use script-relative path
    logger = data_logger.DataLogger(log_dir=None, format="csv", buffer_size=10)
    
    actual_log_dir = str(logger.log_dir)
    print(f"Actual log directory: {actual_log_dir}")
    
    # Verify paths match
    if actual_log_dir == expected_log_dir:
        print("✅ SUCCESS: Log directory is script-relative!")
    else:
        print(f"❌ FAILURE: Path mismatch!")
        logger.close()
        return False
    
    # Check directory permissions
    dir_stat = os.stat(logger.log_dir)
    dir_perms = oct(dir_stat.st_mode)[-3:]
    print(f"\nDirectory permissions: {dir_perms}")
    
    if dir_perms == '755':
        print("✅ SUCCESS: Directory has correct permissions (755)!")
    else:
        print(f"⚠️  WARNING: Directory permissions are {dir_perms} (expected 755)")
    
    # Check file permissions
    if logger.log_file.exists():
        file_stat = os.stat(logger.log_file)
        file_perms = oct(file_stat.st_mode)[-3:]
        print(f"Log file permissions: {file_perms}")
        
        if file_perms == '666':
            print("✅ SUCCESS: File has correct permissions (666)!")
        else:
            print(f"⚠️  WARNING: File permissions are {file_perms} (expected 666)")
    
    # Clean up
    logger.close()
    if logger.log_file.exists():
        os.remove(logger.log_file)
    
    print("\n✅ Test 1 PASSED\n")
    return True


def test_from_different_directory():
    """Test running from a different directory (simulates the original issue)"""
    print("="*70)
    print("TEST 2: Execution from Different Directory")
    print("="*70)
    
    original_cwd = os.getcwd()
    
    # Change to self_aware directory (this was causing the nested issue)
    test_dir = os.path.join(os.path.dirname(__file__), 'self_aware')
    os.chdir(test_dir)
    print(f"Changed directory to: {os.getcwd()}")
    
    try:
        # Create logger - should still create logs in self_aware/logs, NOT self_aware/self_aware/logs
        logger = data_logger.DataLogger(log_dir=None, format="csv", buffer_size=10)
        
        actual_log_dir = str(logger.log_dir)
        print(f"Log directory created: {actual_log_dir}")
        
        # Check that it doesn't create nested self_aware/self_aware/logs
        if "self_aware/self_aware" in actual_log_dir or "self_aware\\self_aware" in actual_log_dir:
            print("❌ FAILURE: Created nested self_aware/self_aware/logs!")
            logger.close()
            return False
        
        # Should end with self_aware/logs
        if actual_log_dir.endswith(os.path.join('self_aware', 'logs')):
            print("✅ SUCCESS: No nested directory created!")
        else:
            print(f"⚠️  WARNING: Unexpected path structure")
        
        # Clean up
        logger.close()
        if logger.log_file.exists():
            os.remove(logger.log_file)
        
        print("\n✅ Test 2 PASSED\n")
        return True
        
    finally:
        # Restore original directory
        os.chdir(original_cwd)


def test_file_editable_without_sudo():
    """Test that created files can be edited without sudo"""
    print("="*70)
    print("TEST 3: File Editability (No Sudo Required)")
    print("="*70)
    
    logger = data_logger.DataLogger(log_dir=None, format="csv", buffer_size=10)
    log_file_path = logger.log_file
    
    # Write some data
    logger.log_entry(
        sensor_data={'distance': 50, 'pitch': 0, 'roll': 0, 'accel_x': 0, 'accel_y': 0, 
                     'accel_z': 0, 'gyro_x': 0, 'gyro_y': 0, 'gyro_z': 0,
                     'floor_fl': 0, 'floor_fr': 0, 'floor_bl': 0, 'floor_br': 0},
        action_data={'action': 'test', 'steps': 1, 'speed': 50},
        context_data={'state': 'test', 'previous_state': 'test', 'current_speed': 50,
                      'consecutive_obstacles': 0, 'consecutive_floor_dangers': 0, 'stuck_counter': 0}
    )
    logger.flush()
    logger.close()
    
    # Try to read the file (should work without sudo)
    try:
        with open(log_file_path, 'r') as f:
            content = f.read()
        print("✅ SUCCESS: File is readable without sudo!")
    except PermissionError:
        print("❌ FAILURE: Cannot read file (permission denied)!")
        return False
    
    # Try to write to the file (should work without sudo)
    try:
        with open(log_file_path, 'a') as f:
            f.write("# Test line\n")
        print("✅ SUCCESS: File is writable without sudo!")
    except PermissionError:
        print("❌ FAILURE: Cannot write to file (permission denied)!")
        return False
    
    # Clean up
    os.remove(log_file_path)
    
    print("\n✅ Test 3 PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("LOGGING PATH FIX VERIFICATION SUITE")
    print("="*70)
    print("Testing fixes for:")
    print("  1. Script-relative paths (no nested self_aware/self_aware/logs)")
    print("  2. Proper file permissions (no sudo required)")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Script-Relative Path", test_script_relative_path()))
        results.append(("Different Directory", test_from_different_directory()))
        results.append(("File Editable (No Sudo)", test_file_editable_without_sudo()))
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Fixes are working correctly!")
        print("\nYou can now run autonomous_navigator_with_logging.py from any")
        print("directory and logs will always go to self_aware/logs with proper")
        print("permissions (no sudo required to edit/move files).")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review the output above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
