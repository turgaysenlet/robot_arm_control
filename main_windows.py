import sys
import platform
import cv2
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QComboBox, QLabel,
    QSlider
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
        self.servo_limits = {
            'base': {'min': -40, 'max': 180},
            'shoulder': {'min': 90, 'max': 160},
            'elbow': {'min': 90, 'max': 120},
            'gripper': {'min': 95, 'max': 180}
        }
        self.gauges = {}

        try:
            self.servo_controller = MaestroController(port='COM12')  # Change COM port if needed
        except Exception as e:
            print(f"Error initializing Maestro controller: {e}")
            self.servo_controller = None

        self.setup_ui()

    def update_robot(self, changes):
        """Handle controller updates and move the robot arm accordingly."""
        # print(f"Updating robot with changes: {changes}")

        for servo_name, change in changes.items():
            if change != 0:
                current = self.desired_angles.get(servo_name, 90)
                # Apply servo limits
                new_angle = max(
                    self.servo_limits[servo_name]['min'],
                    min(self.servo_limits[servo_name]['max'],
                        current + change)
                )
                print(f"Setting {servo_name} from {current} to {new_angle}")
                self.desired_angles[servo_name] = new_angle

                if self.servo_controller:
                    self.servo_controller.set_angle(servo_name, new_angle)

        self.update_gauges()

    def update_gauges(self):
        """Update gauge displays using desired angles."""
        for servo_name, gauge in self.gauges.items():
            angle = self.desired_angles[servo_name]
            # Convert to radians and rotate by -90 degrees to make 0 point up
            rad_angle = (angle - 90) * np.pi / 180
            
            # Calculate pointer end point
            end_x = np.cos(rad_angle)
            end_y = np.sin(rad_angle)
            
            # Update pointer line (from center to edge)
            gauge['pointer'].setData(
                [0, end_x],
                [0, end_y]
            )
            
            # Update angle label
            gauge['angle_label'].setText(f"{int(angle)}°")
            
            # Force immediate update
            gauge['widget'].update()
            QApplication.processEvents()

    def toggle_controller(self):
        """Toggle PS4 controller on/off."""
        if not self.controller.running:
            if self.controller.connect():
                print("Starting controller")
                self.controller.start()
                self.controller_button.setText("Stop Controller")
        else:
            print("Stopping controller")
            self.controller.stop()
            self.controller_button.setText("Start Controller")

    def emergency_stop(self):
        """Reset all angles to middle of their range and stop controller."""
        # Reset desired angles to middle of their range
        for servo_name in self.desired_angles:
            min_angle = self.servo_limits[servo_name]['min']
            max_angle = self.servo_limits[servo_name]['max']
            middle_angle = (min_angle + max_angle) // 2
            self.desired_angles[servo_name] = middle_angle
        
        # Update actual servos if connected
        if self.servo_controller:
            self.servo_controller.emergency_stop()
        
        if self.controller.running:
            self.controller.stop()
            self.controller_button.setText("Start Controller")
        
        # Update gauges to show reset position
        self.update_gauges()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create horizontal layout for cameras and gauges
        top_layout = QHBoxLayout()

        # Camera section (takes more space)
        camera_widget = QWidget()
        camera_layout = QHBoxLayout(camera_widget)
        camera_layout.setSpacing(20)  # Increased spacing between cameras

        # Left camera controls
        left_camera_widget = QWidget()
        left_camera_layout = QVBoxLayout(left_camera_widget)
        left_camera_layout.setSpacing(5)  # Reduced spacing between controls
        self.left_camera_label = QLabel()
        self.left_camera_label.setMinimumSize(640, 480)  # Larger minimum size
        self.left_camera_label.setStyleSheet("QLabel { background-color: black; }")  # Black background
        self.left_camera_combo = QComboBox()
        self.left_camera_combo.addItems([f"Camera {i}" for i in self.camera_manager.get_available_cameras()])
        self.left_camera_button = QPushButton("Start Camera")
        left_camera_layout.addWidget(self.left_camera_label, stretch=1)
        left_camera_layout.addWidget(self.left_camera_combo)
        left_camera_layout.addWidget(self.left_camera_button)

        # Right camera controls
        right_camera_widget = QWidget()
        right_camera_layout = QVBoxLayout(right_camera_widget)
        right_camera_layout.setSpacing(5)  # Reduced spacing between controls
        self.right_camera_label = QLabel()
        self.right_camera_label.setMinimumSize(640, 480)  # Larger minimum size
        self.right_camera_label.setStyleSheet("QLabel { background-color: black; }")  # Black background
        self.right_camera_combo = QComboBox()
        self.right_camera_combo.addItems([f"Camera {i}" for i in self.camera_manager.get_available_cameras()])
        self.right_camera_button = QPushButton("Start Camera")
        right_camera_layout.addWidget(self.right_camera_label, stretch=1)
        right_camera_layout.addWidget(self.right_camera_combo)
        right_camera_layout.addWidget(self.right_camera_button)

        # Connect camera buttons
        self.left_camera_button.clicked.connect(lambda: self.toggle_camera("left"))
        self.right_camera_button.clicked.connect(lambda: self.toggle_camera("right"))

        # Add cameras to layout with equal stretch
        camera_layout.addWidget(left_camera_widget, stretch=1)
        camera_layout.addWidget(right_camera_widget, stretch=1)

        # Gauge section (takes less space)
        gauge_widget = QWidget()
        gauge_widget.setMaximumWidth(300)  # Limit gauge section width
        gauge_layout = QVBoxLayout(gauge_widget)
        gauge_layout.setSpacing(5)  # Reduced spacing between gauges

        # Create gauges for each servo
        for servo_name in ['base', 'shoulder', 'elbow', 'gripper']:
            # Create plot widget
            gauge_plot = pg.PlotWidget()
            gauge_plot.setBackground('w')
            gauge_plot.setAspectLocked(True)
            gauge_plot.hideAxis('left')
            gauge_plot.hideAxis('bottom')
            gauge_plot.setRange(xRange=(-1.2, 1.2), yRange=(-1.2, 1.2))
            gauge_plot.setMaximumHeight(180)  # Smaller gauge height
            
            # Create circle using plot
            theta = np.linspace(0, 2*np.pi, 100)
            circle_x = np.cos(theta)
            circle_y = np.sin(theta)
            gauge_plot.plot(circle_x, circle_y, pen=pg.mkPen('k'))
            
            # Add angle markers (0°, 90°, 180°)
            marker_angles = [0, 90, 180]
            for angle in marker_angles:
                rad = (angle - 90) * np.pi / 180
                x = 1.1 * np.cos(rad)
                y = 1.1 * np.sin(rad)
                text = pg.TextItem(str(angle) + "°", anchor=(0.5, 0.5))
                text.setPos(x, y)
                gauge_plot.addItem(text)
            
            # Add tick marks every 45 degrees
            for angle in range(0, 360, 45):
                rad = angle * np.pi / 180
                inner_x = 0.9 * np.cos(rad)
                inner_y = 0.9 * np.sin(rad)
                outer_x = np.cos(rad)
                outer_y = np.sin(rad)
                gauge_plot.plot([inner_x, outer_x], [inner_y, outer_y], pen=pg.mkPen('k'))
            
            # Create pointer
            pointer = gauge_plot.plot([0, 0], [0, 1], pen=pg.mkPen('r', width=3))
            
            # Store gauge components
            self.gauges[servo_name] = {
                'widget': gauge_plot,
                'pointer': pointer
            }
            
            # Add labels
            servo_label = QLabel(servo_name.capitalize())
            servo_label.setAlignment(Qt.AlignCenter)
            angle_label = QLabel("90°")
            angle_label.setAlignment(Qt.AlignCenter)
            self.gauges[servo_name]['angle_label'] = angle_label
            
            # Create container for gauge and labels
            gauge_container = QWidget()
            gauge_container_layout = QVBoxLayout(gauge_container)
            gauge_container_layout.setSpacing(2)  # Minimal spacing
            gauge_container_layout.addWidget(servo_label)
            gauge_container_layout.addWidget(gauge_plot)
            gauge_container_layout.addWidget(angle_label)
            
            gauge_layout.addWidget(gauge_container)

        # Add camera and gauge sections to top layout
        top_layout.addWidget(camera_widget, stretch=4)  # Camera section takes 80% width
        top_layout.addWidget(gauge_widget, stretch=1)  # Gauge section takes 20% width

        # Add control buttons and speed slider
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)  # More space between controls
        
        # Left side - buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)  # More space between buttons
        
        self.controller_button = QPushButton("Start Controller")
        self.controller_button.setMinimumHeight(40)  # Taller buttons
        self.controller_button.clicked.connect(self.toggle_controller)
        
        self.emergency_stop_button = QPushButton("Emergency Stop")
        self.emergency_stop_button.setMinimumHeight(40)  # Taller buttons
        self.emergency_stop_button.clicked.connect(self.emergency_stop)
        self.emergency_stop_button.setStyleSheet("QPushButton { background-color: red; color: white; font-weight: bold; }")
        
        button_layout.addWidget(self.controller_button)
        button_layout.addWidget(self.emergency_stop_button)
        
        # Right side - speed control
        speed_layout = QHBoxLayout()
        speed_layout.setSpacing(10)
        
        speed_label = QLabel("Speed:")
        self.speed_value_label = QLabel("5.0x")  # Initial value
        self.speed_value_label.setMinimumWidth(50)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)  # 0.1x
        self.speed_slider.setMaximum(200)  # 20.0x
        self.speed_slider.setValue(40)  # 4.0x
        self.speed_slider.valueChanged.connect(self.update_speed)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider, stretch=1)
        speed_layout.addWidget(self.speed_value_label)
        
        # Add button and speed layouts to controls layout
        controls_layout.addLayout(button_layout, stretch=1)
        controls_layout.addLayout(speed_layout, stretch=1)

        # Add layouts to main layout
        main_layout.addLayout(top_layout, stretch=1)
        main_layout.addLayout(controls_layout)

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
        """Update camera feed with proper scaling."""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Create QImage and QPixmap
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale pixmap to fit label while maintaining aspect ratio
            label_size = label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the scaled pixmap in the label
            label.setAlignment(Qt.AlignCenter)
            label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error updating camera feed: {e}")

    def update_speed(self):
        """Update the movement speed multiplier."""
        speed = self.speed_slider.value() / 10.0  # Convert slider value to actual multiplier
        self.controller.set_speed_multiplier(speed)
        self.speed_value_label.setText(f"{speed:.1f}x")

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
