"""
test_all_components.py - Integration test for all Pathfinder Kit components
"""

import time
import cv2
import numpy as np
from pathlib import Path

# Add parent directory to path to allow imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ComponentClass.IntegratedClass import PathfinderKit, PathfinderConfig

def test_motors(kit):
    """Test motor functionality"""
    print("\n=== Testing Motors ===")
    
    # Test forward movement
    print("Moving forward...")
    kit.move_forward(50)
    time.sleep(2)
    
    # Test turning
    print("Turning right...")
    kit.turn_right(40)
    time.sleep(1)
    
    print("Turning left...")
    kit.turn_left(40)
    time.sleep(1)
    
    # Test backward movement
    print("Moving backward...")
    kit.move_backward(40)
    time.sleep(2)
    
    # Stop
    print("Stopping...")
    kit.stop()
    
    print("Motor test complete!")
    time.sleep(1)

def test_ultrasonic(kit):
    """Test ultrasonic sensor"""
    print("\n=== Testing Ultrasonic Sensor ===")
    
    print("Measuring distance (press Ctrl+C to stop):")
    try:
        for i in range(10):
            distance = kit.get_obstacle_distance()
            if distance < float('inf'):
                print(f"Distance: {distance:.1f} cm")
            else:
                print("No reading")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nUltrasonic test interrupted")
    
    print("Ultrasonic test complete!")

def test_camera(kit):
    """Test camera functionality"""
    print("\n=== Testing Camera ===")
    
    # Capture and display an image
    print("Capturing image...")
    image_data = kit.capture_image("test_image.jpg")
    
    if image_data is not None:
        print(f"Image captured: {image_data['image'].shape}")
        
        # Display the image
        cv2.imshow("Captured Image", cv2.cvtColor(image_data['image'], cv2.COLOR_RGB2BGR))
        print("Press any key to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Failed to capture image")
    
    print("Camera test complete!")

def test_obstacle_avoidance(kit):
    """Test basic obstacle avoidance"""
    print("\n=== Testing Obstacle Avoidance ===")
    
    print("Starting obstacle avoidance test (press Ctrl+C to stop):")
    print("The robot will move forward and stop/turn when an obstacle is detected")
    
    try:
        run_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < run_time:
            if kit.is_obstacle_detected():
                print(f"Obstacle detected at {kit.get_obstacle_distance():.1f}cm - Turning right")
                kit.turn_right(50)
                time.sleep(1)
            else:
                kit.move_forward(40)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nObstacle avoidance test interrupted")
    
    # Stop the robot
    kit.stop()
    print("Obstacle avoidance test complete!")

def main():
    """Main test function"""
    print("Pathfinder Kit Integration Test")
    print("==============================")
    
    # Load or create default config
    config = PathfinderConfig()
    
    # Use context manager to ensure proper cleanup
    with PathfinderKit(config=config) as kit:
        # Run tests
        test_motors(kit)
        test_ultrasonic(kit)
        test_camera(kit)
        
        # Ask before running obstacle avoidance test
        if input("\nRun obstacle avoidance test? (y/n): ").lower() == 'y':
            test_obstacle_avoidance(kit)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()
