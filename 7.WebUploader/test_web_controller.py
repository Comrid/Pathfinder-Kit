"""
test_web_controller.py - Test script for the web controller without hardware dependencies
"""

import os
import time
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mock robot state
class MockRobot:
    def __init__(self):
        self.speed = 0
        self.turn = 0
        self.obstacle_distance = 100.0  # Default distance in cm
        
    def move(self, speed, turn):
        self.speed = max(-100, min(100, speed))  # Clamp between -100 and 100
        self.turn = max(-100, min(100, turn))    # Clamp between -100 and 100
        print(f"Moving - Speed: {self.speed}%, Turn: {self.turn}%")
        
    def stop(self):
        self.speed = 0
        self.turn = 0
        print("Stopped")
        
    def get_obstacle_distance(self):
        # Simulate obstacle detection
        return self.obstacle_distance
        
    def is_obstacle_detected(self, threshold=30):
        # Simulate obstacle detection
        return self.obstacle_distance < threshold
        
    def capture_image(self, filename):
        # Create a simple test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(img, "Test Image", (50, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
        cv2.putText(img, f"Speed: {self.speed}% Turn: {self.turn}%", 
                    (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Save the image
        cv2.imwrite(filename, img)
        return {
            'status': 'captured',
            'filename': os.path.basename(filename),
            'image': img
        }

# Global variables
robot = MockRobot()
control_active = False
control_thread = None
current_speed = 0
current_turn = 0

def control_loop():
    """Background thread for handling robot movement"""
    global robot, control_active, current_speed, current_turn
    
    while control_active:
        try:
            if current_speed == 0 and current_turn == 0:
                robot.stop()
            else:
                robot.move(current_speed, current_turn)
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
        robot.stop()
        current_speed = 0
        current_turn = 0
        return jsonify({'status': 'stopped'})
    
    elif command == 'move':
        current_speed = data.get('speed', 0)
        current_turn = data.get('turn', 0)
        return jsonify({'status': 'moving', 'speed': current_speed, 'turn': current_turn})
    
    elif command == 'capture':
        filename = f"capture_{int(time.time())}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        result = robot.capture_image(filepath)
        return jsonify({
            'status': 'captured', 
            'image_url': f'/uploads/{filename}'
        })
    
    return jsonify({'status': 'unknown_command'})

@app.route('/api/status')
def status():
    """Get robot status"""
    return jsonify({
        'status': 'ok',
        'obstacle_detected': robot.is_obstacle_detected(),
        'obstacle_distance': robot.get_obstacle_distance(),
        'speed': current_speed,
        'turn': current_turn
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def cleanup():
    """Cleanup resources"""
    global control_active
    control_active = False

if __name__ == '__main__':
    import threading
    
    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    try:
        # Start the web server
        print(f"Starting web server at http://localhost:5000")
        print("Press Ctrl+C to stop")
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cleanup()
