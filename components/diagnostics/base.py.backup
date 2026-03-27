#!/usr/bin/env python3
"""
Base Diagnostic Class
=====================

Standard base class for all PiCrawler diagnostic tools.

Features:
- Consistent output formatting
- Result tracking and export
- Standard test patterns
- Error handling

Author: PiCrawler Diagnostic System
Date: March 17, 2026
"""

import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class DiagnosticResult:
    """Single diagnostic test result"""
    test_name: str
    passed: bool
    message: str
    timestamp: str
    duration: float = 0.0
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class BaseDiagnostic:
    """
    Base class for all diagnostic tools.
    
    Provides standard formatting, result tracking, and common patterns.
    """
    
    # ANSI color codes
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
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize diagnostic tool.
        
        Args:
            name: Diagnostic name (e.g., "Accelerometer")
            description: Brief description
        """
        self.name = name
        self.description = description
        self.results: List[DiagnosticResult] = []
        self.status = "not_run"
        self.start_time = None
        self.end_time = None
        self.use_colors = True
    
    def _color(self, text: str, color: str) -> str:
        """Apply color to text"""
        if not self.use_colors:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['END']}"
    
    def print_header(self):
        """Print diagnostic header"""
        print("\n" + "=" * 70)
        title = f"  {self.name.upper()} DIAGNOSTIC"
        if self.description:
            title += f" - {self.description}"
        print(self._color(title, 'HEADER'))
        print("=" * 70 + "\n")
    
    def print_step(self, step_num: int, message: str):
        """Print test step"""
        print(f"\n{self._color(f'[STEP {step_num}]', 'CYAN')} {message}")
    
    def print_success(self, message: str):
        """Print success message"""
        symbol = self._color("[OK]", 'GREEN')
        print(f"  {symbol} {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        symbol = self._color("[X]", 'RED')
        print(f"  {symbol} {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        symbol = self._color("[!]", 'YELLOW')
        print(f"  {symbol} {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        symbol = self._color("[i]", 'BLUE')
        print(f"  {symbol} {message}")
    
    def print_summary(self, passed: bool, message: str):
        """Print final summary"""
        print("\n" + "-" * 70)
        if passed:
            result_text = self._color("PASS", 'GREEN')
            symbol = self._color("[OK]", 'GREEN')
        else:
            result_text = self._color("FAIL", 'RED')
            symbol = self._color("[X]", 'RED')
        
        print(f"RESULT: {symbol} {result_text} - {message}")
        
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"Duration: {duration:.2f}s")
        
        print("-" * 70)
    
    def add_result(self, test_name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """
        Add a test result.
        
        Args:
            test_name: Name of the test
            passed: Whether test passed
            message: Result message
            details: Optional additional details
        """
        result = DiagnosticResult(
            test_name=test_name,
            passed=passed,
            message=message,
            timestamp=datetime.now().isoformat(),
            details=details or {}
        )
        self.results.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get diagnostic summary.
        
        Returns:
            Dictionary with diagnostic results
        """
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        
        return {
            'diagnostic_name': self.name,
            'description': self.description,
            'status': self.status,
            'total_tests': total_count,
            'passed_tests': passed_count,
            'failed_tests': total_count - passed_count,
            'pass_rate': (passed_count / total_count * 100) if total_count > 0 else 0,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': (self.end_time - self.start_time) if (self.start_time and self.end_time) else 0,
            'results': [r.to_dict() for r in self.results]
        }
    
    def export_json(self, filepath: str):
        """
        Export results to JSON file.
        
        Args:
            filepath: Output file path
        """
        summary = self.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n{self._color('[OK]', 'GREEN')} Results exported to: {filepath}")
    
    def export_csv(self, filepath: str):
        """
        Export results to CSV file.
        
        Args:
            filepath: Output file path
        """
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Test Name', 'Passed', 'Message', 'Timestamp', 'Duration'])
            
            for result in self.results:
                writer.writerow([
                    result.test_name,
                    'PASS' if result.passed else 'FAIL',
                    result.message,
                    result.timestamp,
                    f"{result.duration:.2f}s"
                ])
        
        print(f"\n{self._color('[OK]', 'GREEN')} Results exported to: {filepath}")
    
    def run_test(self) -> bool:
        """
        Main test execution method - OVERRIDE THIS.
        
        Returns:
            True if all tests passed, False otherwise
        """
        raise NotImplementedError("Subclasses must implement run_test()")
    
    def execute(self) -> bool:
        """
        Execute the diagnostic with timing and status tracking.
        
        Returns:
            True if diagnostic passed, False otherwise
        """
        self.status = "running"
        self.start_time = time.time()
        
        try:
            success = self.run_test()
            self.status = "passed" if success else "failed"
            return success
        except KeyboardInterrupt:
            self.status = "interrupted"
            print(f"\n\n{self._color('[!]', 'YELLOW')} Test interrupted by user")
            return False
        except Exception as e:
            self.status = "error"
            self.print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.end_time = time.time()


class SimpleDiagnostic(BaseDiagnostic):
    """
    Simple diagnostic template for basic tests.
    
    Override test_* methods to implement your diagnostic.
    """
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self.component = None
    
    def test_initialization(self) -> bool:
        """Test component initialization - OVERRIDE THIS"""
        self.print_step(1, "Initializing component...")
        # Override with actual initialization
        self.print_success("Component initialized")
        return True
    
    def test_basic_operation(self) -> bool:
        """Test basic operation - OVERRIDE THIS"""
        self.print_step(2, "Testing basic operation...")
        # Override with actual tests
        self.print_success("Basic operation working")
        return True
    
    def test_live_stream(self, duration: int = 10) -> bool:
        """Test live data streaming - OVERRIDE THIS"""
        self.print_step(3, f"Live readings ({duration}s)...")
        # Override with actual streaming
        for i in range(duration):
            print(f"  Reading {i+1}/{duration}...", end='\r')
            time.sleep(1)
        print()
        self.print_success(f"Completed {duration}s of streaming")
        return True
    
    def run_test(self) -> bool:
        """Standard test execution pattern"""
        self.print_header()
        
        if not self.test_initialization():
            self.add_result("Initialization", False, "Failed to initialize")
            self.print_summary(False, "Initialization failed")
            return False
        self.add_result("Initialization", True, "Component initialized")
        
        if not self.test_basic_operation():
            self.add_result("Basic Operation", False, "Basic operation failed")
            self.print_summary(False, "Basic operation failed")
            return False
        self.add_result("Basic Operation", True, "Basic operation working")
        
        if not self.test_live_stream():
            self.add_result("Live Stream", False, "Streaming failed")
            self.print_summary(False, "Live streaming failed")
            return False
        self.add_result("Live Stream", True, "Streaming successful")
        
        self.print_summary(True, "All tests passed")
        return True
