# Use me to test your WiFi connection and ESP32 firmware, if needed.

import time
from board import NEOPIXEL
from adafruit_matrixportal.network import Network

print("Boot")

# Create network object with debug enabled
network = Network(status_neopixel=NEOPIXEL, debug=True)
print("Network created")

# Force WiFi connection
print("Connecting to WiFi...")
network.get_local_time()
print("Connected!")

# Give ESP32 time to stabilize
print("Waiting for ESP32 to stabilize...")
time.sleep(2)

# Fetch example.com (try HTTP first)
print("Fetching example.com...")
response = network.fetch("http://example.com")
print("Response:", response.text)
