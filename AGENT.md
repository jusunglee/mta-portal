# Agent Instructions for MTA Portal

## Iteration Workflow

This is a CircuitPython project running on a MatrixPortal device. The device auto-reloads when files change.

### To iterate on code changes:

1. Make edits to `code.py` (the main file that runs on the device)
2. Run the serial capture to see output:
   ```bash
   uv run tools/serial_capture.py 15
   ```
   This will:
   - Touch `/Volumes/CIRCUITPY/code.py` to trigger a device restart
   - Capture serial output for 15 seconds (adjust as needed)
   - Show boot sequence, errors, and runtime output

3. Read the output, fix any errors, repeat

### Common Errors

- **"Socket not managed"** - Usually caused by calling `connection_manager_close_all()` while sockets are still in use. Only call this in error handlers.
- **OutOfRetries** - Network request failed after retries. Make sure to catch `adafruit_requests.OutOfRetries` in exception handlers.
- **ConnectionError** - Transient network issues. Add retry logic and catch this exception.

### Key Files

- `code.py` - Main application code (runs on device)
- `settings.toml` - WiFi credentials (on device, not in repo)
- `example_settings.toml` - Template for settings.toml
- `tools/serial_capture.py` - One-shot serial capture for debugging
- `tools/serial_monitor.py` - Continuous serial monitor
- `tools/test_wifi_and_esp32.py` - WiFi and ESP32 test utility

### Device Location

The CircuitPython device mounts at `/Volumes/CIRCUITPY`. The serial port is typically `/dev/cu.usbmodem*`.

### Exception Handling Pattern

CircuitPython network code can throw many exception types. Use this pattern:
```python
except (ValueError, RuntimeError, BrokenPipeError, OSError, ConnectionError, adafruit_requests.OutOfRetries) as e:
    print("Error:", type(e).__name__, e)
    adafruit_connection_manager.connection_manager_close_all()
    network._wifi.esp.reset()
    time.sleep(2)
    network.connect()
```
