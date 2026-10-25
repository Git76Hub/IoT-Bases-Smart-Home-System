"""Central configuration, read from environment variables (or a .env file)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

# --- MQTT broker ---
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
MQTT_CA = os.getenv("MQTT_CA", "")  # path to CA certificate enables TLS

# --- Storage ---
DB_PATH = Path(os.getenv("DB_PATH", "data/smarthome.db"))

# --- Serial bridge ---
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyACM0")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "9600"))

# --- Automation rules ---
FAN_ON_TEMP = float(os.getenv("FAN_ON_TEMP", "28"))
FAN_HYSTERESIS = float(os.getenv("FAN_HYSTERESIS", "1.5"))
LIGHT_OFF_DELAY = float(os.getenv("LIGHT_OFF_DELAY", "30"))

# --- Dashboard ---
DASH_HOST = os.getenv("DASH_HOST", "0.0.0.0")
DASH_PORT = int(os.getenv("DASH_PORT", "5000"))
DASH_USER = os.getenv("DASH_USER", "")
DASH_PASS = os.getenv("DASH_PASS", "")
