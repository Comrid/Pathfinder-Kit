"""
line_tracer.py - Line following using PID control
"""

import time
import numpy as np
from typing import Tuple, Optional, List
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from ComponentClass.IntegratedClass import PathfinderKit, PathfinderConfig

class PIDController:
    """
    Simple PID controller implementation.
    """
    
    def __init__(self, kp: float, ki: float, kd: float, output_limits: Tuple[float, float] = (-100, 100)):
        """
        Initialize PID controller.
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            output_limits: Tuple of (min, max) output values
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limits = output_limits
        
        # State variables
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = time.time()
    
    def compute(self, error: float) -> float:
        """
        Compute the control output.
        
        Args:
            error: Current error (setpoint - process_variable)
            
        Returns:
            Control output
        """
        current_time = time.time()
        dt = current_time - self.prev_time
        
        # Prevent division by zero
        if dt <= 0:
            dt = 1e-3
            
        # Calculate terms
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        
        # Compute output
        output = (self.kp * error + 
                self.ki * self.integral + 
                self.kd * derivative)
        
        # Apply output limits
        output = max(self.output_limits[0], min(self.output_limits[1], output))
        
        # Update state
        self.prev_error = error
        self.prev_time = current_time
        
        return output
    
    def reset(self) -> None:
        """Reset the controller state"""
        self.prev_error = 0.0
        self.integral = 0.0
        self.prev_time = time.time()


class LineTracer:
    """
    Implements line following using PID control.
    """
    
    def __init__(self, kit: PathfinderKit, config: Optional[dict] = None):
        """
        Initialize the line tracer.
        
        Args:
            kit: Instance of PathfinderKit with initialized components
            config: Configuration dictionary (optional)
        """
        self.kit = kit
        self.config = self._load_config(config)
        self.pid = PIDController(
            kp=self.config['pid_kp'],
            ki=self.config['pid_ki'],
            kd=self.config['pid_kd'],
            output_limits=(-self.config['max_turn_speed'], self.config['max_turn_speed'])
        )
        self.running = False
    
    def _load_config(self, config: Optional[dict]) -> dict:
        """Load and validate configuration"""
        default_config = {
            'base_speed': 40,            # Base speed (0-100)
            'max_turn_speed': 70,        # Maximum turning speed
            'pid_kp': 0.8,               # Proportional gain
            'pid_ki': 0.01,              # Integral gain
            'pid_kd': 0.05,              # Derivative gain
            'line_threshold': 30,         # Threshold to detect line (0-100)
            'sensor_weights': [-1.0, -0.5, 0, 0.5, 1.0],  # Weight for each sensor
            'update_interval': 0.02,      # Control loop interval (seconds)
        }
        
        if config:
            default_config.update(config)
            
        return default_config
    
    def start(self) -> bool:
        """Start the line following behavior"""
        if not self.kit.line_sensors:
            print("Error: Line sensors not initialized")
            return False
            
        self.running = True
        self.pid.reset()
        print("Line following started")
        return True
    
    def stop(self) -> None:
        """Stop the line following behavior"""
        self.running = False
        self.kit.stop()
        print("Line following stopped")
    
    def read_line_sensors(self) -> List[float]:
        """
        Read line sensor values.
        
        Returns:
            List of sensor values (0-100, where 0 is white and 100 is black)
        """
        # In a real implementation, this would read from the actual sensors
        # For now, we'll simulate sensor readings
        return [0, 25, 50, 75, 100]  # Example values
    
    def calculate_error(self, sensor_values: List[float]) -> float:
        """
        Calculate the line position error.
        
        Args:
            sensor_values: List of sensor readings
            
        Returns:
            Normalized error (-1.0 to 1.0)
        """
        if len(sensor_values) != len(self.config['sensor_weights']):
            raise ValueError("Number of sensor values must match number of weights")
        
        # Normalize sensor values to 0-1 range
        normalized = [v / 100.0 for v in sensor_values]
        
        # Calculate weighted sum
        weighted_sum = sum(w * v for w, v in zip(self.config['sensor_weights'], normalized))
        
        # Normalize to -1.0 to 1.0 range
        max_sum = sum(abs(w) for w in self.config['sensor_weights'])
        if max_sum == 0:
            return 0.0
            
        return weighted_sum / max_sum
    
    def follow_line(self) -> None:
        """Main line following loop"""
        if not self.start():
            return
            
        try:
            last_time = time.time()
            
            while self.running:
                current_time = time.time()
                dt = current_time - last_time
                
                if dt < self.config['update_interval']:
                    time.sleep(self.config['update_interval'] - dt)
                    continue
                
                # Read sensors
                sensor_values = self.read_line_sensors()
                
                # Calculate error
                error = self.calculate_error(sensor_values)
                
                # Compute PID output
                turn = self.pid.compute(error)
                
                # Calculate motor speeds
                left_speed = self.config['base_speed'] - turn
                right_speed = self.config['base_speed'] + turn
                
                # Apply motor speeds
                self.kit.motors.set_speeds(left_speed, right_speed)
                
                # Print debug info
                print(f"Error: {error:.2f}, Turn: {turn:.1f}, L: {left_speed:.0f}, R: {right_speed:.0f}")
                
                last_time = current_time
                
        except KeyboardInterrupt:
            print("Line following interrupted")
        finally:
            self.stop()


def main():
    """Test the line following"""
    try:
        # Initialize the kit
        config = PathfinderConfig()
        with PathfinderKit(config=config) as kit:
            if not kit.setup():
                print("Failed to initialize kit")
                return
                
            # Create and start line following
            tracer = LineTracer(kit)
            tracer.follow_line()
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Cleanup complete")


if __name__ == "__main__":
    main()
