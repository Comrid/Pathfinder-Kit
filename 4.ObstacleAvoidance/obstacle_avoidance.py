"""
obstacle_avoidance.py - Obstacle avoidance using ultrasonic sensors
"""

import time
import numpy as np
from typing import Tuple, Optional
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from ComponentClass.IntegratedClass import PathfinderKit, PathfinderConfig

class ObstacleAvoider:
    """
    Implements obstacle avoidance behavior for the Pathfinder Kit.
    Uses ultrasonic sensors to detect and avoid obstacles.
    """
    
    def __init__(self, kit: PathfinderKit, config: Optional[dict] = None):
        """
        Initialize the obstacle avoider.
        
        Args:
            kit: Instance of PathfinderKit with initialized components
            config: Configuration dictionary (optional)
        """
        self.kit = kit
        self.config = self._load_config(config)
        self.running = False
        
    def _load_config(self, config: Optional[dict]) -> dict:
        """Load and validate configuration"""
        default_config = {
            'safe_distance': 30.0,  # cm
            'turn_speed': 50,       # 0-100
            'forward_speed': 40,    # 0-100
            'turn_duration': 0.5,   # seconds
            'scan_angle': 90,       # degrees
            'scan_steps': 5,        # number of steps in scan
        }
        
        if config:
            default_config.update(config)
            
        return default_config
    
    def start(self) -> bool:
        """Start the obstacle avoidance behavior"""
        if not self.kit.ultrasonic:
            print("Error: Ultrasonic sensor not initialized")
            return False
            
        self.running = True
        print("Obstacle avoidance started")
        return True
    
    def stop(self) -> None:
        """Stop the obstacle avoidance behavior"""
        self.running = False
        self.kit.stop()
        print("Obstacle avoidance stopped")
    
    def scan_environment(self) -> Tuple[float, float]:
        """
        Scan the environment for obstacles.
        
        Returns:
            Tuple of (min_distance, angle_to_obstacle)
        """
        min_distance = float('inf')
        angle_to_obstacle = 0
        
        step_size = self.config['scan_angle'] / (self.config['scan_steps'] - 1)
        start_angle = -self.config['scan_angle'] / 2
        
        for i in range(self.config['scan_steps']):
            # Calculate current angle
            current_angle = start_angle + i * step_size
            
            # Turn to angle (simplified)
            # In a real implementation, you would use a servo to turn the sensor
            
            # Get distance
            distance = self.kit.get_obstacle_distance()
            
            if distance < min_distance:
                min_distance = distance
                angle_to_obstacle = current_angle
                
        return min_distance, angle_to_obstacle
    
    def avoid_obstacles(self) -> None:
        """Main obstacle avoidance loop"""
        if not self.start():
            return
            
        try:
            while self.running:
                distance, angle = self.scan_environment()
                
                if distance < self.config['safe_distance']:
                    # Obstacle detected, avoid it
                    print(f"Obstacle detected at {distance:.1f}cm, angle: {angle:.1f}°")
                    
                    # Turn away from the obstacle
                    if angle < 0:
                        # Obstacle on the left, turn right
                        self.kit.turn_right(self.config['turn_speed'])
                        print("Turning right")
                    else:
                        # Obstacle on the right, turn left
                        self.kit.turn_left(self.config['turn_speed'])
                        print("Turning left")
                        
                    time.sleep(self.config['turn_duration'])
                else:
                    # No obstacle, move forward
                    self.kit.move_forward(self.config['forward_speed'])
                    
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Obstacle avoidance interrupted")
        finally:
            self.stop()


def main():
    """Test the obstacle avoidance"""
    try:
        # Initialize the kit
        config = PathfinderConfig()
        with PathfinderKit(config=config) as kit:
            if not kit.setup():
                print("Failed to initialize kit")
                return
                
            # Create and start obstacle avoidance
            avoider = ObstacleAvoider(kit)
            avoider.avoid_obstacles()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleanup complete")


if __name__ == "__main__":
    main()
