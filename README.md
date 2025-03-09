# EEZYbotARM MK2 Controller

A Python application for controlling the EEZYbotARM MK2 robot arm using a PS4 controller and Maestro 6-channel servo controller. The application features a modern UI with dual camera feeds and real-time servo angle visualization.

## Features

- Dual camera feed support with camera selection
- PS4 controller integration for intuitive robot arm control
- Real-time servo angle visualization using circular gauges
- Emergency stop functionality
- Clean and modern PyQt5-based user interface

## Hardware Requirements

- EEZYbotARM MK2 robot arm
- Pololu Maestro 6-Channel USB Servo Controller
- PS4 Controller (connected via Bluetooth)
- USB cameras (up to 2)
- Servos:
  - Base rotation: Channel 0
  - Shoulder: Channel 1
  - Elbow: Channel 2
  - Gripper: Channel 3

## Software Requirements

- Python 3.8 or higher
- PyQt6
- OpenCV
- pygame (for PS4 controller)
- pyserial (for Maestro controller)
- pyqtgraph
- numpy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/robot_arm_control.git
cd robot_arm_control
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Connect the Maestro controller to your computer via USB
2. Pair your PS4 controller via Bluetooth
3. Connect your USB cameras
4. Run the application:
```bash
python main.py
```

### Controls

PS4 Controller mapping:
- Left stick X-axis: Base rotation
- Left stick Y-axis: Elbow angle
- Right stick Y-axis: Shoulder angle
- L2/R2 triggers: Gripper control

UI Features:
- Camera dropdowns: Select which cameras to use
- Start/Stop Camera buttons: Toggle camera feeds
- Start Controller button: Enable/disable PS4 controller
- Emergency Stop: Immediately stop all servos
- Servo gauges: Visual feedback of current servo angles

## Troubleshooting

1. **Maestro Controller Not Found**
   - Ensure the controller is properly connected via USB
   - Check if the correct port is specified in `maestro_controller.py`
   - Verify you have the necessary permissions to access the USB port

2. **PS4 Controller Not Detected**
   - Make sure the controller is paired via Bluetooth
   - Check if the controller is charged
   - Try reconnecting the controller

3. **Cameras Not Working**
   - Verify the cameras are properly connected
   - Check if other applications are using the cameras
   - Ensure you have the necessary permissions to access the cameras

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 