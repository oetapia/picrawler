#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PiCrawler REST API Server

Provides a web-based control interface for manual robot control.
Displays IP address on OLED for easy connection.
"""
import sys
import os
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import json
import time
from datetime import datetime
from flask import request, jsonify, send_from_directory

# Check if terminal supports UTF-8 output
def safe_print(message):
    """Print with fallback for terminals that don't support UTF-8"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        print(ascii_message)

# Safe emoji/icon functions
def get_icon(emoji, fallback):
    """Get emoji if supported, otherwise return fallback"""
    try:
        # Test if we can encode the emoji
        emoji.encode(sys.stdout.encoding or 'utf-8')
        return emoji
    except (UnicodeEncodeError, AttributeError):
        return fallback

# Define icons with fallbacks
ICONS = {
    'spider': get_icon('🕷️', '[SPIDER]'),
    'robot': get_icon('🤖', '[ROBOT]'), 
    'check': get_icon('✅', '[OK]'),
    'error': get_icon('❌', '[ERROR]'),
    'network': get_icon('🌐', '[NET]'),
    'link': get_icon('🔗', '[LINK]'),
    'mobile': get_icon('📱', '[MOBILE]'),
    'lightning': get_icon('⚡', '[API]'),
    'gamepad': get_icon('🎮', '[CTRL]'),
    'stop': get_icon('🛑', '[STOP]'),
    'recycle': get_icon('🔄', '[CLEAN]')
}

# Import your existing modules
from picrawler import Picrawler
from robot_hat import TTS
from components.screens import imageConvert, oled
from components.server.flask import create_app

# Initialize global objects
app = create_app(__name__, cors=True)
crawler = Picrawler()
tts = TTS()

# Global state variables
current_speed = 80
current_pose = "spread_out"
robot_status = "ready"

_POSES_FILE = os.path.join(os.path.dirname(__file__), '../../components/motion/poses.json')
with open(_POSES_FILE) as f:
    poses = json.load(f)

spread_out      = poses["spread_out"]
compact         = poses["compact"]
wave_1          = poses["wave_1"]
wave_2          = poses["wave_2"]
smelling_ground = poses["smelling_ground"]
looking_at_sky  = poses["looking_at_sky"]
lean_left       = poses["lean_left"]
lean_right      = poses["lean_right"]

def get_local_ip():
    """Get the local IP address of the Pi"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def custom_steps(values, speed=None):
    """Execute custom step with given pose values"""
    global current_speed
    if speed is None:
        speed = current_speed
    
    print(f"New step: {values}")
    crawler.do_step(values, speed)
    time.sleep(0.1)

def create_response(success=True, message="", data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    if data:
        response.update(data)
    return jsonify(response)

_CLIENT_DIR = os.path.join(os.path.dirname(__file__), '../client')

@app.route('/')
def web_ui():
    """Serve the web UI"""
    return send_from_directory(_CLIENT_DIR, 'webui.html')

# API Routes
@app.route('/api/status')
def api_status():
    """Get current robot status"""
    try:
        status_data = {
            'speed': current_speed,
            'pose': current_pose,
            'status': robot_status,
            'timestamp': datetime.now().isoformat()
        }
        return create_response(True, f"Status: {robot_status}, Speed: {current_speed}, Pose: {current_pose}", status_data)
    except Exception as e:
        return create_response(False, f"Status error: {str(e)}")

@app.route('/api/movement/<direction>', methods=['POST'])
def api_movement(direction):
    """Handle movement commands"""
    global robot_status
    
    try:
        robot_status = f"moving_{direction}"
        
        if direction == 'forward':
            crawler.do_action('forward', 1, current_speed)
            message = "Moving forward"
        elif direction == 'backward':
            crawler.do_action('backward', 1, current_speed)
            message = "Moving backward"
        elif direction == 'turn_left':
            crawler.do_action('turn left', 1, current_speed)
            message = "Turning left"
        elif direction == 'turn_right':
            crawler.do_action('turn right', 1, current_speed)
            message = "Turning right"
        else:
            return create_response(False, f"Unknown direction: {direction}")
        
        robot_status = "ready"
        return create_response(True, message)
        
    except Exception as e:
        robot_status = "error"
        return create_response(False, f"Movement error: {str(e)}")

@app.route('/api/pose/<pose_name>', methods=['POST'])
def api_pose(pose_name):
    """Handle pose commands"""
    global current_pose, robot_status
    
    try:
        if pose_name not in poses:
            return create_response(False, f"Unknown pose: {pose_name}")
        
        robot_status = f"setting_pose_{pose_name}"
        custom_steps(poses[pose_name])
        current_pose = pose_name
        robot_status = "ready"
        
        return create_response(True, f"Set pose to {pose_name.replace('_', ' ')}")
        
    except Exception as e:
        robot_status = "error"
        return create_response(False, f"Pose error: {str(e)}")

@app.route('/api/action/<action_name>', methods=['POST'])
def api_action(action_name):
    """Handle special action commands"""
    global robot_status
    
    try:
        robot_status = f"performing_{action_name}"
        
        if action_name == 'wave':
            # Simple wave - just the arm movement
            custom_steps(wave_1)
            time.sleep(0.4)
            custom_steps(wave_2)
            time.sleep(0.4)
            custom_steps(wave_1)
            time.sleep(0.4)
            custom_steps(spread_out)  # Return to neutral
            message = "Waving completed"
            
        elif action_name == 'greeting':
            # Full greeting sequence with speech and multiple poses
            custom_steps(wave_1)
            time.sleep(0.3)
            custom_steps(wave_2)
            time.sleep(0.3)
            custom_steps(wave_1)
            time.sleep(0.3)
            tts.say("Hello there!")
            time.sleep(0.5)
            custom_steps(looking_at_sky)  # Look up
            time.sleep(0.5)
            custom_steps(smelling_ground)  # Look down
            time.sleep(0.5)
            custom_steps(spread_out)  # Return to neutral
            message = "Full greeting completed"
            
        elif action_name == 'dance':
            # Dance sequence using lean poses
            custom_steps(lean_left)
            time.sleep(0.4)
            custom_steps(lean_right)
            time.sleep(0.4)
            custom_steps(lean_left)
            time.sleep(0.4)
            custom_steps(lean_right)
            time.sleep(0.4)
            custom_steps(wave_1)
            time.sleep(0.3)
            custom_steps(wave_2)
            time.sleep(0.3)
            custom_steps(spread_out)
            message = "Dance completed"
            
        elif action_name == 'stretch':
            # Stretch sequence - all extreme poses
            custom_steps(compact)
            time.sleep(0.5)
            custom_steps(spread_out)
            time.sleep(0.5)
            custom_steps(looking_at_sky)
            time.sleep(0.5)
            custom_steps(smelling_ground)
            time.sleep(0.5)
            custom_steps(lean_left)
            time.sleep(0.5)
            custom_steps(lean_right)
            time.sleep(0.5)
            custom_steps(spread_out)
            message = "Stretch routine completed"
            
        else:
            return create_response(False, f"Unknown action: {action_name}")
        
        robot_status = "ready"
        return create_response(True, message)
        
    except Exception as e:
        robot_status = "error"
        return create_response(False, f"Action error: {str(e)}")

@app.route('/api/speed/<int:speed>', methods=['POST'])
def api_speed(speed):
    """Set movement speed"""
    global current_speed
    
    try:
        current_speed = max(10, min(100, speed))
        return create_response(True, f"Speed set to {current_speed}")
    except Exception as e:
        return create_response(False, f"Speed error: {str(e)}")

@app.route('/api/speak', methods=['POST'])
def api_speak():
    """Handle text-to-speech"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return create_response(False, "No text provided")
        
        # Limit text length for safety
        text = text[:100]
        tts.say(text)
        oled.update_display(header="Speaking:", text=text)
        return create_response(True, f"Speaking: '{text}'")
        
    except Exception as e:
        return create_response(False, f"Speech error: {str(e)}")

