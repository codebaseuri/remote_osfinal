@echo off
echo ======================================
echo Remote Control Client Setup
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.7 or newer and try again.
    echo You can download Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python is installed. Proceeding with package installation...
echo.

REM Install required packages
echo Installing required packages...
echo.

echo Installing OpenCV (cv2)...
pip install opencv-python

echo Installing NumPy...
pip install numpy

echo Installing socket (part of standard library)...

echo Installing pickle (part of standard library)...

echo Installing struct (part of standard library)...

echo Installing threading (part of standard library)...

echo Installing time (part of standard library)...

echo Installing traceback (part of standard library)...

echo Installing json (part of standard library)...

echo Installing logging (part of standard library)...

echo Installing os (part of standard library)...

echo Installing getpass (part of standard library)...

echo Installing sys (part of standard library)...

echo Installing pynput (for mouse and keyboard control)...
pip install pynput

echo Installing PyQt5 (for the GUI client)...
pip install PyQt5

echo.
echo ======================================
echo Installation completed!
echo ======================================
echo.
echo You can now run the Remote Control Client.
echo.
echo To start the console version: python pickle-client.py
echo To start the GUI version: python improved_gui.py
echo.
pause