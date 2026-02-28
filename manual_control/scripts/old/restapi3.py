#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import socket
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import numpy as np

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

# Add the 'components' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../components')))

# Import your existing modules
from picrawler import Picrawler
from robot_hat import TTS
from screens import imageConvert

# Initialize global objects
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
crawler = Picrawler()
tts = TTS()

# Global state variables
current_speed = 80
current_pose = "spread_out"
robot_status = "ready"

# IMPROVED POSE DEFINITIONS
# Basic poses
spread_out = np.array([[45, 45, -45], [45, 45, -45], [45, 45, -45], [45, 45, -45]])
compact = np.array([[45, 0, 0], [45, 0, 0], [45, 45, 0], [45, 45, 0]])

# Wave poses - more distinct differences
wave_1 = np.array([[45, 45, -45], [-15, 90, 60], [45, 45, -45], [45, 45, -45]])  # Right arm up high
wave_2 = np.array([[45, 45, -45], [15, 45, 30], [45, 45, -45], [45, 45, -45]])   # Right arm mid position

# Look up/down poses
smelling_ground = np.array([[30, 30, -30], [30, 30, -30], [60, 45, -75], [60, 45, -75]])  # Front legs down, back legs up
looking_at_sky = np.array([[60, 45, -75], [60, 45, -75], [30, 30, -30], [30, 30, -30]])   # Front legs up, back legs down

# NEW LEAN POSES - Left and Right
lean_left = np.array([[60, 45, -75], [30, 30, -30], [60, 45, -75], [30, 30, -30]])   # Left legs up, right legs down
lean_right = np.array([[30, 30, -30], [60, 45, -75], [30, 30, -30], [60, 45, -75]])  # Right legs up, left legs down

# Store pose mappings
poses = {
    "spread_out": spread_out,
    "compact": compact,
    "wave_1": wave_1,
    "wave_2": wave_2,
    "smelling_ground": smelling_ground,
    "looking_at_sky": looking_at_sky,
    "lean_left": lean_left,
    "lean_right": lean_right
}

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
    
    print(f"New step: {values.tolist()}")
    crawler.do_step(values.tolist(), speed)
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

