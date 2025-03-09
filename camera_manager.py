import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
import time

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage)
    error = pyqtSignal(str)

    def __init__(self, camera_id):
        super().__init__()
        self.camera_id = camera_id
        self.running = False
        self.cap = None
        self.retry_count = 0
        self.max_retries = 3

    def run(self):
        self.running = True
        while self.running and self.retry_count < self.max_retries:
            try:
                self.cap = cv2.VideoCapture(self.camera_id)
                if not self.cap.isOpened():
                    raise RuntimeError("Failed to open camera")
                
                while self.running:
                    ret, frame = self.cap.read()
                    if ret:
                        # Convert frame to RGB format
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_frame.shape
                        bytes_per_line = ch * w
                        
                        # Convert to QImage
                        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        self.frame_ready.emit(qt_image)
                    else:
                        raise RuntimeError("Failed to read frame")
                    
                    self.msleep(30)  # ~30 fps
                break  # If we get here, camera is working properly
                
            except Exception as e:
                self.retry_count += 1
                if self.retry_count >= self.max_retries:
                    self.error.emit(f"Camera {self.camera_id} error: {str(e)}")
                else:
                    time.sleep(1)  # Wait before retrying
                    
            finally:
                if self.cap:
                    self.cap.release()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.wait()

class CameraManager:
    def __init__(self):
        self.available_cameras = self._get_available_cameras()
        self.active_cameras = {}

    def _get_available_cameras(self):
        """Find all available cameras."""
        available = []
        for i in range(10):  # Check first 10 indexes
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available.append(i)
                cap.release()
            except:
                continue
        return available

    def start_camera(self, camera_id):
        """Start a camera stream."""
        if camera_id not in self.active_cameras:
            camera_thread = CameraThread(camera_id)
            self.active_cameras[camera_id] = camera_thread
            camera_thread.start()
            return camera_thread
        return self.active_cameras[camera_id]

    def stop_camera(self, camera_id):
        """Stop a camera stream."""
        if camera_id in self.active_cameras:
            self.active_cameras[camera_id].stop()
            del self.active_cameras[camera_id]

    def stop_all_cameras(self):
        """Stop all active camera streams."""
        for camera_id in list(self.active_cameras.keys()):
            self.stop_camera(camera_id)

    def get_available_cameras(self):
        """Return list of available camera indices."""
        return self.available_cameras 