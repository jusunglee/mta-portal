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
import rtc
import os
import gc

STOP_ID = 'F20'
DATA_SOURCE = 'https://api.wheresthefuckingtrain.com/by-id/%s' % (STOP_ID,)
DATA_LOCATION = ["data"]
TIME_API = 'http://worldtimeapi.org/api/timezone/America/New_York'
UPDATE_DELAY = 15 # seconds
SYNC_TIME_DELAY = 30 # seconds
METRICS_DELAY = 60 # seconds
MINIMUM_MINUTES_DISPLAY = 3 # minutes
ERROR_RESET_THRESHOLD = 3

# InfluxDB metrics configuration, through settings.toml
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
DEVICE_HOST = os.getenv("DEVICE_HOST", "matrix-portal")

# Loki logging configuration
LOKI_URL = os.getenv("LOKI_URL", "")

# UTC offset in seconds (updated by sync_time)
utc_offset_seconds = 0

# Route icon configuration: letter, fill color, y-center position
ROUTES = [
    {"letter": "G", "color": 0x6CBE45, "y": 7},   # Green line
    {"letter": "F", "color": 0xFF6319, "y": 23},  # Orange line
]
ICON_SIZE = 15

def sync_time():
    """Sync RTC using WorldTimeAPI - auto-handles DST."""
    global utc_offset_seconds
    print("Getting time from WorldTimeAPI")
    response = network.fetch_data(TIME_API, json_path=(["datetime"],))
    dt_str = response if isinstance(response, str) else response[0]
    # Response format: "2026-01-23T15:23:10.123456-05:00"
    # Extract UTC offset from the datetime string (last 6 chars like "-05:00")
    utc_offset_str = dt_str[-6:]
    dt_str = dt_str[:19]  # Trim to "2026-01-23T15:23:10"
    dt = datetime.fromisoformat(dt_str)
    rtc.RTC().datetime = dt.timetuple()
    # Parse UTC offset like "-05:00" or "+02:00"
    sign = -1 if utc_offset_str[0] == '-' else 1
    hours = int(utc_offset_str[1:3])
    minutes = int(utc_offset_str[4:6])
    utc_offset_seconds = sign * (hours * 3600 + minutes * 60)

def create_circle_bitmap(size, color):
    """Create a filled circle bitmap."""
    bitmap = displayio.Bitmap(size, size, 2)
    palette = displayio.Palette(2)
    palette[0] = 0x000000  # Background (black)
    palette[1] = color
    palette.make_transparent(0)

    center = size // 2
    radius = center - 0.5
    for y in range(size):
        for x in range(size):
            dist = (x - center) ** 2 + (y - center) ** 2
            if dist < radius ** 2:
                bitmap[x, y] = 1
    return displayio.TileGrid(bitmap, pixel_shader=palette)

def get_arrival_in_minutes_from_now(now, date_str):
    train_date = datetime.fromisoformat(date_str).replace(tzinfo=None) # Remove tzinfo to be able to diff dates
    return round((train_date-now).total_seconds()/60.0)

def get_arrival_times():
    stop_trains = network.fetch_data(DATA_SOURCE, json_path=(DATA_LOCATION,))
    stop_data = stop_trains[0]

    # Filter northbound trains by route
    g_trains = [x['time'] for x in stop_data['N'] if x['route'] == 'G']
    f_trains = [x['time'] for x in stop_data['N'] if x['route'] == 'F']

    now = datetime.now()

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
    text_lines[0].text = "%s,%s m" % (g0, g1)
    text_lines[1].text = "%s,%s m" % (f0, f1)
    display.root_group = group

# --- Display setup ---
matrix = Matrix(bit_depth=4)
display = matrix.display
network = Network(status_neopixel=NEOPIXEL, debug=False)

# --- Drawing setup ---
group = displayio.Group()
font = bitmap_font.load_font("fonts/6x10.bdf")
# Pre-cache all glyphs we'll use to avoid runtime memory allocation
font.load_glyphs("0123456789-,. mGFQueensManhtn")

# Create route icons and labels
for route in ROUTES:
    # Filled circle
    circle = create_circle_bitmap(ICON_SIZE, route["color"])
    circle.x = 1
    circle.y = route["y"] - ICON_SIZE // 2
    group.append(circle)

    # Letter on top (black, hollow effect) - draw multiple times for bold
    for offset_x, offset_y in [(0, 0), (1, 0)]:
        letter_label = adafruit_display_text.label.Label(
            font, color=0x000000, x=6 + offset_x, y=route["y"] + offset_y, text=route["letter"]
        )
        group.append(letter_label)

# Direction labels and arrival time labels
group.append(adafruit_display_text.label.Label(font, color=0xFFFFFF, x=18, y=3, text="Queens"))
group.append(adafruit_display_text.label.Label(font, color=0xFFFFFF, x=18, y=19, text="Manhtn"))

text_lines = [
    adafruit_display_text.label.Label(font, color=0xFFFF00, x=18, y=11, text="..."),   # G times
    adafruit_display_text.label.Label(font, color=0xFFFF00, x=18, y=27, text="..."),   # F times
]
for label in text_lines:
    group.append(label)
display.root_group = group

