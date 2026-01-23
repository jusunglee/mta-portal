#!/usr/bin/env python3
"""
One-shot serial capture for debugging CircuitPython devices.
Touches code.py to trigger a restart, then captures output.

Usage: python3 serial_capture.py [seconds]
Default: 10 seconds
"""

import serial
import time
import sys
import glob
import os
from pathlib import Path

CIRCUITPY_PATH = "/Volumes/CIRCUITPY"

def find_circuitpy_serial():
    """Find the CircuitPython serial port."""
    patterns = ['/dev/cu.usbmodem*', '/dev/tty.usbmodem*']
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            return ports[0]
    return None

def trigger_restart():
    """Touch code.py to trigger device restart."""
    code_path = Path(CIRCUITPY_PATH) / "code.py"
    if code_path.exists():
        print(f"Triggering restart by touching {code_path}")
        os.utime(code_path, None)
        time.sleep(0.5)  # Give device time to notice
        return True
    else:
        print(f"WARNING: {code_path} not found, skipping restart trigger")
        return False

def capture_serial(duration=10):
    port = find_circuitpy_serial()
    if port is None:
        print("ERROR: No CircuitPython device found")
        sys.exit(1)

    try:
        ser = serial.Serial(port, 115200, timeout=0.1)
    except serial.SerialException as e:
        print(f"ERROR: Could not open {port}: {e}")
        sys.exit(1)

    trigger_restart()

    print(f"Capturing from {port} for {duration} seconds...")
    print("-" * 50)

    start = time.time()
    while time.time() - start < duration:
        try:
            line = ser.readline()
            if line:
                text = line.decode('utf-8', errors='ignore').rstrip()
                if text and not text.startswith('\x1b]0;'):
                    print(text)
        except (serial.SerialException, OSError) as e:
            print(f"ERROR: {e}")
            break

    ser.close()
    print("-" * 50)
    print("Capture complete")

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    capture_serial(duration)
