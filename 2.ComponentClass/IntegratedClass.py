"""
IntegratedClass.py - Main class for integrating all components of the Pathfinder Kit
"""

import time
import threading
import json
import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict

# Import component classes
from _1.MotorClass.Motor import MotorController
from _2.SonicClass.UltrasonicSensor import UltrasonicSensor
from _3.CameraClass.Camera import Camera, CameraConfig

@dataclass
class PathfinderConfig:
    """Configuration for the Pathfinder Kit"""
    # Motor configuration (BCM pin numbers)
    motor_left_pins: Tuple[int, int, int] = (17, 27, 18)  # in1, in2, en
    motor_right_pins: Tuple[int, int, int] = (23, 24, 25)  # in1, in2, en
    
    # Ultrasonic sensor configuration
    ultrasonic_trigger_pin: int = 5
    ultrasonic_echo_pin: int = 6
    
    # Camera configuration
    camera_resolution: Tuple[int, int] = (640, 480)
    camera_framerate: int = 30
    camera_rotation: int = 0
    camera_hflip: bool = False
    camera_vflip: bool = False
    
    # Behavior parameters
    obstacle_threshold_cm: float = 30.0  # Distance threshold for obstacle detection
    default_speed: int = 50  # Default motor speed (0-100)
    turn_speed: int = 40     # Speed during turns


class PathfinderKit:
    """
    Main class for the Pathfinder Kit that integrates all components
    
    This class provides a high-level interface to control the robot's movements,
    sense the environment, and perform autonomous behaviors.
    """
    
    def __init__(self, config: Optional[PathfinderConfig] = None):
        """
        Initialize the Pathfinder Kit with the given configuration
        
        Args:
            config (Optional[PathfinderConfig]): Configuration object. If None, uses defaults.
        """
        self.config = config or PathfinderConfig()
        self.motors = None
        self.ultrasonic = None
        self.camera = None
        self.running = False
        self._obstacle_detected = False
        self._last_obstacle_distance = float('inf')
        self._thread = None
        
    def setup(self) -> bool:
        """
        Initialize all components
        
        Returns:
            bool: True if all components initialized successfully, False otherwise
        """
        success = True
        
        try:
            print("Initializing motors...")
            self.motors = MotorController(
                left_pins=self.config.motor_left_pins,
                right_pins=self.config.motor_right_pins
            )
            
            print("Initializing ultrasonic sensor...")
            self.ultrasonic = UltrasonicSensor(
                trigger_pin=self.config.ultrasonic_trigger_pin,
                echo_pin=self.config.ultrasonic_echo_pin
            )
            
            print("Initializing camera...")
            camera_config = CameraConfig(
                resolution=self.config.camera_resolution,
                framerate=self.config.camera_framerate,
                rotation=self.config.camera_rotation,
                hflip=self.config.camera_hflip,
                vflip=self.config.camera_vflip
            )
            self.camera = Camera(config=camera_config)
            
            # Start obstacle detection in a separate thread
            self.running = True
            self._thread = threading.Thread(target=self._obstacle_detection_loop)
            self._thread.daemon = True
            self._thread.start()
            
            print("Pathfinder Kit initialization complete!")
            return True
            
        except Exception as e:
            print(f"Error during setup: {e}")
            self.cleanup()
            return False
    
    def _obstacle_detection_loop(self):
        """Background thread for obstacle detection"""
        while self.running:
            try:
                distance = self.ultrasonic.get_distance()
                if distance is not None:
                    self._last_obstacle_distance = distance
                    self._obstacle_detected = (distance <= self.config.obstacle_threshold_cm)
            except Exception as e:
                print(f"Error in obstacle detection: {e}")
            
            # Adjust sleep time based on needs (e.g., 100ms)
            time.sleep(0.1)
    
    def is_obstacle_detected(self) -> bool:
        """
        Check if an obstacle is detected within the configured threshold
        
        Returns:
            bool: True if obstacle detected, False otherwise
        """
        return self._obstacle_detected
    
    def get_obstacle_distance(self) -> float:
        """
        Get the last measured obstacle distance
        
        Returns:
            float: Distance in cm, or infinity if no measurement available
        """
        return self._last_obstacle_distance
    
    def move_forward(self, speed: Optional[int] = None) -> None:
        """Move forward at the specified speed"""
        speed = speed or self.config.default_speed
        if self.motors:
            self.motors.move_forward(speed)
    
    def move_backward(self, speed: Optional[int] = None) -> None:
        """Move backward at the specified speed"""
        speed = speed or self.config.default_speed
        if self.motors:
            self.motors.move_backward(speed)
    
    def turn_left(self, speed: Optional[int] = None) -> None:
        """Turn left at the specified speed"""
        speed = speed or self.config.turn_speed
        if self.motors:
            self.motors.turn_left(speed)
    
    def turn_right(self, speed: Optional[int] = None) -> None:
        """Turn right at the specified speed"""
        speed = speed or self.config.turn_speed
        if self.motors:
            self.motors.turn_right(speed)
    
    def stop(self) -> None:
        """Stop all motors"""
        if self.motors:
            self.motors.stop()
    
    def capture_image(self, filename: str = None, annotate: bool = True) -> Optional[dict]:
        """
        Capture an image from the camera
        
        Args:
            filename (str): Optional filename to save the image
            annotate (bool): Whether to add obstacle distance annotation
            
        Returns:
            Optional[dict]: Dictionary containing image data and metadata
        """
        if not self.camera:
            return None
        
        annotation = None
        if annotate and self._last_obstacle_distance < float('inf'):
            annotation = f"Obstacle: {self._last_obstacle_distance:.1f}cm"
        
        image = self.camera.capture_image(
            filename=filename,
            annotate_text=annotation
        )
        
        if image is not None:
            return {
                'image': image,
                'timestamp': time.time(),
                'obstacle_detected': self._obstacle_detected,
                'obstacle_distance': self._last_obstacle_distance
            }
        return None
    
    def cleanup(self) -> None:
        """Cleanup all resources"""
        print("Cleaning up Pathfinder Kit...")
        self.running = False
        
        # Stop motors
        if self.motors:
            self.motors.stop()
            self.motors.cleanup()
        
        # Stop camera
        if self.camera:
            self.camera.release()
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        
        print("Cleanup complete")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


