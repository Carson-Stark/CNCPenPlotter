# CNC Pen Plotter

## Project Overview
The CNC Pen Plotter project is designed to control a CNC machine for pen plotting. It allows users to draw intricate designs and patterns using SVG files as input. The project includes a Python script for processing SVG files and an Arduino sketch for controlling the CNC hardware.

## Features
- Supports SVG file input for plotting.
- Includes a variety of example SVG designs.
- Python script for processing and sending commands to the CNC machine.
- Arduino sketch for precise control of the CNC hardware.

## File Structure
- `CNC.ino`: Arduino sketch for controlling the CNC machine.
- `penplotter.py`: Python script for processing SVG files and sending commands to the CNC machine.
- `draw examples/`: Directory containing example SVG files for plotting.
  - Example files include `circle_fancy.svg`, `helicopter.svg`, `hogwarts.svg`, and more.
- `README.md`: Documentation for the project.

## Usage Instructions
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