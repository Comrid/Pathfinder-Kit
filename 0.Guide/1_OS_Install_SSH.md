# OS Installation and SSH Setup

## 1. Download and Install Raspberry Pi OS
1. Download Raspberry Pi Imager from [raspberrypi.com/software/](https://www.raspberrypi.com/software/)
2. Insert SD card into your computer (minimum 8GB recommended)
3. Open Raspberry Pi Imager
4. Choose OS: Raspberry Pi OS Lite (32-bit)
5. Choose Storage: Select your SD card
6. Click the gear icon (⚙️) to:
   - Set hostname: `pathfinder`
   - Enable SSH with password authentication
   - Configure Wi-Fi (SSID and password)
   - Set locale settings (timezone, keyboard layout)
7. Write the image to the SD card (this will erase all data on the card)

## 2. First Boot and Configuration
1. Insert SD card into Raspberry Pi
2. Connect to power
3. Find the IP address of your Raspberry Pi using one of these methods:
   - Check your router's connected devices list
   - Use an IP scanner like Advanced IP Scanner
   - From another computer on the same network:
     ```bash
     ping raspberrypi.local
     # or
     ping pathfinder.local
     ```

4. SSH into the Pi:
   ```bash
   ssh pi@pathfinder.local
   # or
   ssh pi@<ip-address>
   ```
   Default password: `raspberry`

## 3. Initial System Setup

### Change default password
```bash
passwd
```

### Update system packages
```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

### Install essential packages
```bash
sudo apt install -y \
    python3-pip \
    python3-picamera2 \
    python3-rpi.gpio \
    git \
    vim \
    htop
```

### Enable required interfaces
```bash
sudo raspi-config
```
Navigate to:
1. Interface Options → Camera → Enable
2. Interface Options → I2C → Enable
3. Interface Options → SPI → Enable
4. Advanced Options → Expand Filesystem
5. System Options → Boot / Auto Login → Console Autologin

### Reboot to apply changes
```bash
sudo reboot
```

## 4. Clone the Pathfinder-Kit Repository
```bash
cd ~
git clone https://github.com/yourusername/Pathfinder-Kit.git
cd Pathfinder-Kit
```

## 5. Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

## 6. Test Basic Functionality

### Test GPIO access
```bash
groups  # Check if 'gpio' group is listed
```

### Test camera
```bash
libcamera-hello --timeout 2000
```

Your system is now ready for development with the Pathfinder Kit!
