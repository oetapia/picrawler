#!/usr/bin/env python3
"""
PiCrawler Unified Diagnostic System
====================================

Interactive terminal-based diagnostic launcher for all PiCrawler hardware components.

Features:
- Menu-driven interface for easy navigation
- Run individual tests or complete suites
- Result tracking and export (JSON/CSV)
- Colored output for better readability
- Summary reports with pass/fail status

Usage:
    python3 components/diagnostic.py                    # Interactive menu
    python3 components/diagnostic.py --test accel       # Run specific test
    python3 components/diagnostic.py --suite sensors    # Run test suite
    python3 components/diagnostic.py --all              # Run all tests
    python3 components/diagnostic.py --list             # List available tests

Author: PiCrawler Diagnostic System
Date: March 17, 2026
"""

import sys
import os
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class DiagnosticRegistry:
    """Registry of all available diagnostic tools"""
    
    def __init__(self):
        self.diagnostics = {}
        self.suites = {}
        self._register_diagnostics()
        self._register_suites()
    
    def _register_diagnostics(self):
        """Register all available diagnostics"""
        self.diagnostics = {
            # SENSORS
            'accel': {
                'name': 'Accelerometer (MPU-6050)',
                'module': 'components.sensors.accel_diagnostic',
                'category': 'sensors',
                'available': self._check_file_exists('components/sensors/accel_diagnostic.py'),
                'description': 'Test MPU-6050 accelerometer and gyroscope'
            },
            'ir': {
                'name': 'IR Floor Sensors (4 legs)',
                'module': 'components.sensors.ir_diagnostic',
                'category': 'sensors',
                'available': self._check_file_exists('components/sensors/ir_diagnostic.py'),
                'description': 'Test IR floor danger sensors on all 4 legs'
            },
            'tof': {
                'name': 'ToF Distance Sensors',
                'module': 'components.sensors.tof_diagnostic',
                'category': 'sensors',
                'available': self._check_file_exists('components/sensors/tof_diagnostic.py'),
                'description': 'Test VL53L0X/L1X time-of-flight sensors'
            },
            'mux': {
                'name': 'I2C Multiplexer (PCA9548A)',
                'module': 'components.sensors.pca9548a_diagnostic',
                'category': 'sensors',
                'available': self._check_file_exists('components/sensors/pca9548a_diagnostic.py'),
                'description': 'Test I2C multiplexer channel switching'
            },
            'battery': {
                'name': 'Battery Monitor',
                'module': None,  # To be created
                'category': 'sensors',
                'available': False,
                'description': 'Test battery voltage monitoring (COMING SOON)'
            },
            'fusion': {
                'name': 'Sensor Fusion Test',
                'module': None,  # To be created
                'category': 'sensors',
                'available': False,
                'description': 'Test multi-sensor integration (COMING SOON)'
            },
            
            # DISPLAYS
            'oled': {
                'name': 'OLED Display (SSD1306)',
                'module': 'components.screens.oled_diagnostic',
                'category': 'displays',
                'available': self._check_file_exists('components/screens/oled_diagnostic.py'),
                'description': 'Test OLED display and multiplexer routing'
            },
            
            # CAMERA
            'camera': {
                'name': 'Camera & Detection',
                'module': 'components.camera.camera_diagnostic',
                'category': 'camera',
                'available': self._check_file_exists('components/camera/camera_diagnostic.py'),
                'description': 'Test camera and vilib detection capabilities'
            },
            
            # MOTION & CONTROL
            'motion': {
                'name': 'Motion Controller',
                'module': None,  # To be created
                'category': 'motion',
                'available': False,
                'description': 'Test motion controller and transitions (COMING SOON)'
            },
            'balance': {
                'name': 'Balance System',
                'module': None,  # To be created
                'category': 'motion',
                'available': False,
                'description': 'Test balance pose calculation (COMING SOON)'
            },
            'obstacle': {
                'name': 'Obstacle Handler',
                'module': None,  # To be created
                'category': 'motion',
                'available': False,
                'description': 'Test obstacle avoidance logic (COMING SOON)'
            },
            'recovery': {
                'name': 'Recovery System',
                'module': None,  # To be created
                'category': 'motion',
                'available': False,
                'description': 'Test stuck detection and recovery (COMING SOON)'
            },
            
            # PERIPHERALS
            'sound': {
                'name': 'Sound System',
                'module': None,  # To be created
                'category': 'peripherals',
                'available': False,
                'description': 'Test audio playback and TTS (COMING SOON)'
            },
            'ps4': {
                'name': 'PS4 Controller',
                'module': None,  # To be created
                'category': 'peripherals',
                'available': False,
                'description': 'Test PS4 controller pairing (COMING SOON)'
            },
            'server': {
                'name': 'Web Server API',
                'module': None,  # To be created
                'category': 'peripherals',
                'available': False,
                'description': 'Test Flask REST API endpoints (COMING SOON)'
            },
        }
    
    def _register_suites(self):
        """Register test suites"""
        self.suites = {
            'sensors': {
                'name': 'Sensor Suite',
                'tests': ['accel', 'ir', 'tof', 'mux', 'battery', 'fusion'],
                'description': 'Run all sensor diagnostics'
            },
            'motion': {
                'name': 'Motion Suite',
                'tests': ['motion', 'balance', 'obstacle', 'recovery'],
                'description': 'Run all motion and control diagnostics'
            },
            'all': {
                'name': 'Complete Test Suite',
                'tests': list(self.diagnostics.keys()),
                'description': 'Run ALL available diagnostics'
            }
        }
    
    def _check_file_exists(self, filepath: str) -> bool:
        """Check if diagnostic file exists"""
        full_path = os.path.join(project_root, filepath)
        return os.path.exists(full_path)
    
    def get_available_tests(self) -> List[str]:
        """Get list of available test IDs"""
        return [tid for tid, info in self.diagnostics.items() if info['available']]
    
    def get_tests_by_category(self, category: str) -> List[str]:
        """Get tests filtered by category"""
        return [
            tid for tid, info in self.diagnostics.items()
            if info['category'] == category
        ]


