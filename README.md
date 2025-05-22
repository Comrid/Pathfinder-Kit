# Pathfinder Autonomous Kit
패스파인터 AI 파이썬 자율주행 키트용 예제 코드 및 가이드

A comprehensive kit for building and programming an autonomous robot with Python. This project includes hardware integration, sensor processing, and a web-based control interface.

## Features

- **Motor Control**: Precise control of DC motors using L298N driver
- **Ultrasonic Sensing**: Obstacle detection and distance measurement
- **Camera Integration**: Real-time image capture and processing
- **Web Interface**: Browser-based remote control and monitoring
- **Modular Design**: Easy to extend and customize

## Project Structure

```
Pathfinder-Kit/
├── 0.Guide/                     # Setup guides and documentation
├── 1.Hardware/                  # Hardware specifications and schematics
├── 2.ComponentClass/            # Individual component classes
│   ├── _1.MotorClass/           # Motor control implementation
│   ├── _2.SonicClass/           # Ultrasonic sensor implementation
│   ├── _3.CameraClass/          # Camera module implementation
│   └── IntegratedClass.py       # Combined functionality
├── 3.IntegrationTest/           # Test scripts for integrated components
├── 7.WebUploader/               # Web interface and remote control
│   ├── static/                  # Static files (CSS, JS, images)
│   │   └── uploads/            # Directory for uploaded images
│   ├── templates/               # HTML templates
│   │   └── index.html          # Web interface
│   ├── web_controller.py        # Main Flask application
│   ├── test_web_controller.py   # Test script without hardware
│   └── requirements.txt         # Python dependencies
└── README.md                    # This file
```

## Getting Started

### Prerequisites

- Raspberry Pi (3/4 recommended)
- Raspberry Pi OS (32-bit) with desktop
- Python 3.7+
- Required hardware (motors, sensors, camera)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Pathfinder-Kit.git
   cd Pathfinder-Kit
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. For the web interface:
   ```bash
   cd 7.WebUploader
   pip install -r requirements.txt
   ```

## Usage

### Running the Web Interface

1. Navigate to the web interface directory:
   ```bash
   cd 7.WebUploader
   ```

2. Start the web server:
   ```bash
   python web_controller.py
   ```

3. Open a web browser and navigate to:
   ```
   http://<raspberry-pi-ip>:5000
   ```

### Testing Without Hardware

To test the web interface without actual hardware:

```bash
cd 7.WebUploader
python test_web_controller.py
```

## Documentation

- [Hardware Setup Guide](0.Guide/0_Hardware_Setup.md)
- [OS Installation & SSH Setup](0.Guide/1_OS_Install_SSH.md)
- [Component Documentation](2.ComponentClass/README.md)
- [Web Interface Documentation](7.WebUploader/README.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python 3
- Web interface powered by Flask
- Motor control using RPi.GPIO
- Camera handling with picamera2
