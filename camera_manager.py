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
        """Start the camera stream with the best available backend."""
        self.running = True

        # Try different backends in case some fail
        backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_VFW]  # Windows preferred order
        for backend in backends:
            self.cap = cv2.VideoCapture(self.camera_index, backend)
            if self.cap.isOpened():
                print(f"Camera {self.camera_index} opened successfully using backend {backend}")
                break
            else:
                self.cap.release()

        if not self.cap or not self.cap.isOpened():
            self.error.emit(f"Failed to open camera {self.camera_index}")
            return

        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)
            else:
                self.error.emit(f"Error reading from camera {self.camera_index}")
                break

        self.cap.release()

    def stop(self):
        """Stop the camera stream"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()

if __name__ == "__main__":
    manager = CameraManager()
    print("Detected Cameras:", manager.get_available_cameras())
