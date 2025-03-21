import sys
import platform
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QComboBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from camera_manager import CameraManager
from controller import PS4Controller
from maestro_controller import MaestroController

class RobotArmControlUI(QMainWindow):
    def handle_camera_error(self, side, error_msg):
        """Handle camera errors by displaying a message and resetting the state."""
        print(f"Camera error ({side}): {error_msg}")

        button = self.left_camera_button if side == "left" else self.right_camera_button
        label = self.left_camera_label if side == "left" else self.right_camera_label

        if self.active_cameras[side] is not None:
            self.camera_manager.stop_camera(self.active_cameras[side])
            self.active_cameras[side] = None

        label.setText(f"Camera Error:\n{error_msg}")
        button.setText("Start Camera")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEZYbotARM MK2 Controller")
        self.setGeometry(100, 100, 1200, 800)

        self.camera_manager = CameraManager()
        self.controller = PS4Controller()
        self.controller.control_updated.connect(self.update_robot)

        self.active_cameras = {"left": None, "right": None}
        self.desired_angles = {'base': 90, 'shoulder': 90, 'elbow': 90, 'gripper': 90}

        try:
            self.servo_controller = MaestroController(port='COM12')  # Change COM port if needed
        except Exception as e:
            print(f"Error initializing Maestro controller: {e}")
            self.servo_controller = None

        self.setup_ui()

    def update_robot(self, changes):
        """Handle controller updates and move the robot arm accordingly."""
        print(f"Updating robot with changes: {changes}")

        for servo_name, change in changes.items():
            if change != 0:
                current = self.desired_angles.get(servo_name, 90)
                new_angle = max(0, min(180, current + change))
                print(f"Setting {servo_name} from {current} to {new_angle}")
                self.desired_angles[servo_name] = new_angle

                if self.servo_controller:
                    self.servo_controller.set_angle(servo_name, new_angle)

        self.update_gauges()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        camera_layout = QHBoxLayout()

        # Left camera controls
        left_camera_widget = QWidget()
        left_camera_layout = QVBoxLayout(left_camera_widget)
        self.left_camera_label = QLabel()
        self.left_camera_label.setMinimumSize(400, 300)
        self.left_camera_combo = QComboBox()
        self.left_camera_combo.addItems([f"Camera {i}" for i in self.camera_manager.get_available_cameras()])
        self.left_camera_button = QPushButton("Start Camera")
        self.left_camera_button.clicked.connect(lambda: self.toggle_camera("left"))
        left_camera_layout.addWidget(self.left_camera_label)
        left_camera_layout.addWidget(self.left_camera_combo)
        left_camera_layout.addWidget(self.left_camera_button)

        # Right camera controls
        right_camera_widget = QWidget()
        right_camera_layout = QVBoxLayout(right_camera_widget)
        self.right_camera_label = QLabel()
        self.right_camera_label.setMinimumSize(400, 300)
        self.right_camera_combo = QComboBox()
        self.right_camera_combo.addItems([f"Camera {i}" for i in self.camera_manager.get_available_cameras()])
        self.right_camera_button = QPushButton("Start Camera")
        self.right_camera_button.clicked.connect(lambda: self.toggle_camera("right"))
        right_camera_layout.addWidget(self.right_camera_label)
        right_camera_layout.addWidget(self.right_camera_combo)
        right_camera_layout.addWidget(self.right_camera_button)

        camera_layout.addWidget(left_camera_widget)
        camera_layout.addWidget(right_camera_widget)

        main_layout.addLayout(camera_layout)

    def toggle_camera(self, side):
        button = self.left_camera_button if side == "left" else self.right_camera_button
        combo = self.left_camera_combo if side == "left" else self.right_camera_combo
        label = self.left_camera_label if side == "left" else self.right_camera_label

        if self.active_cameras[side] is None:
            camera_id = int(combo.currentText().split()[-1])
            camera_thread = self.camera_manager.start_camera(camera_id)
            camera_thread.frame_ready.connect(
                lambda frame: self.update_camera_feed(frame, label))
            camera_thread.error.connect(
                lambda msg: self.handle_camera_error(side, msg))
            self.active_cameras[side] = camera_id
            button.setText("Stop Camera")
        else:
            self.camera_manager.stop_camera(self.active_cameras[side])
            self.active_cameras[side] = None
            label.clear()
            button.setText("Start Camera")

    def update_camera_feed(self, frame, label):
        # Convert BGR (OpenCV) to RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        scaled_pixmap = pixmap.scaled(label.size(),
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.camera_manager.stop_all_cameras()
        if self.controller.running:
            self.controller.stop()
        if self.servo_controller:
            self.servo_controller.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RobotArmControlUI()
    window.show()
    sys.exit(app.exec())
