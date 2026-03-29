"""
Diagnostics Module
==================

Unified diagnostic system for PiCrawler hardware testing.

This module provides:
- BaseDiagnostic: Standard base class for all diagnostic tools
- Unified output formatting and result tracking
- Consistent error handling and reporting

Usage:
    from components.diagnostics import BaseDiagnostic
    
    class MyDiagnostic(BaseDiagnostic):
        def run_test(self):
            # Your test logic
            pass
"""

from .base import BaseDiagnostic, DiagnosticResult

__all__ = ['BaseDiagnostic', 'DiagnosticResult']
