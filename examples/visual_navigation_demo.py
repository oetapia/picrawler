#!/usr/bin/env python3
"""
Visual Navigation Demo

Demonstrates how to integrate VilibDetector with autonomous navigation.
This example shows a robot that can:
1. Autonomously navigate while avoiding obstacles
2. Switch to visual seeking mode to find and approach colored targets
3. Return to autonomous navigation after reaching target

Usage:
    python examples/visual_navigation_demo.py

Controls:
    - Autonomous mode: Robot navigates avoiding obstacles
    - When red object detected, enters visual seeking mode
    - Approaches target using color detection
    - Returns to autonomous mode after reaching target
    
    Press Ctrl+C to stop
"""

from picrawler import Picrawler
from components.camera import VilibDetector
from components.sensors import DistanceSensor, SensorFusion
from components.navigation import MotionController, ObstacleHandler
from time import sleep
import sys


class VisualNavigationDemo:
    """
    Demo combining autonomous navigation with visual target seeking.
    """
    
    def __init__(self, target_color='red', detection_threshold=80):
        """
        Initialize the demo.
        
        Args:
            target_color: Color to seek ('red', 'blue', 'green', etc.)
            detection_threshold: Minimum width for "target reached"
        """
        print("Initializing Visual Navigation Demo...")
        
        # Core components
        self.crawler = Picrawler()
        self.detector = VilibDetector()
        
        # Navigation components
        self.distance_sensor = DistanceSensor()
        self.sensor_fusion = SensorFusion(self.distance_sensor)
        self.motion_controller = MotionController(self.crawler)
        self.obstacle_handler = ObstacleHandler(
            self.crawler,
            self.distance_sensor,
            self.sensor_fusion
        )
        
        # Configuration
        self.target_color = target_color
        self.detection_threshold = detection_threshold
        self.visual_mode = False
        self.running = False
        
        # Stats
        self.targets_reached = 0
        self.autonomous_steps = 0
        self.visual_steps = 0
    
    def start(self):
        """Start all systems"""
        print(f"Starting systems...")
        print(f"  - Target color: {self.target_color}")
        print(f"  - Detection threshold: {self.detection_threshold}")
        
        # Start camera
        self.detector.start_camera()
        self.detector.start_display(web=True)
        self.detector.enable_color_detection(self.target_color)
        
        print("  - Camera started ✓")
        print("  - Color detection enabled ✓")
        
        # Initialize sensors
        self.distance_sensor.start_reading()
        
        print("  - Distance sensor started ✓")
        print("\nSystem ready!")
        print(f"\nViewing camera stream at: http://localhost:9000/mjpg")
        print("Robot will autonomously navigate and seek {self.target_color} targets\n")
        
        self.running = True
    
    def stop(self):
        """Stop all systems"""
        print("\n\nStopping systems...")
        self.running = False
        
        self.detector.stop_camera()
        self.distance_sensor.stop_reading()
        self.crawler.do_step('stand', 50)
        
        print("Systems stopped ✓")
        self._print_stats()
    
    def _print_stats(self):
        """Print session statistics"""
        print("\n" + "="*50)
        print("SESSION STATISTICS")
        print("="*50)
        print(f"Targets reached:     {self.targets_reached}")
        print(f"Autonomous steps:    {self.autonomous_steps}")
        print(f"Visual seeking steps: {self.visual_steps}")
        total = self.autonomous_steps + self.visual_steps
        if total > 0:
            visual_pct = (self.visual_steps / total) * 100
            print(f"Visual mode time:    {visual_pct:.1f}%")
        print("="*50)
    
    def navigate_autonomous(self):
        """Perform one step of autonomous navigation"""
        self.autonomous_steps += 1
        
        # Read distance
        distance = self.distance_sensor.get_distance()
        
        if distance < 20:
            # Obstacle very close - back up and turn
            print(f"  [AUTO] Obstacle at {distance}cm - backing up")
            self.crawler.do_action('backward', 1, 60)
            self.crawler.do_action('turn_right', 2, 60)
        elif distance < 35:
            # Obstacle ahead - turn
            print(f"  [AUTO] Obstacle at {distance}cm - turning")
            self.crawler.do_action('turn_right', 1, 60)
        else:
            # Path clear - move forward
            print(f"  [AUTO] Path clear ({distance}cm) - moving forward")
            self.crawler.do_action('forward', 1, 70)
    
    def navigate_visual(self, result):
        """
        Perform one step of visual navigation.
        
        Args:
            result: DetectionResult from color detection
        """
        self.visual_steps += 1
        
        # Get direction to target
        direction = self.detector.get_color_direction(
            result,
            left_threshold=100,
            right_threshold=220
        )
        
        # Check if target is reached (large and centered)
        if result.width > self.detection_threshold and direction == 'center':
            print(f"  [VISUAL] ★ TARGET REACHED! (size: {result.width})")
            self.targets_reached += 1
            self.visual_mode = False
            
            # Celebrate
            self.crawler.do_step('stand', 80)
            sleep(0.5)
            
            return
        
        # Navigate toward target
        if direction == 'left':
            print(f"  [VISUAL] Target left (x:{result.x}, w:{result.width}) - turning left")
            self.crawler.do_action('turn_left', 1, 60)
        elif direction == 'right':
            print(f"  [VISUAL] Target right (x:{result.x}, w:{result.width}) - turning right")
            self.crawler.do_action('turn_right', 1, 60)
        else:  # center
            print(f"  [VISUAL] Target centered (w:{result.width}) - approaching")
            self.crawler.do_action('forward', 1, 80)
    
    def run_step(self):
        """Execute one navigation step"""
        # Check for visual target
        result = self.detector.get_color_detection()
        
        if result.detected:
            if not self.visual_mode:
                print(f"\n→ {self.target_color.upper()} TARGET DETECTED! Entering visual mode...")
                self.visual_mode = True
            
            # Visual navigation mode
            self.navigate_visual(result)
        else:
            if self.visual_mode:
                print(f"\n← Target lost. Returning to autonomous mode...")
                self.visual_mode = False
            
            # Autonomous navigation mode
            self.navigate_autonomous()
        
        sleep(0.1)
    
    def run(self, duration=None):
        """
        Run the demo.
        
        Args:
            duration: Run for specified seconds (None = indefinitely)
        """
        import time
        start_time = time.time()
        
        try:
            while self.running:
                self.run_step()
                
                # Check duration
                if duration and (time.time() - start_time) > duration:
                    print(f"\nDuration limit ({duration}s) reached")
                    break
        
        except KeyboardInterrupt:
            print("\n\nKeyboard interrupt received")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visual Navigation Demo')
    parser.add_argument(
        '--color',
        default='red',
        choices=['red', 'orange', 'yellow', 'green', 'blue', 'purple'],
        help='Target color to seek'
    )
    parser.add_argument(
        '--threshold',
        type=int,
        default=80,
        help='Detection threshold for "target reached"'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Run duration in seconds (default: indefinite)'
    )
    
    args = parser.parse_args()
    
    # Create and run demo
    demo = VisualNavigationDemo(
        target_color=args.color,
        detection_threshold=args.threshold
    )
    
    try:
        demo.start()
        demo.run(duration=args.duration)
    finally:
        demo.stop()


if __name__ == '__main__':
    main()
