import pygame
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time

class PS4Controller(QObject):
    control_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        pygame.init()
        pygame.joystick.init()
        
        self.controller = None
        self.axis_data = {}
        self.button_data = {}
        self.running = False
        
        # Initialize controller if available
        self.connect()
        
        # Control settings
        self.angle_increment = 2  # degrees per update
        self.update_rate = 50  # milliseconds
        
        # Setup timer for polling
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_loop)
        
    def connect(self):
        """Connect to the first available controller."""
        try:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            print("PS4 Controller connected")
            self._print_controller_info()
            return True
        except pygame.error:
            print("No PS4 controller found")
            return False

    def _print_controller_info(self):
        """Print information about the connected controller."""
        print(f"\nController Info:")
        print(f"Name: {self.controller.get_name()}")
        print(f"Number of axes: {self.controller.get_numaxes()}")
        print(f"Number of buttons: {self.controller.get_numbuttons()}")
        print(f"Number of hats: {self.controller.get_numhats()}\n")

    def start(self):
        """Start controller polling."""
        if not self.running and self.controller:
            self.running = True
            self.timer.start(self.update_rate)

    def stop(self):
        """Stop controller polling."""
        self.running = False
        self.timer.stop()

    def _update_loop(self):
        """Main controller update loop."""
        if not self.running:
            return
            
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                self.axis_data[event.axis] = round(event.value, 2)
                print(f"Axis {event.axis} value: {event.value}")
            elif event.type == pygame.JOYBUTTONDOWN:
                self.button_data[event.button] = True
                print(f"Button {event.button} pressed")
            elif event.type == pygame.JOYBUTTONUP:
                self.button_data[event.button] = False
                print(f"Button {event.button} released")
        
        # Get and print control changes
        changes = self.get_controls()
        if any(abs(v) > 0.1 for v in changes.values()):
            print(f"Control changes: {changes}")
        
        # Emit control updates
        self.control_updated.emit(changes)

    def get_controls(self):
        """
        Get current control values for robot arm.
        Returns dict with changes to apply to servo angles.
        """
        changes = {
            'base': 0,
            'shoulder': 0,
            'elbow': 0,
            'gripper': 0
        }
        
        if not self.controller:
            return changes

        try:
            # PS4 Controller axis mapping:
            # 0: Left stick horizontal (left: -1, right: 1)
            # 1: Left stick vertical (up: -1, down: 1)
            # 2: Right stick horizontal (left: -1, right: 1)
            # 3: Right stick vertical (up: -1, down: 1)
            # 4: L2 trigger (-1 to 1)
            # 5: R2 trigger (-1 to 1)

            # Base rotation (left/right on left stick)
            if 0 in self.axis_data:
                if abs(self.axis_data[0]) > 0.1:  # Dead zone
                    changes['base'] = self.angle_increment * -self.axis_data[0]  # Invert for intuitive control

            # Shoulder (up/down on right stick)
            if 3 in self.axis_data:
                if abs(self.axis_data[3]) > 0.1:
                    changes['shoulder'] = self.angle_increment * self.axis_data[3]  # Remove negative

            # Elbow (up/down on left stick)
            if 1 in self.axis_data:
                if abs(self.axis_data[1]) > 0.1:
                    changes['elbow'] = self.angle_increment * self.axis_data[1]  # Remove negative

            # Gripper (L2/R2 triggers)
            # L2 closes (-1 to 1), R2 opens (-1 to 1)
            l2 = self.axis_data.get(4, -1)  # Default to -1 when not pressed
            r2 = self.axis_data.get(5, -1)  # Default to -1 when not pressed
            
            # Map from -1,1 to 0,1 range
            l2_mapped = (l2 + 1) / 2
            r2_mapped = (r2 + 1) / 2
            
            gripper_change = (r2_mapped - l2_mapped) * self.angle_increment
            changes['gripper'] = gripper_change

        except Exception as e:
            print(f"Error in get_controls: {e}")
            print(f"Current axis_data: {self.axis_data}")

        return changes 