def setup_requests():
    pool = adafruit_connection_manager.get_radio_socketpool(network._wifi.esp)
    ssl_ctx = adafruit_connection_manager.get_radio_ssl_context(network._wifi.esp)
    return adafruit_requests.Session(pool, ssl_ctx)

def send_metrics(requests_session, uptime_seconds, error_count):
    """Send health metrics to InfluxDB"""
    if not INFLUX_URL or not INFLUX_TOKEN:
        return
    try:
        # Build fields
        fields = f"uptime={uptime_seconds}i,errors={error_count}i"
        fields += f",mem_free={gc.mem_free()}i,mem_alloc={gc.mem_alloc()}i"
        try:
            ap_info = network._wifi.esp.ap_info
            # ap_info can be a tuple (ssid, bssid, rssi, ...) or a Network object with .rssi attribute
            if hasattr(ap_info, 'rssi'):
                fields += f",wifi_rssi={ap_info.rssi}i"
            elif isinstance(ap_info, (tuple, list)) and len(ap_info) > 2:
                fields += f",wifi_rssi={ap_info[2]}i"
        except (AttributeError, IndexError, TypeError):
            pass  # RSSI not available, skip it

        line = f"matrix_portal,host={DEVICE_HOST} {fields}"
        headers = {
            "Authorization": f"Token {INFLUX_TOKEN}",
            "Content-Type": "text/plain"
        }
        url = f"{INFLUX_URL}/api/v2/write?org={INFLUX_ORG}&bucket={INFLUX_BUCKET}"
        print(f"Sending: {line}")
        response = requests_session.post(url, data=line, headers=headers)
        print(f"Metrics: {response.status_code}")
        response.close()  # Free socket resources
    except Exception as e:
        print(f"Metrics send failed: {e}")

def send_log(requests_session, level, message):
    """Send log entry to Loki"""
    if not LOKI_URL:
        return
    try:
        # Convert local time to UTC by subtracting the offset
        utc_time = time.time() - utc_offset_seconds
        timestamp_ns = str(int(utc_time * 1_000_000_000))
        # Build minimal JSON payload manually to save memory
        msg = message.replace('\\', '\\\\').replace('"', '\\"')
        payload = '{"streams":[{"stream":{"job":"matrix-portal","host":"' + DEVICE_HOST + '","level":"' + level + '"},"values":[["' + timestamp_ns + '","' + msg + '"]]}]}'
        response = requests_session.post(
            LOKI_URL + "/loki/api/v1/push",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        response.close()  # Free socket resources immediately
    except Exception as e:
        print(f"Log send failed: {e}")

# Force WiFi connection before main loop
try:
    fw = network._wifi.esp.firmware_version
    print("ESP32 firmware:", fw)
except Exception as e:
    print("Could not get firmware:", e)

wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
if not wifi_ssid:
    raise Exception("No WiFi SSID found, did you create a settings.toml file?")

print("Connecting to WiFi SSID: %s" % (wifi_ssid,))
network.connect()
print("WiFi connected!")
time.sleep(3)

print("Getting time...")
for attempt in range(3):
    try:
        sync_time()
        print("Time synced!")
        break
    except (ConnectionError, OSError, RuntimeError, adafruit_requests.OutOfRetries) as e:
        print("Time sync failed (attempt %d): %s" % (attempt + 1, e))
        time.sleep(2)
else:
    print("Warning: Could not sync time, continuing anyway")
time.sleep(1)

error_counter = 0
last_time_sync = time.monotonic()
last_metrics_send = 0
start_time = time.monotonic()
requests_session = setup_requests()
send_log(requests_session, "info", "Device started")

while True:
    try:
        print("Syncing clock")
        if last_time_sync is None or time.monotonic() > last_time_sync + SYNC_TIME_DELAY:
            # Sync clock to minimize time drift
            sync_time()
            last_time_sync = time.monotonic()
            send_log(requests_session, "info", "Time synced")
        arrivals = get_arrival_times()
        update_text(*arrivals)
        send_log(requests_session, "info", "Arrivals updated, g0: %s, g1: %s, f0: %s, f1: %s" % (arrivals[0], arrivals[1], arrivals[2], arrivals[3]))
        error_counter = 0  # Reset on success

        # Send metrics periodically
        if time.monotonic() > last_metrics_send + METRICS_DELAY:
            uptime = int(time.monotonic() - start_time)
            send_metrics(requests_session, uptime, error_counter)
            last_metrics_send = time.monotonic()
    except (ValueError, RuntimeError, BrokenPipeError, OSError, ConnectionError, adafruit_requests.OutOfRetries) as e:
        error_msg = f"{type(e).__name__}: {e}"
        print("Error:", error_msg)
        send_log(requests_session, "error", error_msg)
        error_counter = error_counter + 1
        # Close all sockets and reset ESP32 to recover
        adafruit_connection_manager.connection_manager_close_all()
        print("Resetting ESP32, error count:", error_counter)
        network._wifi.esp.reset()
        time.sleep(2)
        network.connect()
        requests_session = setup_requests()
        send_log(requests_session, "info", f"Recovered from error, count: {error_counter}")
        if error_counter > ERROR_RESET_THRESHOLD:
            print("Too many errors, full reset...")
            time.sleep(1)
            microcontroller.reset()

    print("Sleeping for %s seconds" % (UPDATE_DELAY,))
    time.sleep(UPDATE_DELAY)
