"""
UltrasonicSensor.py - HC-SR04 Ultrasonic Distance Sensor
"""

import RPi.GPIO as GPIO
import time
from dataclasses import dataclass
from typing import Optional, Tuple

class UltrasonicSensor:
    """
    HC-SR04 Ultrasonic Distance Sensor Controller
    
    This class provides methods to measure distance using the HC-SR04 ultrasonic sensor.
    It includes error handling and temperature compensation for more accurate measurements.
    
    Attributes:
        trigger_pin (int): GPIO pin connected to the TRIG pin
        echo_pin (int): GPIO pin connected to the ECHO pin
        temperature (float): Ambient temperature in Celsius (for speed of sound compensation)
        timeout (float): Measurement timeout in seconds
    """
    
    # Speed of sound in cm/s at 20°C
    SPEED_OF_SOUND_20C = 34300
    
    def __init__(self, trigger_pin: int, echo_pin: int, temperature: float = 20.0, timeout: float = 0.05):
        """
        Initialize the ultrasonic sensor
        
        Args:
            trigger_pin (int): GPIO pin connected to the TRIG pin
            echo_pin (int): GPIO pin connected to the ECHO pin
            temperature (float): Ambient temperature in Celsius (default: 20.0)
            timeout (float): Measurement timeout in seconds (default: 0.05)
        """
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.temperature = temperature
        self.timeout = timeout
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Initialize trigger pin to low
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.5)  # Allow sensor to settle
    
    def _get_speed_of_sound(self) -> float:
        """
        Calculate the speed of sound based on temperature
        
        Returns:
            float: Speed of sound in cm/s
        """
        # Speed of sound calculation: 331.5 + (0.6 * temperature) m/s
        return (331.5 + (0.6 * self.temperature)) * 100  # Convert to cm/s
    
    def get_distance(self, samples: int = 5) -> Optional[float]:
        """
        Measure distance using the ultrasonic sensor
        
        Args:
            samples (int): Number of samples to average (default: 5)
            
        Returns:
            Optional[float]: Distance in cm, or None if measurement failed
        """
        distances = []
        
        for _ in range(samples):
            # Send 10µs pulse to trigger
            GPIO.output(self.trigger_pin, True)
            time.sleep(0.00001)  # 10µs
            GPIO.output(self.trigger_pin, False)
            
            # Wait for echo to go high
            pulse_start = time.time()
            timeout_start = time.time()
            while GPIO.input(self.echo_pin) == 0:
                if time.time() - timeout_start > self.timeout:
                    print("Timeout waiting for echo start")
                    break
                pulse_start = time.time()
            
            # Wait for echo to go low
            pulse_end = time.time()
            timeout_start = time.time()
            while GPIO.input(self.echo_pin) == 1:
                if time.time() - timeout_start > self.timeout:
                    print("Timeout waiting for echo end")
                    break
                pulse_end = time.time()
            
            # Calculate pulse duration and distance
            pulse_duration = pulse_end - pulse_start
            distance = (pulse_duration * self._get_speed_of_sound()) / 2
            
            # Filter out invalid readings (HC-SR04 range is 2-400cm)
            if 2 <= distance <= 400:
                distances.append(distance)
            
            # Short delay between measurements
            time.sleep(0.01)
        
        # Return average distance if we have valid readings
        if distances:
            return sum(distances) / len(distances)
        return None
    
    def get_distance_smoothed(self, samples: int = 5, window_size: int = 3) -> Optional[float]:
        """
        Get distance with median filtering to reduce noise
        
        Args:
            samples (int): Number of samples to take
            window_size (int): Size of the median filter window (must be odd)
            
        Returns:
            Optional[float]: Filtered distance in cm, or None if measurement failed
        """
        distances = []
        for _ in range(samples):
            dist = self.get_distance(1)
            if dist is not None:
                distances.append(dist)
        
        if not distances:
            return None
            
        # Sort and take median
        distances.sort()
        return distances[len(distances) // 2]
    
    def is_obstacle_detected(self, threshold_cm: float = 30.0) -> bool:
        """
        Check if an obstacle is detected within the threshold distance
        
        Args:
            threshold_cm (float): Distance threshold in cm (default: 30.0)
            
        Returns:
            bool: True if obstacle detected, False otherwise
        """
        distance = self.get_distance()
        if distance is None:
            return False
        return distance <= threshold_cm
    
    def cleanup(self) -> None:
        """Cleanup GPIO resources"""
        # Don't call GPIO.cleanup() here as other components might be using it
        pass


# Example usage
if __name__ == "__main__":
    try:
        # Example pin configuration - adjust according to your wiring
        TRIGGER_PIN = 5
        ECHO_PIN = 6
        
        # Create sensor instance
        sensor = UltrasonicSensor(trigger_pin=TRIGGER_PIN, echo_pin=ECHO_PIN)
        
        print("Measuring distance...")
        print("Press Ctrl+C to stop")
        
        while True:
            distance = sensor.get_distance()
            if distance is not None:
                print(f"Distance: {distance:.2f} cm")
            else:
                print("Measurement failed")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nMeasurement stopped by user")
    finally:
        if 'sensor' in locals():
            sensor.cleanup()
        print("Cleanup complete")