@app.route('/api/emergency_stop', methods=['POST'])
def api_emergency_stop():
    """Emergency stop - return to safe position"""
    global robot_status, current_pose
    
    try:
        robot_status = "emergency_stop"
        custom_steps(spread_out)  # Safe neutral position
        current_pose = "spread_out"
        robot_status = "ready"
        
        return create_response(True, "Emergency stop activated - robot in safe position")
        
    except Exception as e:
        return create_response(False, f"Emergency stop error: {str(e)}")


def initialize_robot():
    """Initialize robot systems"""
    try:
        safe_print(f"{ICONS['robot']} Initializing PiCrawler systems...")
        
        # Initialize image conversion
        imageConvert.main()
        
        # Set initial pose
        custom_steps(spread_out)
        
        # Say hello
        time.sleep(1)
        tts.say("PiCrawler API server ready")
        
        safe_print(f"{ICONS['check']} Robot initialization complete")
        return True
        
    except Exception as e:
        safe_print(f"{ICONS['error']} Robot initialization failed: {e}")
        return False

def main():
    """Main server function"""
    safe_print(f"{ICONS['spider']} PiCrawler REST API Server Starting...")
    
    # Initialize robot
    if not initialize_robot():
        safe_print(f"{ICONS['error']} Failed to initialize robot. Exiting...")
        return
    
    # Get local IP
    local_ip = get_local_ip()
    port = 5000
    
    # Display IP address on OLED screen
    oled.update_display(header="Manual Control", text=f'{local_ip}:{port}')
    
    safe_print(f"{ICONS['network']} Starting server on {local_ip}:{port}")
    safe_print(f"{ICONS['mobile']} Web UI: http://{local_ip}:{port}/")
    safe_print(f"{ICONS['lightning']} API endpoints available:")
    safe_print(f"   - GET  http://{local_ip}:{port}/api/status")
    safe_print(f"   - POST http://{local_ip}:{port}/api/movement/<direction>")
    safe_print(f"   - POST http://{local_ip}:{port}/api/pose/<pose_name>")
    safe_print(f"   - POST http://{local_ip}:{port}/api/action/<action_name>")
    safe_print(f"   - POST http://{local_ip}:{port}/api/speed/<speed>")
    safe_print(f"   - POST http://{local_ip}:{port}/api/speak")
    safe_print(f"   - POST http://{local_ip}:{port}/api/emergency_stop")
    safe_print(f"\n{ICONS['gamepad']} Press Ctrl+C to stop the server")
    
    try:
        # Start Flask server
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        safe_print(f"\n{ICONS['stop']} Server stopped by user")
    except Exception as e:
        safe_print(f"{ICONS['error']} Server error: {e}")
    finally:
        safe_print(f"{ICONS['recycle']} Cleaning up...")
        try:
            custom_steps(compact)  # Return to safe position
        except:
            pass

if __name__ == '__main__':
    main()
