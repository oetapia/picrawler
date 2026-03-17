#!/usr/bin/env python3
"""
battery_diagnostic.py - Battery voltage monitoring diagnostic

Tests: Battery voltage monitoring, ADC readings, threshold validation
Usage: python3 components/sensors/battery_diagnostic.py
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
    from components.sensors.battery_status import BatteryStatus
except ImportError:
    BatteryStatus = None


class BatteryDiagnostic(BaseDiagnostic):
    """Battery voltage monitoring diagnostic"""
    
    def __init__(self):
        super().__init__("Battery Monitor", "Real-time voltage monitoring and threshold validation")
        self.battery = None
        self.voltage_readings = []
    
    def test_initialization(self) -> bool:
        """Test battery monitor initialization"""
        self.print_step(1, "Initializing battery monitor...")
        
        if BatteryStatus is None:
            self.print_error("BatteryStatus module not available")
            return False
        
        try:
            self.battery = BatteryStatus()
            self.print_success("Battery monitor initialized")
            
            # Get initial voltage
            voltage = self.battery.get_battery_voltage()
            if voltage is None:
                self.print_error("Failed to read battery voltage")
                return False
            
            percentage = self.battery.get_battery_percentage()
            self.print_info(f"Current voltage: {voltage:.2f}V ({percentage}% charge)")
            
            return True
            
        except Exception as e:
            self.print_error(f"Initialization failed: {e}")
            return False
    
    def test_voltage_reading(self) -> bool:
        """Test voltage reading accuracy"""
        self.print_step(2, "Testing voltage readings...")
        
        try:
            voltage = self.battery.get_battery_voltage()
            percentage = self.battery.get_battery_percentage()
            
            # Typical LiPo 2S range: 6.0V (empty) to 8.4V (full)
            if voltage < 5.0 or voltage > 9.0:
                self.print_warning(f"Voltage out of typical range: {voltage:.2f}V")
                self.print_info("Expected range: 6.0V - 8.4V for 2S LiPo")
            else:
                self.print_success(f"Voltage reading: {voltage:.2f}V")
            
            self.print_info(f"Battery percentage: {percentage}%")
            self.print_info(f"Charge estimate: {self._get_charge_status(voltage)}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Voltage reading failed: {e}")
            return False
    
    def test_live_monitoring(self, duration: int = 10) -> bool:
        """Test live voltage monitoring with stability check"""
        self.print_step(3, f"Live voltage monitoring ({duration}s)...")
        
        try:
            start_time = time.time()
            readings = []
            
            while time.time() - start_time < duration:
                voltage = self.battery.get_battery_voltage()
                percentage = self.battery.get_battery_percentage()
                elapsed = int(time.time() - start_time)
                
                # Create ASCII bar chart
                bar = self._create_voltage_bar(percentage)
                
                print(f"\r  {voltage:.2f}V |{bar}| {percentage:>3}%  [{elapsed:02d}:{(duration-elapsed):02d}]", end="", flush=True)
                
                readings.append(voltage)
                time.sleep(0.5)
            
            print()  # New line after monitoring
            
            # Calculate stability
            if len(readings) > 2:
                avg_voltage = sum(readings) / len(readings)
                variance = sum((v - avg_voltage) ** 2 for v in readings) / len(readings)
                std_dev = variance ** 0.5
                
                self.print_info(f"Average voltage: {avg_voltage:.3f}V")
                self.print_info(f"Voltage stability: {std_dev:.3f}V std deviation")
                
                if std_dev < 0.05:
                    self.print_success("Voltage stable (< 0.05V variation)")
                else:
                    self.print_warning(f"Voltage unstable ({std_dev:.3f}V variation)")
            
            return True
            
        except KeyboardInterrupt:
            print()
            self.print_warning("Monitoring interrupted by user")
            return True
        except Exception as e:
            print()
            self.print_error(f"Monitoring failed: {e}")
            return False
    
    def test_threshold_validation(self) -> bool:
        """Test voltage threshold warnings"""
        self.print_step(4, "Threshold validation...")
        
        try:
            voltage = self.battery.get_battery_voltage()
            
            # Define thresholds
            CRITICAL_THRESHOLD = 6.0  # Below this, robot should stop
            WARNING_THRESHOLD = 6.5   # Below this, warning should trigger
            NORMAL_THRESHOLD = 7.0    # Above this, normal operation
            
            if voltage < CRITICAL_THRESHOLD:
                self.print_error(f"CRITICAL: Battery voltage too low ({voltage:.2f}V < {CRITICAL_THRESHOLD}V)")
                self.print_error("Robot should stop operation immediately!")
                status = "CRITICAL"
            elif voltage < WARNING_THRESHOLD:
                self.print_warning(f"WARNING: Battery voltage low ({voltage:.2f}V < {WARNING_THRESHOLD}V)")
                self.print_warning("Recharge soon to avoid damage")
                status = "LOW"
            elif voltage < NORMAL_THRESHOLD:
                self.print_info(f"CAUTION: Battery voltage moderate ({voltage:.2f}V)")
                status = "MODERATE"
            else:
                self.print_success(f"NORMAL: Battery voltage good ({voltage:.2f}V > {NORMAL_THRESHOLD}V)")
                status = "NORMAL"
            
            self.print_info(f"Battery status: {status}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Threshold test failed: {e}")
            return False
    
    def _get_charge_status(self, voltage: float) -> str:
        """Get human-readable charge status"""
        if voltage >= 8.0:
            return "Fully charged"
        elif voltage >= 7.5:
            return "Good charge"
        elif voltage >= 7.0:
            return "Moderate charge"
        elif voltage >= 6.5:
            return "Low charge"
        else:
            return "Critical - recharge now"
    
    def _create_voltage_bar(self, percentage: int, width: int = 20) -> str:
        """Create ASCII bar chart for voltage level"""
        filled = int(percentage / 100 * width)
        empty = width - filled
        return "[EMOJI]" * filled + "[EMOJI]" * empty
    
    def run_test(self) -> bool:
        """Main test execution"""
        self.print_header()
        
        # Test 1: Initialization
        if not self.test_initialization():
            self.add_result("Initialization", False, "Failed to initialize battery monitor")
            self.print_summary(False, "Initialization failed")
            return False
        self.add_result("Initialization", True, "Battery monitor initialized successfully")
        
        # Test 2: Voltage Reading
        if not self.test_voltage_reading():
            self.add_result("Voltage Reading", False, "Failed to read voltage")
            self.print_summary(False, "Voltage reading failed")
            return False
        self.add_result("Voltage Reading", True, "Voltage reading successful")
        
        # Test 3: Live Monitoring
        if not self.test_live_monitoring(duration=10):
            self.add_result("Live Monitoring", False, "Monitoring failed")
            self.print_summary(False, "Live monitoring failed")
            return False
        self.add_result("Live Monitoring", True, "Live monitoring completed")
        
        # Test 4: Threshold Validation
        if not self.test_threshold_validation():
            self.add_result("Threshold Validation", False, "Threshold test failed")
            self.print_summary(False, "Threshold validation failed")
            return False
        self.add_result("Threshold Validation", True, "Thresholds validated")
        
        # All tests passed
        self.print_summary(True, "Battery monitor operational")
        return True


def main():
    """Main entry point"""
    diagnostic = BatteryDiagnostic()
    success = diagnostic.execute()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
