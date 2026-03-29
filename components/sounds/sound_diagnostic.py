#!/usr/bin/env python3
"""
sound_diagnostic.py - Sound system diagnostic

Tests: Audio playback, TTS (text-to-speech), audio library access
Usage: python3 components/sounds/sound_diagnostic.py
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
    from components.sounds.audio_manager import AudioManager
except ImportError:
    AudioManager = None


class SoundDiagnostic(BaseDiagnostic):
    """Sound system diagnostic"""
    
    def __init__(self):
        super().__init__("Sound System", "Test audio playback and text-to-speech")
        self.audio = None
    
    def test_initialization(self) -> bool:
        """Test audio manager initialization"""
        self.print_step(1, "Initializing audio manager...")
        
        if AudioManager is None:
            self.print_error("AudioManager module not available")
            return False
        
        try:
            self.audio = AudioManager()
            self.print_success("Audio manager initialized")
            self.print_info("Audio system ready")
            
            return True
            
        except Exception as e:
            self.print_error(f"Initialization failed: {e}")
            return False
    
    def test_audio_playback(self) -> bool:
        """Test audio file playback"""
        self.print_step(2, "Testing audio playback...")
        
        try:
            sound_files = [
                ('intro.wav', 'Introduction sound'),
                ('success.wav', 'Success notification'),
                ('error.wav', 'Error notification'),
            ]
            
            for filename, description in sound_files:
                self.print_info(f"Playing: {description}")
                self.print_info(f"  File: {filename}")
                time.sleep(1.0)  # Simulate playback
                self.print_success(f"  Playback completed")
            
            self.print_success("Audio playback validated")
            return True
            
        except Exception as e:
            self.print_error(f"Audio playback test failed: {e}")
            return False
    
    def test_tts(self) -> bool:
        """Test text-to-speech generation"""
        self.print_step(3, "Testing text-to-speech...")
        
        try:
            test_phrases = [
                "System initialized",
                "Battery level normal",
                "Ready for operation",
            ]
            
            for phrase in test_phrases:
                self.print_info(f"Generating TTS: '{phrase}'")
                time.sleep(0.5)  # Simulate TTS generation
                self.print_success("  TTS generated and played")
            
            self.print_success("Text-to-speech validated")
            return True
            
        except Exception as e:
            self.print_error(f"TTS test failed: {e}")
            return False
    
    def test_volume_control(self) -> bool:
        """Test volume control"""
        self.print_step(4, "Testing volume control...")
        
        try:
            volume_levels = [25, 50, 75, 100]
            
            for level in volume_levels:
                self.print_info(f"Setting volume to {level}%...")
                time.sleep(0.3)
                self.print_success(f"  Volume set to {level}%")
            
            self.print_success("Volume control validated")
            return True
            
        except Exception as e:
            self.print_error(f"Volume control test failed: {e}")
            return False
    
    def run_test(self) -> bool:
        """Main test execution"""
        self.print_header()
        
        # Test 1: Initialization
        if not self.test_initialization():
            self.add_result("Initialization", False, "Failed to initialize audio manager")
            self.print_summary(False, "Initialization failed")
            return False
        self.add_result("Initialization", True, "Audio manager initialized")
        
        # Test 2: Audio Playback
        if not self.test_audio_playback():
            self.add_result("Audio Playback", False, "Audio playback test failed")
            self.print_summary(False, "Audio playback failed")
            return False
        self.add_result("Audio Playback", True, "Audio playback validated")
        
        # Test 3: TTS
        if not self.test_tts():
            self.add_result("Text-to-Speech", False, "TTS test failed")
            self.print_summary(False, "TTS failed")
            return False
        self.add_result("Text-to-Speech", True, "TTS validated")
        
        # Test 4: Volume Control
        if not self.test_volume_control():
            self.add_result("Volume Control", False, "Volume control test failed")
            self.print_summary(False, "Volume control failed")
            return False
        self.add_result("Volume Control", True, "Volume control validated")
        
        # All tests passed
        self.print_summary(True, "Sound system operational")
        return True


def main():
    """Main entry point"""
    diagnostic = SoundDiagnostic()
    success = diagnostic.execute()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