class DiagnosticMenu:
    """Interactive menu system"""
    
    COLORS = {
        'HEADER': '\033[95m',
        'BLUE': '\033[94m',
        'CYAN': '\033[96m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'END': '\033[0m',
        'BOLD': '\033[1m',
    }
    
    def __init__(self, registry: DiagnosticRegistry):
        self.registry = registry
        self.results = {}
    
    def _color(self, text: str, color: str) -> str:
        """Apply color to text"""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['END']}"
    
    def print_header(self):
        """Print menu header"""
        print("\n" + "=" * 70)
        title = self._color("  PiCrawler Hardware Diagnostic Suite", 'HEADER')
        print(title)
        print("=" * 70)
    
    def print_menu(self):
        """Print main menu"""
        self.print_header()
        
        # Group by category
        categories = {
            'sensors': 'SENSORS',
            'displays': 'DISPLAYS',
            'camera': 'CAMERA',
            'motion': 'MOTION & CONTROL',
            'peripherals': 'PERIPHERALS'
        }
        
        test_num = 1
        test_map = {}
        
        for cat_id, cat_name in categories.items():
            tests = self.registry.get_tests_by_category(cat_id)
            if not tests:
                continue
            
            print(f"\n{self._color(cat_name, 'CYAN')}")
            for tid in tests:
                info = self.registry.diagnostics[tid]
                status = "" if info['available'] else " [NEW]"
                test_map[test_num] = tid
                
                if info['available']:
                    print(f"  [{test_num:2d}] {info['name']}")
                else:
                    print(f"  [{test_num:2d}] {info['name']}{self._color(status, 'YELLOW')}")
                
                test_num += 1
        
        # Quick options
        print(f"\n{self._color('QUICK OPTIONS', 'CYAN')}")
        print(f"  [A] Run ALL available diagnostics")
        print(f"  [S] Run SENSOR suite")
        print(f"  [M] Run MOTION suite")
        print(f"  [L] List all tests with descriptions")
        print(f"  [Q] Quit")
        
        print("\n" + "=" * 70)
        
        return test_map
    
    def list_tests(self):
        """List all tests with descriptions"""
        self.print_header()
        print("\nAvailable Diagnostic Tests:\n")
        
        for tid, info in self.registry.diagnostics.items():
            status = self._color("[OK]", 'GREEN') if info['available'] else self._color("[NEW]", 'YELLOW')
            print(f"{status} {self._color(info['name'], 'BOLD')}")
            print(f"    ID: {tid}")
            print(f"    Category: {info['category']}")
            print(f"    Description: {info['description']}")
            print()
    
    def run_test(self, test_id: str) -> bool:
        """
        Run a single diagnostic test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if test passed, False otherwise
        """
        info = self.registry.diagnostics.get(test_id)
        
        if not info:
            print(self._color(f"\n[X] Unknown test ID: {test_id}", 'RED'))
            return False
        
        if not info['available']:
            print(self._color(f"\n[!] Test not yet implemented: {info['name']}", 'YELLOW'))
            print(f"    Coming soon! Check DIAGNOSTIC_TOOLS.md for details.")
            return False
        
        print(self._color(f"\n[i] Running: {info['name']}", 'CYAN'))
        print(f"    Module: {info['module']}")
        print()
        
        try:
            # Import and run the diagnostic module
            module_parts = info['module'].split('.')
            module = __import__(info['module'], fromlist=[module_parts[-1]])
            
            # Call main() if it exists
            if hasattr(module, 'main'):
                result = module.main()
                success = (result == 0) if result is not None else True
                self.results[test_id] = {
                    'name': info['name'],
                    'passed': success,
                    'timestamp': datetime.now().isoformat()
                }
                return success
            else:
                print(self._color("[!] Module has no main() function", 'YELLOW'))
                return False
                
        except ImportError as e:
            print(self._color(f"[X] Failed to import module: {e}", 'RED'))
            return False
        except KeyboardInterrupt:
            print(self._color("\n\n[!] Test interrupted by user", 'YELLOW'))
            return False
        except Exception as e:
            print(self._color(f"[X] Error running test: {e}", 'RED'))
            import traceback
            traceback.print_exc()
            return False
    
    def run_suite(self, suite_id: str) -> Dict[str, bool]:
        """
        Run a test suite.
        
        Args:
            suite_id: Suite identifier
            
        Returns:
            Dictionary of test results
        """
        suite = self.registry.suites.get(suite_id)
        if not suite:
            print(self._color(f"\n[X] Unknown suite: {suite_id}", 'RED'))
            return {}
        
        print(self._color(f"\n{suite['name']}", 'HEADER'))
        print(f"  {suite['description']}")
        print(f"  Tests: {len(suite['tests'])}")
        print()
        
        results = {}
        available_tests = [t for t in suite['tests'] if self.registry.diagnostics[t]['available']]
        
        if not available_tests:
            print(self._color("[!] No available tests in this suite yet", 'YELLOW'))
            return results
        
        print(f"Running {len(available_tests)} available tests...\n")
        input("Press Enter to continue or Ctrl+C to cancel...")
        
        for test_id in available_tests:
            success = self.run_test(test_id)
            results[test_id] = success
            print("\n" + "-" * 70)
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test results summary"""
        if not results:
            return
        
        print("\n" + "=" * 70)
        print(self._color("  TEST SUMMARY", 'HEADER'))
        print("=" * 70 + "\n")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_id, success in results.items():
            info = self.registry.diagnostics[test_id]
            symbol = self._color("[OK]", 'GREEN') if success else self._color("[X]", 'RED')
            status = "PASS" if success else "FAIL"
            print(f"{symbol} {info['name']:<40} {status}")
        
        print("\n" + "-" * 70)
        pass_rate = (passed / total * 100) if total > 0 else 0
        print(f"Total: {passed}/{total} passed ({pass_rate:.1f}%)")
        print("=" * 70)
    
    def interactive_mode(self):
        """Run interactive menu mode"""
        while True:
            test_map = self.print_menu()
            
            try:
                choice = input("\nSelect option: ").strip().upper()
                
                if choice == 'Q':
                    print("\nGoodbye!")
                    break
                
                elif choice == 'L':
                    self.list_tests()
                    input("\nPress Enter to continue...")
                    continue
                
                elif choice == 'A':
                    results = self.run_suite('all')
                    self.print_summary(results)
                    input("\nPress Enter to continue...")
                
                elif choice == 'S':
                    results = self.run_suite('sensors')
                    self.print_summary(results)
                    input("\nPress Enter to continue...")
                
                elif choice == 'M':
                    results = self.run_suite('motion')
                    self.print_summary(results)
                    input("\nPress Enter to continue...")
                
                elif choice.isdigit():
                    test_num = int(choice)
                    if test_num in test_map:
                        test_id = test_map[test_num]
                        self.run_test(test_id)
                        input("\nPress Enter to continue...")
                    else:
                        print(self._color("\n[X] Invalid test number", 'RED'))
                        input("Press Enter to continue...")
                
                else:
                    print(self._color("\n[X] Invalid choice", 'RED'))
                    input("Press Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(self._color(f"\n[X] Error: {e}", 'RED'))
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PiCrawler Unified Diagnostic System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 components/diagnostic.py                    # Interactive menu
  python3 components/diagnostic.py --list             # List all tests
  python3 components/diagnostic.py --test accel       # Run accelerometer test
  python3 components/diagnostic.py --test ir          # Run IR sensor test
  python3 components/diagnostic.py --suite sensors    # Run all sensor tests
  python3 components/diagnostic.py --all              # Run ALL tests
        """
    )
    
    parser.add_argument('--test', help='Run specific test by ID')
    parser.add_argument('--suite', help='Run test suite (sensors, motion, all)')
    parser.add_argument('--all', action='store_true', help='Run all available tests')
    parser.add_argument('--list', action='store_true', help='List all available tests')
    
    args = parser.parse_args()
    
    # Create registry and menu
    registry = DiagnosticRegistry()
    menu = DiagnosticMenu(registry)
    
    # Handle command-line arguments
    if args.list:
        menu.list_tests()
        return 0
    
    elif args.test:
        success = menu.run_test(args.test)
        return 0 if success else 1
    
    elif args.suite:
        results = menu.run_suite(args.suite)
        menu.print_summary(results)
        passed = sum(1 for v in results.values() if v)
        return 0 if passed == len(results) else 1
    
    elif args.all:
        results = menu.run_suite('all')
        menu.print_summary(results)
        passed = sum(1 for v in results.values() if v)
        return 0 if passed == len(results) else 1
    
    else:
        # Interactive mode
        menu.interactive_mode()
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
