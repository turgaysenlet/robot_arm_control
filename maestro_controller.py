import serial
import time

class MaestroController:
    def __init__(self, port='/dev/ttyACM0', device_number=0x0C):
        self.port = port
        self.device_number = device_number
        self.serial = None
        self.connect()
        
        # Define servo channels
        self.BASE_CHANNEL = 0
        self.SHOULDER_CHANNEL = 1
        self.ELBOW_CHANNEL = 2
        self.GRIPPER_CHANNEL = 3
        
        # Define servo limits (in microseconds)
        self.SERVO_MIN = 2000  # Typically ~4000 for 0 degrees
        self.SERVO_MAX = 10000  # Typically ~8000 for 180 degrees
        
        # Current angles
        self.current_angles = {
            'base': 90,
            'shoulder': 90,
            'elbow': 90,
            'gripper': 90
        }

    def connect(self):
        """Connect to the Maestro controller."""
        try:
            self.serial = serial.Serial(self.port, timeout=1)
        except serial.SerialException as e:
            print(f"Error connecting to Maestro: {e}")
            raise

    def close(self):
        """Close the serial connection."""
        if self.serial:
            self.serial.close()

    def _send_command(self, command, channel, value=None):
        """Send a command to the Maestro controller."""
        if value is not None:
            cmd = chr(command) + chr(channel) + chr(value & 0x7F) + chr((value >> 7) & 0x7F)
        else:
            cmd = chr(command) + chr(channel)
        self.serial.write(cmd.encode('latin-1'))

    def set_target(self, channel, target):
        """
        Set channel to a specified target.
        Target is in units of quarter microseconds, so 6000 = 1500 microseconds
        """
        target = max(self.SERVO_MIN, min(self.SERVO_MAX, target))
        self._send_command(0x84, channel, target)

    def set_angle(self, servo_name, angle):
        """Set servo angle (0-180 degrees)."""
        # Ensure angle is within bounds
        angle = max(0, min(360, angle))
        
        # Map angle to servo range
        target = int(self.SERVO_MIN + (angle / 180.0) * (self.SERVO_MAX - self.SERVO_MIN))
        print("Target: ", target)
        # Determine channel based on servo name
        channel_map = {
            'base': self.BASE_CHANNEL,
            'shoulder': self.SHOULDER_CHANNEL,
            'elbow': self.ELBOW_CHANNEL,
            'gripper': self.GRIPPER_CHANNEL
        }
        
        if servo_name in channel_map:
            self.set_target(channel_map[servo_name], target)
            self.current_angles[servo_name] = angle
        else:
            raise ValueError(f"Invalid servo name: {servo_name}")

    def get_angle(self, servo_name):
        """Get the current angle of a servo."""
        return self.current_angles.get(servo_name, 0)

    def emergency_stop(self):
        """Stop all servos immediately."""
        for channel in range(4):
            self.set_target(channel, 6000)  # Move to neutral position 