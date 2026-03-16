#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify logging paths are correct regardless of execution location.
"""

import os
import sys
import tempfile
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from self_aware.data_logger import DataLogger


def test_default_path():
    """Test that default path is always script_dir/logs"""
    print("\n" + "="*60)
    print("Testing Default Path Resolution")
    print("="*60)
    
    # Get expected path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    expected_log_dir = os.path.join(script_dir, "logs")
    
    print(f"Script location: {script_dir}")
    print(f"Expected log directory: {expected_log_dir}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Create logger with default path (None)
    logger = DataLogger(log_dir=None, format="csv", buffer_size=10)
    
    actual_log_dir = str(logger.log_dir)
    print(f"Actual log directory: {actual_log_dir}")
    
    # Check if they match
    if actual_log_dir == expected_log_dir:
        print("✅ SUCCESS: Log directory is correct!")
    else:
        print("❌ FAILURE: Log directory mismatch!")
        return False
    
    # Check file permissions
    print(f"\nChecking directory permissions...")
    dir_stat = os.stat(logger.log_dir)
    dir_perms = oct(dir_stat.st_mode)[-3:]
    print(f"Directory permissions: {dir_perms} (expected: 755)")
    
    if dir_perms == '755':
        print("✅ SUCCESS: Directory permissions are correct!")
    else:
        print(f"⚠️  WARNING: Directory permissions are {dir_perms}, expected 755")
    
    # Check if log file was created
    if logger.log_file.exists():
        file_stat = os.stat(logger.log_file)
        file_perms = oct(file_stat.st_mode)[-3:]
        print(f"\nLog file permissions: {file_perms} (expected: 666)")
        
        if file_perms == '666':
            print("✅ SUCCESS: File permissions are correct!")
        else:
            print(f"⚠️  WARNING: File permissions are {file_perms}, expected 666")
    
    # Clean up
    logger.close()
    if logger.log_file.exists():
        os.remove(logger.log_file)
    
    return True


def test_custom_path():
    """Test that custom paths still work"""
    print("\n" + "="*60)
    print("Testing Custom Path")
    print("="*60)
    
    # Create a temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_logs_")
    print(f"Custom log directory: {temp_dir}")
    
    try:
        logger = DataLogger(log_dir=temp_dir, format="csv", buffer_size=10)
        actual_log_dir = str(logger.log_dir)
        
        if actual_log_dir == temp_dir:
            print("✅ SUCCESS: Custom path works correctly!")
            logger.close()
            return True
        else:
            print(f"❌ FAILURE: Expected {temp_dir}, got {actual_log_dir}")
            logger.close()
            return False
    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Log Path Resolution Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Default path
    results.append(("Default Path", test_default_path()))
    
    # Test 2: Custom path
    results.append(("Custom Path", test_custom_path()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
