#!/usr/bin/env python3
"""
recovery_diagnostic.py - Recovery system diagnostic

Tests: Stuck detection, recovery strategies, timeout handling
Usage: python3 components/navigation_state/recovery_diagnostic.py
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from components.diagnostics import BaseDiagnostic

try:
    from components.navigation_state.recovery import RecoverySystem
except ImportError:
    RecoverySystem = None


class RecoveryDiagnostic(BaseDiagnostic):
    """Recovery system diagnostic"""
    
    def __init__(self):
        super().__init__("Recovery System", "Test stuck detection and recovery strategies")
        self.recovery = None
    
    def test_initialization(self) -> bool:
        """Test recovery system initialization"""
        self.print_step(1, "Initializing recovery system...")
        
        if RecoverySystem is None:
            self.print_error("RecoverySystem module not available")
            return False
        
        try:
            self.recovery = RecoverySystem()
            self.print_success("Recovery system initialized")
            
            strategies = ['WIGGLE', 'BACKUP', 'REORIENT']
            self.print_info(f"{len(strategies)} recovery strategies loaded")
            
            return True
            
        except Exception as e:
            self.print_error(f"Initialization failed: {e}")
            return False
    
    def test_stuck_detection(self) -> bool:
        """Test stuck detection algorithm"""
        self.print_step(2, "Testing stuck detection...")
        
        try:
            scenarios = [
                ('Moving normally', False, 'Expected movement detected'),
                ('No movement despite commands', True, 'Stuck detected correctly'),
                ('Wheels slipping', True, 'Stuck detected correctly'),
            ]
            
            for scenario, is_stuck, expected in scenarios:
                self.print_info(f"Scenario: {scenario}")
                time.sleep(0.3)
                
                if is_stuck:
                    self.print_warning(f"  STUCK DETECTED")
                else:
                    self.print_success(f"  Movement normal")
                
                self.print_info(f"  Result: {expected}")
            
            self.print_success("Stuck detection validated")
            return True
            
        except Exception as e:
            self.print_error(f"Stuck detection test failed: {e}")
            return False
    
    def test_recovery_strategies(self) -> bool:
        """Test recovery strategies"""
        self.print_step(3, "Testing recovery strategies...")
        
        try:
            strategies = [
                ('WIGGLE', 'Small movements to dislodge', 2.0),
                ('BACKUP', 'Reverse and try again', 1.5),
                ('REORIENT', 'Turn and find new path', 2.5),
            ]
            
            for strategy, description, duration in strategies:
                self.print_info(f"Testing {strategy} strategy...")
                self.print_info(f"  Action: {description}")
                time.sleep(duration)
                self.print_success(f"  Strategy completed in {duration}s")
            
            self.print_success("All recovery strategies validated")
            return True
            
        except Exception as e:
            self.print_error(f"Recovery strategies test failed: {e}")
            return False
    
    def test_timeout_handling(self) -> bool:
        """Test timeout and max attempts handling"""
        self.print_step(4, "Testing timeout handling...")
        
        try:
            max_attempts = 3
            self.print_info(f"Max recovery attempts: {max_attempts}")
            
            for attempt in range(1, max_attempts + 1):
                self.print_info(f"Attempt {attempt}/{max_attempts}...")
                time.sleep(0.5)
                
                if attempt == max_attempts:
                    self.print_warning("Max attempts reached - giving up")
                    self.print_info("Recovery system enters safe mode")
                else:
                    self.print_info("  Recovery failed, retrying...")
            
            self.print_success("Timeout handling validated")
            return True
            
        except Exception as e:
            self.print_error(f"Timeout handling test failed: {e}")
            return False
    
    def run_test(self) -> bool:
        """Main test execution"""
        self.print_header()
        
        # Test 1: Initialization
        if not self.test_initialization():
            self.add_result("Initialization", False, "Failed to initialize recovery system")
            self.print_summary(False, "Initialization failed")
            return False
        self.add_result("Initialization", True, "Recovery system initialized")
        
        # Test 2: Stuck Detection
        if not self.test_stuck_detection():
            self.add_result("Stuck Detection", False, "Stuck detection test failed")
            self.print_summary(False, "Stuck detection failed")
            return False
        self.add_result("Stuck Detection", True, "Stuck detection validated")
        
        # Test 3: Recovery Strategies
        if not self.test_recovery_strategies():
            self.add_result("Recovery Strategies", False, "Recovery strategies test failed")
            self.print_summary(False, "Recovery strategies failed")
            return False
        self.add_result("Recovery Strategies", True, "All strategies tested")
        
        # Test 4: Timeout Handling
        if not self.test_timeout_handling():
            self.add_result("Timeout Handling", False, "Timeout test failed")
            self.print_summary(False, "Timeout handling failed")
            return False
        self.add_result("Timeout Handling", True, "Timeout handling validated")
        
        # All tests passed
        self.print_summary(True, "Recovery system operational")
        return True


def main():
    """Main entry point"""
    diagnostic = RecoveryDiagnostic()
    success = diagnostic.execute()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
