@echo off
REM Step 1: Go to the Scripts folder where activate.bat is located
cd /d C:\ultrasonic-holography-tests\blender-venv\test-blender-venv\Scripts

REM Step 2: Run activate.bat to activate the virtual environment
call activate.bat

REM Step 3: Go back to the main directory
cd /d C:\ultrasonic-holography-tests\blender-venv

REM Step 4: Run python canvas_control.py in a new window
start cmd /k "python canvas_control.py"

REM Step 5: Open a new window and run the rust commands
start cmd /k "cd C:\ultrasonic-holography-tests\blender-venv\rust_sonic_surface && cargo run --release --bin redis_positions_to_ftdi"