"""
Camera.py - Raspberry Pi Camera Module Controller
"""

import time
import io
import numpy as np
from typing import Optional, Tuple, Union
from dataclasses import dataclass
import cv2
from picamera2 import Picamera2, Preview
from PIL import Image, ImageDraw, ImageFont

@dataclass
class CameraConfig:
    """Camera configuration parameters"""
    resolution: Tuple[int, int] = (640, 480)
    framerate: int = 30
    rotation: int = 0
    hflip: bool = False
    vflip: bool = False
    format: str = "RGB888"
    buffer_count: int = 2

class Camera:
    """
    Raspberry Pi Camera Module Controller
    
    This class provides a high-level interface to the Raspberry Pi Camera Module
    using the Picamera2 library. It supports capturing still images and video,
    as well as basic image processing and computer vision operations.
    
    Attributes:
        config (CameraConfig): Camera configuration
        camera (Picamera2): The camera instance
        is_preview (bool): Whether the camera preview is active
    """
    
    def __init__(self, config: Optional[CameraConfig] = None):
        """
        Initialize the camera with the given configuration
        
        Args:
            config (Optional[CameraConfig]): Camera configuration. If None, uses default values.
        """
        self.config = config or CameraConfig()
        self.camera = None
        self.is_preview = False
        self._setup_camera()
    
    def _setup_camera(self) -> None:
        """Configure and initialize the camera"""
        try:
            # Create camera instance
            self.camera = Picamera2()
            
            # Configure camera
            config = self.camera.create_preview_configuration(
                main={
                    "size": self.config.resolution,
                    "format": self.config.format
                },
                buffer_count=self.config.buffer_count
            )
            
            self.camera.configure(config)
            
            # Apply camera settings
            self.camera.rotation = self.config.rotation
            self.camera.hflip = self.config.hflip
            self.camera.vflip = self.config.vflip
            
            print(f"Camera initialized: {self.config.resolution[0]}x{self.config.resolution[1]} @ {self.config.framerate}fps")
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None
    
    def start_preview(self, window: Tuple[int, int, int, int] = None) -> None:
        """
        Start the camera preview
        
        Args:
            window (Tuple[int, int, int, int]): Optional window position and size (x, y, width, height)
        """
        if self.camera is None:
            print("Camera not initialized")
            return
            
        try:
            if window:
                self.camera.start_preview(Preview.QTGL, x=window[0], y=window[1], width=window[2], height=window[3])
            else:
                self.camera.start_preview(Preview.QTGL)
            self.is_preview = True
            print("Camera preview started")
        except Exception as e:
            print(f"Error starting preview: {e}")
    
    def stop_preview(self) -> None:
        """Stop the camera preview"""
        if self.camera and self.is_preview:
            try:
                self.camera.stop_preview()
                self.is_preview = False
                print("Camera preview stopped")
            except Exception as e:
                print(f"Error stopping preview: {e}")
    
    def capture_image(self, filename: str = None, format: str = 'jpeg', 
                     quality: int = 85, annotate_text: str = None) -> Optional[np.ndarray]:
        """
        Capture a still image
        
        Args:
            filename (str): Optional filename to save the image
            format (str): Image format ('jpeg' or 'png')
            quality (int): Image quality (1-100)
            annotate_text (str): Optional text to annotate on the image
            
        Returns:
            Optional[np.ndarray]: Captured image as numpy array, or None if failed
        """
        if self.camera is None:
            print("Camera not initialized")
            return None
            
        try:
            # Start camera if not already running
            if not self.camera.started:
                self.camera.start()
                time.sleep(2)  # Allow camera to adjust to lighting
            
            # Capture to numpy array
            image = self.camera.capture_array()
            
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Add annotation if requested
            if annotate_text:
                pil_image = Image.fromarray(image)
                draw = ImageDraw.Draw(pil_image)
                
                # Use default font
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 20)
                except IOError:
                    font = ImageFont.load_default()
                
                # Add text with black border
                position = (10, 10)
                border_color = (0, 0, 0)  # Black
                text_color = (255, 255, 255)  # White
                
                # Draw border
                for x_offset in [-1, 0, 1]:
                    for y_offset in [-1, 0, 1]:
                        draw.text((position[0] + x_offset, position[1] + y_offset), 
                                 annotate_text, font=font, fill=border_color)
                
                # Draw main text
                draw.text(position, annotate_text, font=font, fill=text_color)
                
                # Convert back to numpy array
                image = np.array(pil_image)
            
            # Save to file if filename provided
            if filename:
                save_image = image.copy()
                if len(save_image.shape) == 3 and save_image.shape[2] == 3:
                    save_image = cv2.cvtColor(save_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(filename, save_image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            
            return image
            
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
    
    def capture_video(self, filename: str, duration: float = 10.0, 
                      fps: float = 30.0, resolution: Tuple[int, int] = None) -> bool:
        """
        Capture a video
        
        Args:
            filename (str): Output filename (should end with .mp4)
            duration (float): Recording duration in seconds
            fps (float): Frames per second
            resolution (Tuple[int, int]): Video resolution (width, height)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.camera is None:
            print("Camera not initialized")
            return False
            
        try:
            # Configure video recording
            config = self.camera.create_video_configuration(
                main={"size": resolution or self.config.resolution},
                encode="main"
            )
            self.camera.configure(config)
            
            # Start recording
            self.camera.start_recording(filename, format='mp4', fps=fps)
            print(f"Recording video to {filename} for {duration} seconds...")
            
            # Record for specified duration
            time.sleep(duration)
            
            # Stop recording
            self.camera.stop_recording()
            print("Recording finished")
            return True
            
        except Exception as e:
            print(f"Error capturing video: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera
        
        Returns:
            Optional[np.ndarray]: Captured frame as numpy array, or None if failed
        """
        if self.camera is None:
            print("Camera not initialized")
            return None
            
        try:
            if not self.camera.started:
                self.camera.start()
                time.sleep(1)
                
            frame = self.camera.capture_array()
            
            # Convert BGR to RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
            return frame
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None
    
    def release(self) -> None:
        """Release camera resources"""
        if self.camera is not None:
            try:
                if self.is_preview:
                    self.stop_preview()
                if self.camera.started:
                    self.camera.stop()
                self.camera.close()
                print("Camera released")
            except Exception as e:
                print(f"Error releasing camera: {e}")
            finally:
                self.camera = None


# Example usage
if __name__ == "__main__":
    import cv2
    
    # Create camera instance with default settings
    camera = Camera()
    
    try:
        # Start preview
        camera.start_preview()
        
        # Wait a moment for camera to adjust
        time.sleep(2)
        
        # Capture and save an image
        print("Capturing image...")
        image = camera.capture_image("test_image.jpg", annotate_text="Test Image")
        
        if image is not None:
            print(f"Image captured: {image.shape}")
            
            # Display the image
            cv2.imshow("Captured Image", cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            cv2.waitKey(3000)  # Display for 3 seconds
            cv2.destroyAllWindows()
        
        # Example of capturing a short video
        print("Capturing 5-second video...")
        camera.capture_video("test_video.mp4", duration=5.0, fps=30)
        
        print("Test complete!")
        
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        camera.release()
