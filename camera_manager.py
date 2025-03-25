import cv2
import threading
from PyQt5.QtCore import pyqtSignal, QThread
from cv2_enumerate_cameras import enumerate_cameras

class CameraThread(QThread):
    frame_ready = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None

    def run(self):
        """Start the camera stream."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.error.emit(f"Failed to open camera {self.camera_index}")
                return

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            while self.running:
                ret, frame = self.cap.read()
                if ret:
                    self.frame_ready.emit(frame)
                else:
                    self.error.emit(f"Error reading from camera {self.camera_index}")
                    break
                self.msleep(30)  # Limit frame rate to ~30 fps
                
        except Exception as e:
            self.error.emit(f"Camera error: {str(e)}")
        finally:
            if self.cap:
                self.cap.release()
            self.running = False

    def stop(self):
        """Stop the camera stream"""
        self.running = False
        self.wait()
        if self.cap:
            self.cap.release()
            self.cap = None

class CameraManager:
    def __init__(self):
        self.available_cameras = self._get_available_cameras()
        self.active_cameras = {}

    def _get_available_cameras(self):
        """Find all available cameras."""
        available = []
        for i in range(10):  # Check first 10 indexes
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    available.append(i)
                cap.release()
            except Exception as e:
                print(f"Error checking camera {i}: {e}")
            finally:
                if cap:
                    cap.release()
        return available

    def start_camera(self, camera_id):
        """Start a camera stream."""
        # If camera is already running, return existing thread
        if camera_id in self.active_cameras and self.active_cameras[camera_id].running:
            return self.active_cameras[camera_id]
        
        # Stop existing camera if it exists
        if camera_id in self.active_cameras:
            self.stop_camera(camera_id)
        
        # Create and start new camera thread
        camera_thread = CameraThread(camera_id)
        self.active_cameras[camera_id] = camera_thread
        camera_thread.start()
        return camera_thread

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

if __name__ == "__main__":
    manager = CameraManager()
    print("Detected Cameras:", manager.get_available_cameras())
