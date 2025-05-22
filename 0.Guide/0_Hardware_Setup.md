# Pathfinder Kit Hardware Setup Guide

## Components
1. Raspberry Pi 4B
2. Motor Driver (L298N)
3. DC Motors (x2)
4. Ultrasonic Sensor (HC-SR04)
5. Raspberry Pi Camera Module
6. Power Supply
7. Jumper Wires

## Connections

### Motor Driver (L298N) to Raspberry Pi
- IN1 → GPIO 23
- IN2 → GPIO 24
- IN3 → GPIO 27
- IN4 → GPIO 22
- ENA → GPIO 13 (PWM)
- ENB → GPIO 12 (PWM)
- GND → GND
- 5V → 5V

### Ultrasonic Sensor (HC-SR04)
- VCC → 5V
- TRIG → GPIO 5
- ECHO → GPIO 6
- GND → GND

### Camera Module
- Connect to the CSI port of Raspberry Pi

## Power Requirements
- Raspberry Pi: 5V/3A power supply
- Motor Driver: 7-12V power supply