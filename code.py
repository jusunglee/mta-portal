import time
import microcontroller
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import adafruit_connection_manager
import adafruit_requests

STOP_ID = 'F20'
DATA_SOURCE = 'https://api.wheresthefuckingtrain.com/by-id/%s' % (STOP_ID,)
DATA_LOCATION = ["data"]
UPDATE_DELAY = 15 # seconds
SYNC_TIME_DELAY = 30 # seconds
MINIMUM_MINUTES_DISPLAY = 5 # minutes
BACKGROUND_IMAGE = 'g-dashboard.bmp'
ERROR_RESET_THRESHOLD = 3

def get_arrival_in_minutes_from_now(now, date_str):
    train_date = datetime.fromisoformat(date_str).replace(tzinfo=None) # Remove tzinfo to be able to diff dates
    return round((train_date-now).total_seconds()/60.0)

def get_arrival_times():
    # Close any stale sockets before fetching
    adafruit_connection_manager.connection_manager_close_all()
    stop_trains =  network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
    stop_data = stop_trains[0]

    # Filter northbound trains by route
    g_trains = [x['time'] for x in stop_data['N'] if x['route'] == 'G']
    f_trains = [x['time'] for x in stop_data['N'] if x['route'] == 'F']

    now = datetime.now()
    print("Now: ", now)

    g_arrivals = [get_arrival_in_minutes_from_now(now, x) for x in g_trains]
    f_arrivals = [get_arrival_in_minutes_from_now(now, x) for x in f_trains]

    g = [str(x) for x in g_arrivals if x >= MINIMUM_MINUTES_DISPLAY]
    f = [str(x) for x in f_arrivals if x >= MINIMUM_MINUTES_DISPLAY]

    g0 = g[0] if len(g) > 0 else '-'
    g1 = g[1] if len(g) > 1 else '-'
    f0 = f[0] if len(f) > 0 else '-'
    f1 = f[1] if len(f) > 1 else '-'

    return g0, g1, f0, f1

def update_text(g0, g1, f0, f1):
    text_lines[2].text = "%s,%s m" % (g0, g1)
    text_lines[4].text = "%s,%s m" % (f0, f1)
    display.root_group = group

# --- Display setup ---
print('boot')
matrix = Matrix(bit_depth=6)
print('Matrix')
display = matrix.display
network = Network(status_neopixel=NEOPIXEL, debug=False)
print('Network')

# --- Drawing setup ---
group = displayio.Group()
bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, 'rb'))
colors = [0xFFFFFF, 0xFFFF00]  # [white, yellow]

font = bitmap_font.load_font("fonts/6x10.bdf")
text_lines = [
    displayio.TileGrid(bitmap, pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter())),
    # Keep text at 7 chars or under otherwise it will overflow the display
    adafruit_display_text.label.Label(font, color=colors[0], x=20, y=3, text="Queens"),
    adafruit_display_text.label.Label(font, color=colors[1], x=20, y=11, text="- mins"),
    adafruit_display_text.label.Label(font, color=colors[0], x=20, y=20, text="Manhat"),
    adafruit_display_text.label.Label(font, color=colors[1], x=20, y=28, text="- mins"),
]
for x in text_lines:
    group.append(x)
display.root_group = group

def setup_requests():
    pool = adafruit_connection_manager.get_radio_socketpool(network._wifi.esp)
    ssl_ctx = adafruit_connection_manager.get_radio_ssl_context(network._wifi.esp)
    return adafruit_requests.Session(pool, ssl_ctx)

# Force WiFi connection before main loop
try:
    fw = network._wifi.esp.firmware_version
    print("ESP32 firmware:", fw)
except Exception as e:
    print("Could not get firmware:", e)
import os
wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
if not wifi_ssid:
    raise Exception("No WiFi SSID found, did you create a settings.toml file?")

print("Connecting to WiFi SSID: %s" % (wifi_ssid,))
network.connect()
print("WiFi connected!")
time.sleep(3)
print("Getting time...")
network.get_local_time()
print("Connected! Letting ESP32 stabilize...")
time.sleep(3)

# Test fetch to confirm connectivity
print("Testing API connection...")
try:
    test = network.fetch_data("https://httpbin.org/get", json_path=(['url'],))
    print("Test fetch worked:", test)
except Exception as e:
    print("Test fetch failed:", e)

error_counter = 0
last_time_sync = time.monotonic()
while True:
    try:
        print("Syncing clock")
        if last_time_sync is None or time.monotonic() > last_time_sync + SYNC_TIME_DELAY:
            # Sync clock to minimize time drift
            network.get_local_time()
            last_time_sync = time.monotonic()
        arrivals = get_arrival_times()
        update_text(*arrivals)
        error_counter = 0  # Reset on success
    except (ValueError, RuntimeError, BrokenPipeError, OSError) as e:
        print("Error:", type(e).__name__, e)
        error_counter = error_counter + 1
        # Close all sockets and reset ESP32 to recover
        adafruit_connection_manager.connection_manager_close_all()
        print("Resetting ESP32, error count:", error_counter)
        network._wifi.esp.reset()
        time.sleep(2)
        network.connect()
        if error_counter > ERROR_RESET_THRESHOLD:
            print("Too many errors, full reset...")
            time.sleep(1)
            microcontroller.reset()

    print("Sleeping for %s seconds" % (UPDATE_DELAY,))
    time.sleep(UPDATE_DELAY)