def save_config(config: PathfinderConfig, filename: str = "pathfinder_config.json") -> bool:
    """
    Save configuration to a JSON file
    
    Args:
        config (PathfinderConfig): Configuration to save
        filename (str): Output filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, 'w') as f:
            json.dump(asdict(config), f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def load_config(filename: str = "pathfinder_config.json") -> Optional[PathfinderConfig]:
    """
    Load configuration from a JSON file
    
    Args:
        filename (str): Input filename
        
    Returns:
        Optional[PathfinderConfig]: Loaded configuration, or None if failed
    """
    if not os.path.exists(filename):
        return None
        
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return PathfinderConfig(**data)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


# Example usage
if __name__ == "__main__":
    print("Pathfinder Kit Test")
    print("==================")
    
    # Create and configure the kit
    config = PathfinderConfig(
        motor_left_pins=(17, 27, 18),
        motor_right_pins=(23, 24, 25),
        ultrasonic_trigger_pin=5,
        ultrasonic_echo_pin=6,
        camera_resolution=(640, 480)
    )
    
    # Save config for future use
    save_config(config, "my_config.json")
    
    # Use context manager for automatic cleanup
    with PathfinderKit(config=config) as kit:
        print("Testing motors...")
        
        # Test forward movement
        print("Moving forward for 2 seconds...")
        kit.move_forward(50)
        time.sleep(2)
        
        # Test turning
        print("Turning right for 1 second...")
        kit.turn_right(40)
        time.sleep(1)
        
        # Test obstacle detection
        print("Checking for obstacles...")
        if kit.is_obstacle_detected():
            print(f"Obstacle detected at {kit.get_obstacle_distance():.1f}cm")
        else:
            print("No obstacles detected")
        
        # Test camera
        print("Capturing image...")
        image_data = kit.capture_image("test_capture.jpg")
        if image_data:
            print(f"Image captured: {image_data['image'].shape}")
        
        # Stop all motors
        print("Stopping...")
        kit.stop()
    
    print("Test complete!")