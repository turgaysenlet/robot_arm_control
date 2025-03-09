import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QComboBox, QLabel)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap
import pyqtgraph as pg
import numpy as np
from camera_manager import CameraManager
from controller import PS4Controller
from maestro_controller import MaestroController

class RobotArmControlUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEZYbotARM MK2 Controller")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize components
        self.camera_manager = CameraManager()
        self.controller = PS4Controller()
        self.controller.control_updated.connect(self.update_robot)
        
        # Track desired angles separately from servo controller
        self.desired_angles = {
            'base': 90,
            'shoulder': 90,
            'elbow': 90,
            'gripper': 90
        }
        
        try:
            self.servo_controller = MaestroController(port='/dev/cu.usbmodem00000000001A1')  # Updated port for macOS
        except Exception as e:
            print(f"Error initializing Maestro controller: {e}")
            self.servo_controller = None

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Camera feeds section
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
        
        # Servo gauges section
        gauge_layout = QHBoxLayout()
        self.gauges = {}
        
        for servo_name in ['base', 'shoulder', 'elbow', 'gripper']:
            # Create plot widget
            gauge_widget = pg.PlotWidget()
            gauge_widget.setBackground('w')
            gauge_widget.setAspectLocked(True)
            gauge_widget.hideAxis('left')
            gauge_widget.hideAxis('bottom')
            gauge_widget.setRange(xRange=(-1.2, 1.2), yRange=(-1.2, 1.2))
            
            # Create circle using plot
            theta = np.linspace(0, 2*np.pi, 100)
            circle_x = np.cos(theta)
            circle_y = np.sin(theta)
            gauge_widget.plot(circle_x, circle_y, pen=pg.mkPen('k'))
            
            # Add angle markers (0°, 90°, 180°)
            marker_angles = [0, 90, 180]  # degrees
            for angle in marker_angles:
                # Convert to radians and rotate by -90 to make 0 point up
                rad = (angle - 90) * np.pi / 180
                x = 1.1 * np.cos(rad)
                y = 1.1 * np.sin(rad)
                text = pg.TextItem(str(angle) + "°", anchor=(0.5, 0.5))
                text.setPos(x, y)
                gauge_widget.addItem(text)
            
            # Add tick marks every 45 degrees
            for angle in range(0, 360, 45):
                rad = angle * np.pi / 180
                inner_x = 0.9 * np.cos(rad)
                inner_y = 0.9 * np.sin(rad)
                outer_x = np.cos(rad)
                outer_y = np.sin(rad)
                gauge_widget.plot([inner_x, outer_x], [inner_y, outer_y], pen=pg.mkPen('k'))
            
            # Create pointer starting at 90 degrees (pointing up)
            pointer = gauge_widget.plot([0, 0], [0, 1], pen=pg.mkPen('r', width=3))
            
            self.gauges[servo_name] = {
                'widget': gauge_widget,
                'pointer': pointer
            }
            
            # Add label
            servo_label = QLabel(servo_name.capitalize())
            servo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add current angle label
            angle_label = QLabel("90°")
            angle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gauges[servo_name]['angle_label'] = angle_label
            
            gauge_container = QWidget()
            gauge_container_layout = QVBoxLayout(gauge_container)
            gauge_container_layout.addWidget(servo_label)
            gauge_container_layout.addWidget(gauge_widget)
            gauge_container_layout.addWidget(angle_label)
            
            gauge_layout.addWidget(gauge_container)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.controller_button = QPushButton("Start Controller")
        self.controller_button.clicked.connect(self.toggle_controller)
        
        self.emergency_stop_button = QPushButton("Emergency Stop")
        self.emergency_stop_button.clicked.connect(self.emergency_stop)
        self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
        
        button_layout.addWidget(self.controller_button)
        button_layout.addWidget(self.emergency_stop_button)
        
        # Add all layouts to main layout
        main_layout.addLayout(camera_layout)
        main_layout.addLayout(gauge_layout)
        main_layout.addLayout(button_layout)
        
        # Initialize camera states
        self.active_cameras = {"left": None, "right": None}

    def toggle_camera(self, side):
        button = self.left_camera_button if side == "left" else self.right_camera_button
        combo = self.left_camera_combo if side == "left" else self.right_camera_combo
        label = self.left_camera_label if side == "left" else self.right_camera_label
        
        if self.active_cameras[side] is None:
            # Start camera
            camera_id = int(combo.currentText().split()[-1])
            camera_thread = self.camera_manager.start_camera(camera_id)
            camera_thread.frame_ready.connect(
                lambda frame: self.update_camera_feed(frame, label))
            camera_thread.error.connect(
                lambda msg: self.handle_camera_error(side, msg))
            self.active_cameras[side] = camera_id
            button.setText("Stop Camera")
        else:
            # Stop camera
            self.camera_manager.stop_camera(self.active_cameras[side])
            self.active_cameras[side] = None
            label.clear()
            button.setText("Start Camera")

    def update_camera_feed(self, frame, label):
        pixmap = QPixmap.fromImage(frame)
        scaled_pixmap = pixmap.scaled(label.size(), 
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)

    def handle_camera_error(self, side, error_msg):
        """Handle camera errors by showing message and resetting state."""
        print(f"Camera error ({side}): {error_msg}")
        button = self.left_camera_button if side == "left" else self.right_camera_button
        label = self.left_camera_label if side == "left" else self.right_camera_label
        
        # Stop the camera
        if self.active_cameras[side] is not None:
            self.camera_manager.stop_camera(self.active_cameras[side])
            self.active_cameras[side] = None
        
        # Update UI
        label.setText(f"Camera Error:\n{error_msg}")
        button.setText("Start Camera")

    def toggle_controller(self):
        if not self.controller.running:
            if self.controller.connect():
                print("Starting controller")
                self.controller.start()
                self.controller_button.setText("Stop Controller")
        else:
            print("Stopping controller")
            self.controller.stop()
            self.controller_button.setText("Start Controller")

    def update_robot(self, changes):
        """Handle controller updates."""
        print(f"Updating robot with changes: {changes}")
        
        # Update desired angles based on controller input
        for servo_name, change in changes.items():
            if change != 0:
                current = self.desired_angles[servo_name]
                new_angle = max(0, min(180, current + change))
                print(f"Setting {servo_name} from {current} to {new_angle}")
                self.desired_angles[servo_name] = new_angle
                
                # Update actual servo if connected
                if self.servo_controller:
                    self.servo_controller.set_angle(servo_name, new_angle)
        
        # Update gauges
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
            
            print(f"Updating gauge for {servo_name}: {angle}° ({end_x:.2f}, {end_y:.2f})")
            
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

    def emergency_stop(self):
        """Reset all angles to 90 degrees and stop controller."""
        # Reset desired angles
        for servo_name in self.desired_angles:
            self.desired_angles[servo_name] = 90
        
        # Update actual servos if connected
        if self.servo_controller:
            self.servo_controller.emergency_stop()
        
        if self.controller.running:
            self.controller.stop()
            self.controller_button.setText("Start Controller")
        
        # Update gauges to show reset position
        self.update_gauges()

    def closeEvent(self, event):
        # Cleanup when closing the application
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