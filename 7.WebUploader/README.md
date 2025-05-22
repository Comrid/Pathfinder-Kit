# Pathfinder Kit Web Controller

A web-based controller for the Pathfinder Kit, allowing remote control of the robot through a browser interface.

## Features

- **Real-time Control**: Control the robot's movement using on-screen buttons or a virtual joystick
- **Live Camera Feed**: View the robot's camera feed in real-time
- **Obstacle Detection**: Monitor the ultrasonic sensor readings
- **Image Capture**: Take and save images from the robot's camera
- **Responsive Design**: Works on desktop and mobile devices
- **Emergency Stop**: Immediately stop all robot movement

## Requirements

- Python 3.6+
- Flask
- RPi.GPIO (on Raspberry Pi)
- picamera2 (on Raspberry Pi)
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pathfinder-kit.git
   cd pathfinder-kit/7.WebUploader
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create the necessary directories:
   ```bash
   mkdir -p static/uploads
   ```

## Usage

1. Start the web server:
   ```bash
   python web_controller.py
   ```

2. Open a web browser and navigate to:
   ```
   http://<raspberry-pi-ip>:5000
   ```
   Replace `<raspberry-pi-ip>` with the IP address of your Raspberry Pi.

3. Use the web interface to control the robot:
   - **Joystick**: Click and drag to control direction and speed
   - **Control Buttons**: Use the arrow buttons for directional control
   - **Emergency Stop**: Immediately stop all movement
   - **Camera Controls**: Capture and save images

## Controls

- **Forward/Backward Buttons**: Move the robot forward or backward
- **Left/Right Buttons**: Turn the robot left or right
- **Joystick**: Drag in any direction to control both speed and direction
- **Max Speed Slider**: Adjust the maximum speed of the robot
- **Capture Button**: Take a picture with the robot's camera
- **Refresh Rate Slider**: Adjust how often the status updates

## File Structure

```
7.WebUploader/
├── static/                 # Static files (CSS, JS, images)
│   └── uploads/            # Directory for uploaded images
├── templates/              # HTML templates
│   └── index.html          # Main web interface
├── web_controller.py       # Main Flask application
└── README.md               # This file
```

## Troubleshooting

- **Connection Issues**: Ensure the Raspberry Pi is connected to the network and the web server is running
- **Camera Not Working**: Verify the camera is properly connected and enabled in the Raspberry Pi configuration
- **GPIO Errors**: Make sure the script has the necessary permissions to access the GPIO pins

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Uses [Bootstrap](https://getbootstrap.com/) for styling
- Icons by [Bootstrap Icons](https://icons.getbootstrap.com/)
