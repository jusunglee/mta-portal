#!/usr/bin/env python3
"""
Serial monitor for CircuitPython devices.
Automatically reconnects when the device reboots or is unplugged.

Usage: python3 ~/serial_monitor.py
"""

import serial
import time
import sys
import glob

def find_circuitpy_serial():
    """Find the CircuitPython serial port."""
    patterns = ['/dev/cu.usbmodem*', '/dev/tty.usbmodem*']
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            return ports[0]
    return None

def monitor_serial():
    port = None
    ser = None

    print("🔌 CircuitPython Serial Monitor")
    print("   Press Ctrl+C to exit\n")
    print("-" * 50)

    while True:
        try:
            # Find port if not connected
            if ser is None:
                port = find_circuitpy_serial()
                if port is None:
                    print("\r⏳ Waiting for device...", end="", flush=True)
                    time.sleep(1)
                    continue

                try:
                    ser = serial.Serial(port, 115200, timeout=0.1)
                    print(f"\n✅ Connected to {port}\n" + "-" * 50)
                except serial.SerialException:
                    time.sleep(1)
                    continue

            # Read and print data
            line = ser.readline()
            if line:
                text = line.decode('utf-8', errors='ignore').rstrip()
                # Filter out terminal control sequences for cleaner output
                if text and not text.startswith('\x1b]0;'):
                    print(text, flush=True)

        except (serial.SerialException, OSError):
            if ser:
                print("\n" + "-" * 50)
                print("🔄 Device disconnected, waiting to reconnect...")
                ser = None
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n👋 Exiting serial monitor")
            if ser:
                ser.close()
            sys.exit(0)

if __name__ == "__main__":
    monitor_serial()
