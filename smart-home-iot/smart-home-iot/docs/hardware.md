# Hardware and wiring

| Part | Qty | Notes |
|---|---|---|
| Raspberry Pi 3/4/Zero 2 W | 1 | Raspberry Pi OS, on your home network |
| ESP32 dev board | 1 | WiFi node |
| Arduino Uno or Nano | 1 | Wired to the Pi by USB |
| DHT22 (or DHT11) | 1 | Change `DHT_TYPE` in the sketch for DHT11 |
| HC-SR501 PIR sensor | 1 | |
| 2-channel 5 V relay module | 1 | Light and fan. Use a lamp/fan you can safely isolate |
| SG90 servo | 1 | Door lock demo |
| LED + 220 Ω resistor | 1 | Stands in for the hallway light |

> **Mains safety:** for a class demo, switch low-voltage loads (LED strip, USB fan) through the
> relays instead of 230 V/120 V appliances.

## ESP32 (living room)

| ESP32 pin | Connects to |
|---|---|
| GPIO4 | DHT22 data (10 kΩ pull-up to 3V3) |
| GPIO26 | Relay IN1 (light) |
| GPIO27 | Relay IN2 (fan) |
| 3V3 / 5V / GND | DHT22 3V3, relay VCC (5 V), common GND |

## Arduino (hallway)

| Arduino pin | Connects to |
|---|---|
| D2 | PIR OUT |
| D8 | LED anode through 220 Ω (or relay IN) |
| D9 | Servo signal (power the servo from 5 V and GND; use a separate supply if it jitters) |
| 5V / GND | PIR VCC, servo, common GND |

## Flashing

- **ESP32:** Arduino IDE, board "ESP32 Dev Module"; install `PubSubClient` and `DHT sensor library`;
  copy `secrets.h.example` to `secrets.h`; upload.
- **Arduino:** install the `Servo` library (bundled); upload `arduino_hall_node.ino`; then plug it into the Pi.
  Find the port with `ls /dev/ttyACM*` and set `SERIAL_PORT` in `.env`. You may need
  `sudo usermod -aG dialout $USER` and a re-login.
