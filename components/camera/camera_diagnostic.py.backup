#!/usr/bin/env python3
"""
Camera Detection Diagnostic Tool

Tests all vilib detection capabilities:
- Color detection (red, orange, yellow, green, blue, purple)
- Face detection
- QR code detection
- Object detection (COCO dataset)
- Traffic sign detection
- Image classification (ImageNet)

Usage:
    python components/camera/camera_diagnostic.py [--mode MODE] [--duration SECONDS]

Modes:
    all      - Test all detection types sequentially (default)
    color    - Test color detection only
    face     - Test face detection only
    qr       - Test QR code detection only
    object   - Test object detection only
    traffic  - Test traffic sign detection only
    classify - Test image classification only
    
Press Ctrl+C to stop any test early.
"""

import sys
import os
import time

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from components.camera.vilib_detector import VilibDetector


class CameraDiagnostic:
    """Diagnostic tool for camera detection capabilities"""
    
    def __init__(self):
        self.detector = VilibDetector()
        self.results = {}
    
    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_result(self, detected: bool, message: str):
        """Print detection result"""
        symbol = "[OK]" if detected else "[X]"
        print(f"{symbol} {message}")
    
    def test_color_detection(self, duration: int = 10):
        """Test color detection for all colors"""
        self.print_header("COLOR DETECTION TEST")
        
        colors = ["red", "orange", "yellow", "green", "blue", "purple"]
        results = {}
        
        print("\nTesting color detection for all available colors...")
        print("Show colored objects to the camera!\n")
        
        for color in colors:
            print(f"\n-> Testing {color.upper()} detection ({duration}s)...")
            self.detector.enable_color_detection(color)
            time.sleep(0.5)
            
            detected_count = 0
            for i in range(duration * 10):  # 10 checks per second
                result = self.detector.get_color_detection()
                if result.detected:
                    detected_count += 1
                    print(f"  {color}: Detected at {result.coordinate}, size {result.size}")
                time.sleep(0.1)
            
            results[color] = detected_count > 0
            self.print_result(results[color], f"{color} detection: {'WORKING' if results[color] else 'No detection'}")
            self.detector.disable_color_detection()
        
        self.results['color'] = results
        return results
    
    def test_face_detection(self, duration: int = 10):
        """Test face detection"""
        self.print_header("FACE DETECTION TEST")
        
        print("\nTesting face detection...")
        print("Show your face to the camera!\n")
        
        self.detector.enable_face_detection()
        time.sleep(0.5)
        
        detected_count = 0
        for i in range(duration * 10):
            result = self.detector.get_face_detection()
            if result.detected:
                detected_count += 1
                print(f"  Face detected: {result.count} face(s) at {result.coordinate}, size {result.size}")
            time.sleep(0.1)
        
        success = detected_count > 0
        self.detector.disable_face_detection()
        
        self.print_result(success, f"Face detection: {'WORKING' if success else 'No detection'}")
        self.results['face'] = success
        return success
    
    def test_qr_detection(self, duration: int = 10):
        """Test QR code detection"""
        self.print_header("QR CODE DETECTION TEST")
        
        print("\nTesting QR code detection...")
        print("Show a QR code to the camera!\n")
        
        self.detector.enable_qr_detection()
        time.sleep(0.5)
        
        detected_codes = []
        for i in range(duration * 10):
            result = self.detector.get_qr_detection()
            if result.detected and result.data not in detected_codes:
                detected_codes.append(result.data)
                print(f"  QR Code detected: {result.data}")
            time.sleep(0.1)
        
        success = len(detected_codes) > 0
        self.detector.disable_qr_detection()
        
        self.print_result(success, f"QR code detection: {'WORKING' if success else 'No detection'}")
        if detected_codes:
            print(f"  Detected codes: {detected_codes}")
        self.results['qr'] = success
        return success
    
    def test_object_detection(self, duration: int = 15):
        """Test object detection (COCO dataset)"""
        self.print_header("OBJECT DETECTION TEST (COCO)")
        
        print("\nTesting object detection...")
        print("Show common objects to the camera (person, car, dog, cat, etc.)\n")
        
        self.detector.enable_object_detection()
        time.sleep(0.5)
        
        detected_objects = {}
        for i in range(duration * 10):
            result = self.detector.get_object_detection()
            if result.detected:
                obj_type = result.data or 'unknown'
                if obj_type not in detected_objects:
                    detected_objects[obj_type] = 0
                detected_objects[obj_type] += 1
                print(f"  Object detected: {obj_type} at {result.coordinate}, size {result.size}")
            time.sleep(0.1)
        
        success = len(detected_objects) > 0
        self.detector.disable_object_detection()
        
        self.print_result(success, f"Object detection: {'WORKING' if success else 'No detection'}")
        if detected_objects:
            print(f"  Detected objects: {list(detected_objects.keys())}")
            print(f"  Detection counts: {detected_objects}")
        self.results['object'] = success
        return success
    
    def test_traffic_sign_detection(self, duration: int = 10):
        """Test traffic sign detection"""
        self.print_header("TRAFFIC SIGN DETECTION TEST")
        
        print("\nTesting traffic sign detection...")
        print("Show traffic signs to the camera (or images of signs)\n")
        
        self.detector.enable_traffic_sign_detection()
        time.sleep(0.5)
        
        detected_signs = {}
        for i in range(duration * 10):
            result = self.detector.get_traffic_sign_detection()
            if result.detected:
                sign_type = result.data or 'unknown'
                if sign_type not in detected_signs:
                    detected_signs[sign_type] = 0
                detected_signs[sign_type] += 1
                print(f"  Traffic sign detected: {sign_type} at {result.coordinate}, size {result.size}")
            time.sleep(0.1)
        
        success = len(detected_signs) > 0
        self.detector.disable_traffic_sign_detection()
        
        self.print_result(success, f"Traffic sign detection: {'WORKING' if success else 'No detection'}")
        if detected_signs:
            print(f"  Detected signs: {list(detected_signs.keys())}")
        self.results['traffic_sign'] = success
        return success
    
    def test_image_classification(self, duration: int = 10):
        """Test image classification (ImageNet)"""
        self.print_header("IMAGE CLASSIFICATION TEST (ImageNet)")
        
        print("\nTesting image classification...")
        print("Point camera at various objects for classification\n")
        
        self.detector.enable_image_classification()
        time.sleep(0.5)
        
        classifications = []
        for i in range(duration * 10):
            result = self.detector.get_image_classification()
            if result.detected and result.data not in classifications:
                classifications.append(result.data)
                print(f"  Classification: {result.data}")
            time.sleep(0.1)
        
        success = len(classifications) > 0
        self.detector.disable_image_classification()
        
        self.print_result(success, f"Image classification: {'WORKING' if success else 'No detection'}")
        if classifications:
            print(f"  Classifications: {classifications}")
        self.results['image_classify'] = success
        return success
    
    def print_summary(self):
        """Print overall test summary"""
        self.print_header("DIAGNOSTIC SUMMARY")
        
        print("\nDetection Type             Status")
        print("-" * 40)
        
        for test_name, result in self.results.items():
            if isinstance(result, dict):
                # Color detection results
                print(f"\n{test_name.upper()} DETECTION:")
                for color, status in result.items():
                    symbol = "[OK]" if status else "[X]"
                    status_str = "PASS" if status else "FAIL"
                    print(f"  {symbol} {color:12s} {status_str}")
            else:
                symbol = "[OK]" if result else "[X]"
                status_str = "PASS" if result else "FAIL"
                print(f"{symbol} {test_name:20s} {status_str}")
        
        # Overall status
        all_tests = []
        for result in self.results.values():
            if isinstance(result, dict):
                all_tests.extend(result.values())
            else:
                all_tests.append(result)
        
        total_passed = sum(all_tests)
        total_tests = len(all_tests)
        
        print("\n" + "="*40)
        print(f"Total: {total_passed}/{total_tests} tests passed")
        print("="*40)
        
        if total_passed == total_tests:
            print("\n[OK] ALL SYSTEMS OPERATIONAL")
        elif total_passed > 0:
            print(f"\n[!] PARTIAL FUNCTIONALITY ({total_passed}/{total_tests} working)")
        else:
            print("\n[X] NO DETECTIONS WORKING - CHECK VILIB INSTALLATION")
    
    def run_all_tests(self, color_duration: int = 5, other_duration: int = 10, skip_tests: list = None):
        """Run all diagnostic tests"""
        skip_tests = skip_tests or []
        
        print("\n" + "="*60)
        print("  CAMERA DETECTION DIAGNOSTIC TOOL")
        print("="*60)
        print("\nThis will test all vilib detection capabilities.")
        if skip_tests:
            print(f"Skipping tests: {', '.join(skip_tests)}")
        print("View camera stream at: http://localhost:9000/mjpg")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        try:
            # Start camera
            self.detector.start_camera()
            self.detector.start_display(web=True)
            time.sleep(1)
            
            # Run tests (skip any in skip list)
            if 'object' not in skip_tests:
                self.test_object_detection(other_duration)
            if 'color' not in skip_tests:
                self.test_color_detection(color_duration)
            if 'face' not in skip_tests:
                self.test_face_detection(other_duration)
            if 'qr' not in skip_tests:
                self.test_qr_detection(other_duration)
            if 'traffic' not in skip_tests:
                self.test_traffic_sign_detection(other_duration)
            if 'classify' not in skip_tests:
                self.test_image_classification(other_duration)
            
        except KeyboardInterrupt:
            print("\n\n[!] Test interrupted by user")
        finally:
            self.detector.stop_camera()
        
        # Print summary
        self.print_summary()
    
    def run_single_test(self, mode: str, duration: int = 10):
        """Run a single diagnostic test"""
        print("\n" + "="*60)
        print(f"  CAMERA {mode.upper()} DETECTION TEST")
        print("="*60)
        print(f"\nView camera stream at: http://localhost:9000/mjpg")
        print(f"Test duration: {duration} seconds")
        print("\nStarting in 2 seconds...")
        time.sleep(2)
        
        try:
            self.detector.start_camera()
            self.detector.start_display(web=True)
            time.sleep(1)
            
            if mode == 'color':
                self.test_color_detection(duration)
            elif mode == 'face':
                self.test_face_detection(duration)
            elif mode == 'qr':
                self.test_qr_detection(duration)
            elif mode == 'object':
                self.test_object_detection(duration)
            elif mode == 'traffic':
                self.test_traffic_sign_detection(duration)
            elif mode == 'classify':
                self.test_image_classification(duration)
            
        except KeyboardInterrupt:
            print("\n\n[!] Test interrupted by user")
        finally:
            self.detector.stop_camera()
        
        self.print_summary()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Camera Detection Diagnostic Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python components/camera/camera_diagnostic.py                       # Run all tests
  python components/camera/camera_diagnostic.py --skip qr             # Run all tests except QR
  python components/camera/camera_diagnostic.py --skip qr classify    # Skip QR and classify
  python components/camera/camera_diagnostic.py --mode object         # Test object detection
  python components/camera/camera_diagnostic.py --mode color -d 15    # Test colors for 15s each
  python components/camera/camera_diagnostic.py --mode face -d 20     # Test face for 20s

Note: Use --skip to avoid tests that cause errors (e.g., QR code has vilib bug)
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['all', 'color', 'face', 'qr', 'object', 'traffic', 'classify'],
        default='all',
        help='Detection mode to test (default: all)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=10,
        help='Test duration in seconds for each test (default: 10)'
    )
    parser.add_argument(
        '--skip',
        nargs='+',
        choices=['color', 'face', 'qr', 'object', 'traffic', 'classify'],
        default=[],
        help='Tests to skip (space-separated list)'
    )
    
    args = parser.parse_args()
    
    # Create diagnostic tool
    diagnostic = CameraDiagnostic()
    
    # Run tests
    if args.mode == 'all':
        # For 'all', use shorter duration per color
        color_duration = max(5, args.duration // 2)
        diagnostic.run_all_tests(color_duration=color_duration, other_duration=args.duration, skip_tests=args.skip)
    else:
        diagnostic.run_single_test(args.mode, args.duration)


if __name__ == '__main__':
    main()
