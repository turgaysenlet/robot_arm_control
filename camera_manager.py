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
        backends = [cv2.CAP_DSHOW] #, cv2.CAP_MSMF, cv2.CAP_VFW]  # Windows preferred order
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

if __name__ == "__main__":
    manager = CameraManager()
    print("Detected Cameras:", manager.get_available_cameras())