# Web interface HTML template
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>PiCrawler Robot Control</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        .status { 
            background: linear-gradient(45deg, #e9ecef, #f8f9fa);
            padding: 20px; 
            margin: 20px 0; 
            border-radius: 15px;
            border-left: 6px solid #007bff;
            font-weight: bold;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .status.connected { 
            background: linear-gradient(45deg, #d4edda, #c3e6cb);
            border-left-color: #28a745; 
            color: #155724;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }
        .control { 
            padding: 25px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            border: 1px solid rgba(222, 226, 230, 0.8);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .control:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }
        .control h3 {
            margin-top: 0;
            color: #495057;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
            font-size: 1.3em;
        }
        button { 
            padding: 15px 25px; 
            margin: 8px; 
            font-size: 16px; 
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }
        button:active {
            transform: translateY(0);
        }
        .movement-btn { 
            background: linear-gradient(45deg, #28a745, #20c997); 
            color: white; 
            min-width: 120px;
        }
        .movement-btn:hover { background: linear-gradient(45deg, #218838, #1ea085); }
        
        .pose-btn { 
            background: linear-gradient(45deg, #007bff, #6610f2); 
            color: white; 
            min-width: 120px;
        }
        .pose-btn:hover { background: linear-gradient(45deg, #0056b3, #520dc2); }
        
        .action-btn { 
            background: linear-gradient(45deg, #fd7e14, #e83e8c); 
            color: white; 
            min-width: 120px;
        }
        .action-btn:hover { background: linear-gradient(45deg, #e8660c, #d91a72); }
        
        .stop-btn { 
            background: linear-gradient(45deg, #dc3545, #c82333); 
            color: white; 
            min-width: 120px;
        }
        .stop-btn:hover { background: linear-gradient(45deg, #c82333, #a71e2a); }
        
        .slider-container {
            margin: 20px 0;
            padding: 15px;
            background: rgba(248, 249, 250, 0.8);
            border-radius: 10px;
        }
        .slider-container label {
            display: block;
            margin-bottom: 12px;
            font-weight: bold;
            color: #495057;
            font-size: 1.1em;
        }
        .slider-wrapper {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .slider {
            flex: 1;
            height: 10px;
            border-radius: 5px;
            background: linear-gradient(to right, #ddd, #007bff);
            outline: none;
            -webkit-appearance: none;
        }
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: linear-gradient(45deg, #007bff, #0056b3);
            cursor: pointer;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
        }
        .value-display {
            min-width: 80px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            color: #495057;
            background: white;
            padding: 8px 15px;
            border-radius: 8px;
            border: 2px solid #dee2e6;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .dpad {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            margin: 20px 0;
            justify-items: center;
        }
        .dpad button {
            width: 70px;
            height: 70px;
            font-size: 24px;
            margin: 0;
            border-radius: 50%;
        }
        .dpad .empty { visibility: hidden; }
        
        .pose-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin: 15px 0;
        }
        
        .message-input {
            display: flex;
            gap: 12px;
            margin: 20px 0;
        }
        .message-input input {
            flex: 1;
            padding: 15px;
            border: 2px solid #dee2e6;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .message-input input:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 10px rgba(0,123,255,0.3);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            .control-grid {
                grid-template-columns: 1fr;
            }
            .dpad button {
                width: 60px;
                height: 60px;
                font-size: 20px;
            }
        }
        
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .pulse {
            animation: pulse 0.5s;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🕷️ PiCrawler Control Center</h1>
        <p class="subtitle">Advanced Quadruped Robot Control Interface</p>
        <div class="status connected" id="status">✅ Connected - Ready to Control!</div>
        
        <div class="control-grid">
            <div class="control">
                <h3>🎮 Movement Control</h3>
                <div class="dpad">
                    <div class="empty"></div>
                    <button class="movement-btn" onclick="sendMovement('forward')">⬆️</button>
                    <div class="empty"></div>
                    <button class="movement-btn" onclick="sendMovement('turn_left')">⬅️</button>
                    <button class="stop-btn" onclick="emergencyStop()">⏹️</button>
                    <button class="movement-btn" onclick="sendMovement('turn_right')">➡️</button>
                    <div class="empty"></div>
                    <button class="movement-btn" onclick="sendMovement('backward')">⬇️</button>
                    <div class="empty"></div>
                </div>
            </div>
            
            <div class="control">
                <h3>⚙️ Speed Control</h3>
                <div class="slider-container">
                    <label>Movement Speed:</label>
                    <div class="slider-wrapper">
                        <span>0</span>
                        <input type="range" id="speedSlider" class="slider" min="10" max="100" value="80" 
                               oninput="updateSpeedDisplay(this.value)" onchange="setSpeed(this.value)">
                        <span>100</span>
                    </div>
                    <div class="value-display" id="speedDisplay">80</div>
                </div>
                <button class="action-btn" onclick="getStatus()">📊 Get Status</button>
            </div>
            
            <div class="control">
                <h3>🤖 Basic Poses</h3>
                <div class="pose-grid">
                    <button class="pose-btn" onclick="sendPose('spread_out')">🕷️ Spread</button>
                    <button class="pose-btn" onclick="sendPose('compact')">📦 Compact</button>
                    <button class="action-btn" onclick="sendAction('wave')">👋 Wave</button>
                </div>
            </div>
            
            <div class="control">
                <h3>↕️ Vertical Poses</h3>
                <div class="pose-grid">
                    <button class="pose-btn" onclick="sendPose('smelling_ground')">👃 Look Down</button>
                    <button class="pose-btn" onclick="sendPose('looking_at_sky')">👆 Look Up</button>
                </div>
            </div>
            
            <div class="control">
                <h3>↔️ Lean Poses</h3>
                <div class="pose-grid">
                    <button class="pose-btn" onclick="sendPose('lean_left')">⬅️ Lean Left</button>
                    <button class="pose-btn" onclick="sendPose('lean_right')">➡️ Lean Right</button>
                </div>
            </div>
            
            <div class="control">
                <h3>🎭 Special Actions</h3>
                <div class="pose-grid">
                    <button class="action-btn" onclick="sendAction('greeting')">👋 Full Greeting</button>
                    <button class="action-btn" onclick="sendAction('dance')">💃 Dance</button>
                    <button class="action-btn" onclick="sendAction('stretch')">🤸 Stretch</button>
                </div>
            </div>
            
            <div class="control">
                <h3>💬 Text-to-Speech</h3>
                <div class="message-input">
                    <input type="text" id="messageInput" placeholder="Type message for robot to say..." maxlength="100">
                    <button class="action-btn" onclick="sendMessage()">🔊 Speak</button>
                </div>
                <button class="action-btn" onclick="sendMessage('Hello, I am PiCrawler!')">👋 Say Hello</button>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        
        function updateStatus(message, isSuccess = true) {
            const status = document.getElementById('status');
            status.textContent = isSuccess ? `✅ ${message}` : `⚠️ ${message}`;
            status.className = isSuccess ? 'status connected' : 'status';
            status.classList.add('pulse');
            setTimeout(() => status.classList.remove('pulse'), 500);
        }
        
        function setLoading(loading) {
            isLoading = loading;
            document.body.classList.toggle('loading', loading);
        }
        
        function updateSpeedDisplay(value) {
            document.getElementById('speedDisplay').textContent = value;
        }
        
        function sendMovement(direction) {
            if (isLoading) return;
            setLoading(true);
            
            fetch(`/api/movement/${direction}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message, data.success);
                })
                .catch(error => {
                    updateStatus('Movement command failed', false);
                    console.error('Movement error:', error);
                })
                .finally(() => setLoading(false));
        }
        
        function sendPose(pose) {
            if (isLoading) return;
            setLoading(true);
            
            fetch(`/api/pose/${pose}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message, data.success);
                })
                .catch(error => {
                    updateStatus('Pose command failed', false);
                    console.error('Pose error:', error);
                })
                .finally(() => setLoading(false));
        }
        
        function sendAction(action) {
            if (isLoading) return;
            setLoading(true);
            
            fetch(`/api/action/${action}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message, data.success);
                })
                .catch(error => {
                    updateStatus('Action command failed', false);
                    console.error('Action error:', error);
                })
                .finally(() => setLoading(false));
        }
        
        function setSpeed(speed) {
            fetch(`/api/speed/${speed}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message, data.success);
                })
                .catch(error => {
                    updateStatus('Speed change failed', false);
                    console.error('Speed error:', error);
                });
        }
        
        function sendMessage(customMessage = null) {
            const message = customMessage || document.getElementById('messageInput').value.trim();
            if (!message) {
                updateStatus('Please enter a message', false);
                return;
            }
            
            if (isLoading) return;
            setLoading(true);
            
            fetch('/api/speak', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: message})
            })
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message, data.success);
                    if (data.success && !customMessage) {
                        document.getElementById('messageInput').value = '';
                    }
                })
                .catch(error => {
                    updateStatus('Speech command failed', false);
                    console.error('Speech error:', error);
                })
                .finally(() => setLoading(false));
        }
        
        function getStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.message, data.success);
                    if (data.success && data.speed) {
                        document.getElementById('speedSlider').value = data.speed;
                        updateSpeedDisplay(data.speed);
                    }
                })
                .catch(error => {
                    updateStatus('Status request failed', false);
                    console.error('Status error:', error);
                });
        }
        
        function emergencyStop() {
            fetch('/api/emergency_stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    updateStatus('Emergency stop activated!', data.success);
                })
                .catch(error => {
                    updateStatus('Emergency stop failed', false);
                    console.error('Emergency stop error:', error);
                });
        }
        
        // Allow Enter key to send message
        document.getElementById('messageInput').addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            if (event.target.tagName.toLowerCase() === 'input') {
                return; // Allow normal typing in input fields
            }
            
            switch(event.key.toLowerCase()) {
                case 'w': case 'arrowup': sendMovement('forward'); break;
                case 's': case 'arrowdown': sendMovement('backward'); break;
                case 'a': case 'arrowleft': sendMovement('turn_left'); break;
                case 'd': case 'arrowright': sendMovement('turn_right'); break;
                case ' ': emergencyStop(); event.preventDefault(); break;
            }
        });
        
        // Initial status check
        setTimeout(getStatus, 1000);
        
        // Auto-refresh status every 30 seconds
        setInterval(getStatus, 30000);
    </script>
</body>
</html>'''

# API Routes
@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template_string(HTML_TEMPLATE)

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
    
    safe_print(f"{ICONS['network']} Starting web server on {local_ip}:{port}")
    safe_print(f"{ICONS['link']} Access the control interface at: http://{local_ip}:{port}")
    safe_print(f"{ICONS['mobile']} The interface is mobile-friendly and works on any device")
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
            custom_steps(spread_out)  # Return to safe position
        except:
            pass

if __name__ == '__main__':
    main()
