"""
web_controller.py - Web interface for controlling the Pathfinder Kit
"""

import os
import time
import json
import threading
from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path

# Add parent directory to path to allow imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ComponentClass.IntegratedClass import PathfinderKit, PathfinderConfig

# Configuration
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables
kit = None
control_active = False
control_thread = None
current_speed = 50
current_turn = 0  # -100 (full left) to 100 (full right)

def control_loop():
    """Background thread for handling robot movement"""
    global kit, control_active, current_speed, current_turn
    
    while control_active and kit is not None:
        try:
            if current_speed == 0 and current_turn == 0:
                kit.stop()
            else:
                # Calculate motor speeds based on turn and speed
                left_speed = current_speed - current_turn
                right_speed = current_speed + current_turn
                
                # Normalize speeds to 0-100 range
                max_speed = max(abs(left_speed), abs(right_speed))
                if max_speed > 100:
                    left_speed = int(left_speed * 100 / max_speed)
                    right_speed = int(right_speed * 100 / max_speed)
                
                # Apply speeds
                kit.motors.set_speeds(left_speed, right_speed)
            
            time.sleep(0.05)
        except Exception as e:
            print(f"Error in control loop: {e}")
            break

@app.route('/')
def index():
    """Render the main control page"""
    return render_template('index.html')

@app.route('/api/control', methods=['POST'])
def control():
    """Handle control commands"""
    global control_active, control_thread, current_speed, current_turn
    
    data = request.json
    command = data.get('command')
    
    if command == 'start':
        if not control_active:
            control_active = True
            control_thread = threading.Thread(target=control_loop)
            control_thread.daemon = True
            control_thread.start()
        return jsonify({'status': 'started'})
    
    elif command == 'stop':
        control_active = False
        if kit:
            kit.stop()
        return jsonify({'status': 'stopped'})
    
    elif command == 'move':
        current_speed = data.get('speed', 0)
        current_turn = data.get('turn', 0)
        return jsonify({'status': 'moving', 'speed': current_speed, 'turn': current_turn})
    
    elif command == 'capture':
        if kit and kit.camera:
            filename = f"capture_{int(time.time())}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            kit.capture_image(filename=filepath)
            return jsonify({
                'status': 'captured', 
                'image_url': f'/uploads/{filename}'
            })
        return jsonify({'status': 'error', 'message': 'Camera not available'})
    
    return jsonify({'status': 'unknown_command'})

@app.route('/api/status')
def status():
    """Get robot status"""
    if kit is None:
        return jsonify({'status': 'error', 'message': 'Robot not initialized'})
    
    return jsonify({
        'status': 'ok',
        'obstacle_detected': kit.is_obstacle_detected(),
        'obstacle_distance': kit.get_obstacle_distance(),
        'speed': current_speed,
        'turn': current_turn
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def init_robot():
    """Initialize the robot"""
    global kit
    
    try:
        # Try to load config, use defaults if not found
        config = PathfinderConfig()
        
        # Initialize the robot
        kit = PathfinderKit(config=config)
        if not kit.setup():
            print("Failed to initialize robot")
            return False
            
        return True
    except Exception as e:
        print(f"Error initializing robot: {e}")
        return False

def cleanup():
    """Cleanup resources"""
    global control_active, kit
    
    control_active = False
    if kit:
        kit.cleanup()

if __name__ == '__main__':
    # Initialize the robot
    if init_robot():
        print("Robot initialized successfully")
        
        try:
            # Start the web server
            app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            cleanup()
    else:
        print("Failed to initialize robot. Starting web interface in simulation mode.")
        app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
