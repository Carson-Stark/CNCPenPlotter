# CNC Pen Plotter

![skeletonafter](https://github.com/user-attachments/assets/39aa730f-f690-4c4c-bad6-58a236fd3881)

## Project Overview
The CNC Pen Plotter project is designed to control a CNC machine for pen plotting. It allows users to draw intricate designs and patterns using SVG files as input. The project includes a Python script for processing SVG files and an Arduino sketch for controlling the CNC hardware.

### Features
- Full mechanical XY drawing system using stepper motors, drivers, and limit switches
- SVG path parser and GUI interface written in Python using Tkinter
- Selectable fill algorithms: hatching, cross-hatching, center-line filling, and more
- Dynamic path optimization for shortest path and stroke ordering
- Automatic scaling and centering of designs to fit paper dimensions
- Smooth stroke interpolation for Bezier curves with adjustable fidelity
- User-friendly GUI with real-time controls for starting, stopping, and pausing drawings
- Real-time progress tracking including estimated time and total distance
- Serial command interface and live feedback from Arduino microcontroller

### Project Timeline

- **Date Started:** Feburary 2019
- **Date Finished:** June 2019

## Demo Video

https://github.com/user-attachments/assets/00a7063d-4f03-40fc-bda0-691d05dff355

## Hardware

![Screenshot 2025-06-22 195545](https://github.com/user-attachments/assets/8916188a-2256-4e3a-9612-13fc3c97223e)

- **Arduino Uno** for serial control and motor sequencing
- **Nema 17 Stepper Motors (x2)** to drive the X and Y gantries
- **Stepper Motor Driver Shield** (A4988) for precise step control
- **Limit Switches** for automatic homing and calibration
- **Custom-built Frame** with custom cut acrylic, wood blocks, and linear rails for stability and accuracy
- **Servo** for pen lift/drop actuation

## File Structure
- `CNC.ino`: Arduino sketch for controlling the CNC machine.
- `penplotter.py`: Python script for processing SVG files and sending commands to the CNC machine.
- `draw examples/`: Directory containing example SVG files for plotting.
  - Example files include `circle_fancy.svg`, `helicopter.svg`, `hogwarts.svg`, and more.
- `README.md`: Documentation for the project.

## Usage Instructions

![skeleton](https://github.com/user-attachments/assets/c944e568-c591-4d27-bebf-eee15e504551)

1. **Hardware Setup**:
   - Assemble your CNC machine and connect it to your computer.
   - Upload the `CNC.ino` sketch to the Arduino board using the Arduino IDE.

2. **Software Setup**:
   - Ensure you have Python installed on your system.
   - Install any required Python dependencies

3. **Running the Script**:
   - Place your desired SVG file in the `draw examples/` directory.
   - Run the `penplotter.py` script which will start the GUI

4. **Start Plotting**:
   - Ensure the CNC machine Arduino is connected via a serial port (assumes COM4 by default)
   - Load your SVG design by entering the file name and clicking "Use"
   - Configure the fill, smoothness, and other settings
   - When you press start the CNC machine will begin plotting the design from the SVG file.

## Dependencies
- Python 3.x
- `serial`
- `Tkinter`

## License
This project is licensed under the MIT License. See the LICENSE file for details.
