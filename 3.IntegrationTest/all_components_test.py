
### 3. IntegratedClass.py
"""
IntegratedClass.py - Main class for integrating all components
"""

from MotorClass.Motor import Motor
from SonicClass.UltrasonicSensor import UltrasonicSensor
from CameraClass.Camera import Camera
import time

class PathfinderKit:
    def __init__(self):
        """Initialize all components"""
        self.motors = Motor()
        self.ultrasonic = UltrasonicSensor()
        self.camera = Camera()
        self.running = False
        
    def setup(self):
        """Setup all components"""
        try:
            self.motors.setup()
            self.ultrasonic.setup()
            self.camera.setup()
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False
            
    def cleanup(self):
        """Cleanup all components"""
        self.motors.cleanup()
        self.ultrasonic.cleanup()
        self.camera.cleanup()
        
    def obstacle_avoidance(self):
        """Simple obstacle avoidance behavior"""
        self.running = True
        try:
            while self.running:
                distance = self.ultrasonic.get_distance()
                if distance < 20:  # 20cm threshold
                    self.motors.stop()
                    time.sleep(0.5)
                    self.motors.turn_right(50)
                    time.sleep(0.5)
                else:
                    self.motors.forward(70)
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.cleanup()
            
    def stop(self):
        """Stop all operations"""
        self.running = False
        self.motors.stop()

if __name__ == "__main__":
    kit = PathfinderKit()
    if kit.setup():
        try:
            kit.obstacle_avoidance()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            kit.cleanup()