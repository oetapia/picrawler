#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Photo Logger for ML Dataset Creation

Lightweight photo capture using picamera2 (SimpleCamera) for efficient
dataset collection. Photos are captured at configurable rate and saved
asynchronously to minimize navigation impact.
"""

import os
import time
from datetime import datetime
from pathlib import Path
import threading
import queue


class PhotoLogger:
    """
    Lightweight photo capture for ML dataset creation.
    Uses picamera2 (SimpleCamera) for fast, efficient capture.
    
    Features:
    - Throttled capture (configurable Hz)
    - Async disk writes (non-blocking)
    - Auto-labeling support
    - Session-based organization
    """
    
    def __init__(self, session_dir, 
                 resolution=(320, 240),
                 capture_rate_hz=2.0):
        """
        Initialize photo logger.
        
        Args:
            session_dir: Session directory for photos
            resolution: Photo size (width, height)
            capture_rate_hz: Photos per second (1-5 Hz recommended)
        """
        # Directory setup
        self.session_dir = Path(session_dir)
        self.photos_dir = self.session_dir / "photos"
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        
        # Camera setup (deferred until start())
        self.camera = None
        self.resolution = resolution
        
        # Capture control
        self.capture_rate_hz = capture_rate_hz
        self.capture_interval = 1.0 / capture_rate_hz
        self.last_capture_time = 0
        
        # Frame counter
        self.frame_count = 0
        
        # Async save queue
        self.save_queue = queue.Queue(maxsize=50)
        self.save_thread = None
        self.running = False
        
        print(f"[EMOJI] Photo logger initialized")
        print(f"   Photos dir: {self.photos_dir}")
        print(f"   Resolution: {resolution[0]}x{resolution[1]}")
        print(f"   Capture rate: {capture_rate_hz} Hz")
    
    def start(self):
        """Start camera and save thread."""
        # Import here to avoid dependency issues
        from components.camera.simple_camera import SimpleCamera
        
        self.camera = SimpleCamera(size=self.resolution)
        self.camera.start()
        time.sleep(0.5)  # Camera warmup
        
        # Start async save thread
        self.running = True
        self.save_thread = threading.Thread(target=self._save_worker, daemon=True)
        self.save_thread.start()
        
        print("[EMOJI] Photo logger camera started")
    
    def capture_if_ready(self, sensor_data=None, label=None):
        """
        Capture photo if enough time has passed (throttled).
        
        Args:
            sensor_data: Optional sensor readings to include in manifest
            label: Optional label for this photo
        
        Returns:
            dict: Photo metadata if captured, None otherwise
        """
        current_time = time.time()
        
        if current_time - self.last_capture_time < self.capture_interval:
            return None  # Too soon
        
        self.last_capture_time = current_time
        return self._capture_now(sensor_data, label)
    
    def _capture_now(self, sensor_data=None, label=None):
        """Capture photo immediately."""
        if not self.camera:
            return None
        
        try:
            # Get frame from camera
            frame_bytes = self.camera.get_frame()
            
            if not frame_bytes:
                return None
            
            # Generate filename
            self.frame_count += 1
            filename = f"frame_{self.frame_count:06d}.jpg"
            filepath = self.photos_dir / filename
            
            # Create metadata
            metadata = {
                'frame_id': self.frame_count,
                'timestamp': time.time(),
                'filename': filename,
                'filepath': str(filepath),
                'label': label,
                'sensor_data': sensor_data
            }
            
            # Queue for async save
            self.save_queue.put((frame_bytes, metadata))
            
            return metadata
            
        except Exception as e:
            print(f"[EMOJI] Photo capture failed: {e}")
            return None
    
    def _save_worker(self):
        """Background thread for async photo saving."""
        while self.running:
            try:
                # Get from queue with timeout
                frame_bytes, metadata = self.save_queue.get(timeout=1.0)
                
                # Save to disk
                with open(metadata['filepath'], 'wb') as f:
                    f.write(frame_bytes)
                
                self.save_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[EMOJI] Photo save failed: {e}")
    
    def stop(self):
        """Stop photo logger and cleanup."""
        print("\n[EMOJI] Stopping photo logger...")
        
        # Stop capture
        self.running = False
        
        # Wait for queue to empty (with timeout)
        try:
            self.save_queue.join()
        except:
            pass
        
        # Stop camera
        if self.camera:
            try:
                self.camera.stop()
            except:
                pass
        
        # Stats
        print(f"[EMOJI] Photo logger stopped")
        print(f"   Total photos: {self.frame_count}")
        print(f"   Location: {self.photos_dir}")
    
    def get_stats(self):
        """Get capture statistics."""
        return {
            'frames_captured': self.frame_count,
            'photos_dir': str(self.photos_dir),
            'queue_size': self.save_queue.qsize()
        }


# ============================================================================
# MAIN - For testing
# ============================================================================

def main():
    """Test photo logger."""
    print("Testing PhotoLogger...")
    
    # Create logger
    logger = PhotoLogger(
        session_dir="self_aware/logs/test_photos",
        resolution=(320, 240),
        capture_rate_hz=2.0
    )
    
    logger.start()
    
    # Capture some test photos
    print("\nCapturing 10 test photos...")
    for i in range(20):
        metadata = logger.capture_if_ready(
            sensor_data={'distance': 25.5 + i},
            label=f"test_{i}"
        )
        if metadata:
            print(f"  Captured: {metadata['filename']}")
        time.sleep(0.3)  # Try at 3.3 Hz, will throttle to 2 Hz
    
    # Stats
    stats = logger.get_stats()
    print(f"\n[EMOJI] Capture complete!")
    print(f"  Photos: {stats['frames_captured']}")
    print(f"  Queue: {stats['queue_size']} pending")
    
    # Stop
    logger.stop()


if __name__ == '__main__':
    main()
