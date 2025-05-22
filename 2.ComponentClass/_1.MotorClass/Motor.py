"""
Motor.py - Controls the L298N motor driver for the Pathfinder Kit
"""

import RPi.GPIO as GPIO
import time
from dataclasses import dataclass
from typing import Tuple

@dataclass
class MotorPins:
    """Dataclass to store motor pin configuration"""
    in1: int  # Motor control pin 1
    in2: int  # Motor control pin 2
    en: int   # PWM enable pin

class Motor:
    """
    Controls a single DC motor using L298N driver
    
    Attributes:
        pins (MotorPins): Motor pin configuration
        pwm (PWM): PWM controller for speed control
        speed (int): Current motor speed (0-100)
    """
    
    def __init__(self, in1: int, in2: int, en: int):
        """
        Initialize motor with specified pins
        
        Args:
            in1 (int): GPIO pin for motor control 1
            in2 (int): GPIO pin for motor control 2
            en (int): GPIO pin for PWM speed control
        """
        self.pins = MotorPins(in1=in1, in2=in2, en=en)
        self.pwm = None
        self.speed = 0
        self.setup()
    
    def setup(self) -> None:
        """Initialize GPIO pins and PWM"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pins.in1, GPIO.OUT)
        GPIO.setup(self.pins.in2, GPIO.OUT)
        GPIO.setup(self.pins.en, GPIO.OUT)
        
        # Initialize PWM (1000 Hz)
        self.pwm = GPIO.PWM(self.pins.en, 1000)
        self.pwm.start(0)  # Start with 0% duty cycle
    
    def forward(self, speed: int = 50) -> None:
        """
        Rotate motor forward
        
        Args:
            speed (int): Speed percentage (0-100)
        """
        self._set_speed(speed)
        GPIO.output(self.pins.in1, GPIO.HIGH)
        GPIO.output(self.pins.in2, GPIO.LOW)
    
    def backward(self, speed: int = 50) -> None:
        """
        Rotate motor backward
        
        Args:
            speed (int): Speed percentage (0-100)
        """
        self._set_speed(speed)
        GPIO.output(self.pins.in1, GPIO.LOW)
        GPIO.output(self.pins.in2, GPIO.HIGH)
    
    def stop(self) -> None:
        """Stop the motor"""
        self._set_speed(0)
        GPIO.output(self.pins.in1, GPIO.LOW)
        GPIO.output(self.pins.in2, GPIO.LOW)
    
    def _set_speed(self, speed: int) -> None:
        """
        Set motor speed
        
        Args:
            speed (int): Speed percentage (0-100)
        """
        self.speed = max(0, min(100, speed))  # Clamp between 0-100
        self.pwm.ChangeDutyCycle(self.speed)
    
    def cleanup(self) -> None:
        """Cleanup GPIO resources"""
        self.stop()
        if self.pwm is not None:
            self.pwm.stop()
        # Don't call GPIO.cleanup() here as other motors might be using it


class MotorController:
    """
    Controls two motors for differential drive
    
    Attributes:
        left_motor (Motor): Left motor instance
        right_motor (Motor): Right motor instance
    """
    
    def __init__(self, left_pins: Tuple[int, int, int], right_pins: Tuple[int, int, int]):
        """
        Initialize motor controller with pin configurations
        
        Args:
            left_pins: Tuple of (in1, in2, en) pins for left motor
            right_pins: Tuple of (in1, in2, en) pins for right motor
        """
        self.left_motor = Motor(*left_pins)
        self.right_motor = Motor(*right_pins)
    
    def move_forward(self, speed: int = 50) -> None:
        """Move both motors forward"""
        self.left_motor.forward(speed)
        self.right_motor.forward(speed)
    
    def move_backward(self, speed: int = 50) -> None:
        """Move both motors backward"""
        self.left_motor.backward(speed)
        self.right_motor.backward(speed)
    
    def turn_left(self, speed: int = 50) -> None:
        """Turn left (right motor forward, left motor backward)"""
        self.left_motor.backward(speed)
        self.right_motor.forward(speed)
    
    def turn_right(self, speed: int = 50) -> None:
        """Turn right (left motor forward, right motor backward)"""
        self.left_motor.forward(speed)
        self.right_motor.backward(speed)
    
    def stop(self) -> None:
        """Stop both motors"""
        self.left_motor.stop()
        self.right_motor.stop()
    
    def set_speeds(self, left_speed: int, right_speed: int) -> None:
        """
        Set speeds for each motor independently
        
        Args:
            left_speed: Speed for left motor (-100 to 100)
            right_speed: Speed for right motor (-100 to 100)
        """
        if left_speed >= 0:
            self.left_motor.forward(abs(left_speed))
        else:
            self.left_motor.backward(abs(left_speed))
            
        if right_speed >= 0:
            self.right_motor.forward(abs(right_speed))
        else:
            self.right_motor.backward(abs(right_speed))
    
    def cleanup(self) -> None:
        """Cleanup all motor resources"""
        self.left_motor.cleanup()
        self.right_motor.cleanup()
        GPIO.cleanup()  # Only call this when we're completely done with GPIO


# Example usage
if __name__ == "__main__":
    try:
        # Example pin configuration - adjust according to your wiring
        LEFT_MOTOR_PINS = (17, 27, 18)  # in1, in2, en
        RIGHT_MOTOR_PINS = (23, 24, 25)  # in1, in2, en
        
        # Create motor controller
        motors = MotorController(LEFT_MOTOR_PINS, RIGHT_MOTOR_PINS)
        
        # Test sequence
        print("Moving forward...")
        motors.move_forward(50)
        time.sleep(2)
        
        print("Turning right...")
        motors.turn_right(50)
        time.sleep(1)
        
        print("Moving backward...")
        motors.move_backward(50)
        time.sleep(2)
        
        print("Stopping...")
        motors.stop()
        
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        if 'motors' in locals():
            motors.cleanup()
        print("Cleanup complete")
