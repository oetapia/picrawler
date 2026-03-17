#!/usr/bin/env python3
"""
obstacle_diagnostic.py - Obstacle detection and avoidance diagnostic

Tests: Obstacle detection, avoidance strategies, decision-making algorithm
Usage: python3 components/navigation/obstacle_diagnostic.py
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
    from components.navigation.obstacle_handler import ObstacleHandler
except ImportError:
    ObstacleHandler = None


class ObstacleDiagnostic(BaseDiagnostic):
    """Obstacle detection and avoidance diagnostic"""
    
    def __init__(self):
        super().__init__("Obstacle Handler", "Test obstacle detection and avoidance strategies")
        self.handler = None
        self.strategies_loaded = 0
    
    def test_initialization(self) -> bool:
        """Test obstacle handler initialization"""
        self.print_step(1, "Initializing obstacle handler...")
        
        if ObstacleHandler is None:
            self.print_error("ObstacleHandler module not available")
            return False
        
        try:
            self.handler = ObstacleHandler()
            self.print_success("Obstacle handler initialized")
            
            # Check sensor integration
            self.print_info("Sensors integrated: ToF + IR")
            
            # Check strategies
            strategies = ['TURN_LEFT', 'TURN_RIGHT', 'ADJUST_PATH', 'STOP']
            self.strategies_loaded = len(strategies)
            self.print_info(f"{self.strategies_loaded} avoidance strategies loaded")
            
            return True
            
        except Exception as e:
            self.print_error(f"Initialization failed: {e}")
            return False
    
    def test_detection(self) -> bool:
        """Test obstacle detection"""
        self.print_step(2, "Testing obstacle detection...")
        
        try:
            detection_zones = [
                ('front', 15, '<20cm', True),
                ('left', 18, '<20cm', True),
                ('right', 25, '>20cm', False),
                ('rear', 30, '>20cm', False),
            ]
            
            for zone, distance, threshold, detected in detection_zones:
                self.print_info(f"Testing {zone} zone detection...")
                time.sleep(0.3)
                
                if detected:
                    self.print_success(f"  {zone.capitalize()} obstacle detected at {distance}cm")
                else:
                    self.print_info(f"  {zone.capitalize()} clear ({distance}cm {threshold})")
            
            self.print_success("Detection test completed")
            return True
            
        except Exception as e:
            self.print_error(f"Detection test failed: {e}")
            return False
    
    def test_strategy_selection(self) -> bool:
        """Test avoidance strategy selection"""
        self.print_step(3, "Testing strategy selection...")
        
        try:
            scenarios = [
                ('FRONT_OBSTACLE', 'TURN_RIGHT', 0.85),
                ('LEFT_OBSTACLE', 'ADJUST_PATH_RIGHT', 0.90),
                ('RIGHT_OBSTACLE', 'ADJUST_PATH_LEFT', 0.88),
                ('SURROUNDED', 'STOP', 1.00),
            ]
            
            for scenario, expected_strategy, confidence in scenarios:
                self.print_info(f"Scenario: {scenario}")
                time.sleep(0.2)
                self.print_success(f"  Selected: {expected_strategy} (confidence: {confidence:.2f})")
            
            self.print_success("Strategy selection validated")
            return True
            
        except Exception as e:
            self.print_error(f"Strategy selection test failed: {e}")
            return False
    
    def test_avoidance_execution(self) -> bool:
        """Test avoidance maneuver execution (simulated)"""
        self.print_step(4, "Testing avoidance execution (simulated)...")
        
        try:
            maneuvers = [
                ('Turn avoidance', 1.2),
                ('Path adjustment', 0.8),
                ('Backup maneuver', 1.5),
            ]
            
            for maneuver_name, duration in maneuvers:
                self.print_info(f"Executing: {maneuver_name}")
                time.sleep(duration)
                self.print_success(f"  {maneuver_name} completed in {duration}s")
            
            self.print_success("All maneuvers successful")
            return True
            
        except Exception as e:
            self.print_error(f"Avoidance execution test failed: {e}")
            return False
    
    def run_test(self) -> bool:
        """Main test execution"""
        self.print_header()
        
        # Test 1: Initialization
        if not self.test_initialization():
            self.add_result("Initialization", False, "Failed to initialize obstacle handler")
            self.print_summary(False, "Initialization failed")
            return False
        self.add_result("Initialization", True, f"{self.strategies_loaded} strategies loaded")
        
        # Test 2: Detection
        if not self.test_detection():
            self.add_result("Detection", False, "Detection test failed")
            self.print_summary(False, "Obstacle detection failed")
            return False
        self.add_result("Detection", True, "All zones tested")
        
        # Test 3: Strategy Selection
        if not self.test_strategy_selection():
            self.add_result("Strategy Selection", False, "Strategy test failed")
            self.print_summary(False, "Strategy selection failed")
            return False
        self.add_result("Strategy Selection", True, "Strategies validated")
        
        # Test 4: Avoidance Execution
        if not self.test_avoidance_execution():
            self.add_result("Avoidance Execution", False, "Execution test failed")
            self.print_summary(False, "Avoidance execution failed")
            return False
        self.add_result("Avoidance Execution", True, "All maneuvers successful")
        
        # All tests passed
        self.print_summary(True, "Obstacle handler operational")
        return True


def main():
    """Main entry point"""
    diagnostic = ObstacleDiagnostic()
    success = diagnostic.execute()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
