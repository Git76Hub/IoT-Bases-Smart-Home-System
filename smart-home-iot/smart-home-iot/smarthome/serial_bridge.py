"""Bridge between a USB-connected Arduino and MQTT.

    python -m smarthome.serial_bridge

Serial protocol (text lines, both directions):  key:value\\n
  Arduino -> Pi : motion:0|1   light:ON|OFF   lock:LOCKED|UNLOCKED
  Pi -> Arduino : light:ON|OFF   lock:LOCK|UNLOCK   sync:1 (resend all states)
"""
import logging
import time

import serial

from . import config, mqtt_util, topics

log = logging.getLogger("serial-bridge")

DEVICE_ID = "arduino-hall"
UP = {  # serial key -> (mqtt topic, allowed values, retain)
    "motion": (topics.MOTION, {"0", "1"}, False),
    "light": (topics.HALL_LIGHT_STATE, {"ON", "OFF"}, True),
    "lock": (topics.DOOR_LOCK_STATE, {"LOCKED", "UNLOCKED"}, True),
}
DOWN = {  # mqtt command topic -> (serial key, allowed values)
    topics.HALL_LIGHT_SET: ("light", {"ON", "OFF"}),
    topics.DOOR_LOCK_SET: ("lock", {"LOCK", "UNLOCK"}),
}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    status_topic = topics.status(DEVICE_ID)
    client = mqtt_util.make_client("smarthome-serial-bridge", will_topic=status_topic)
    port: serial.Serial | None = None

    def publish_status() -> None:
        client.publish(status_topic, "online" if port else "offline", qos=1, retain=True)

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("MQTT connect failed: %s", reason_code)
            return
        c.subscribe([(t, 1) for t in DOWN])
        publish_status()

    def on_message(c, userdata, msg):
        key, allowed = DOWN[msg.topic]
        value = msg.payload.decode(errors="replace").strip().upper()
        if value not in allowed or port is None:
            return
        try:
            port.write(f"{key}:{value}\n".encode())
        except serial.SerialException:
            log.warning("serial write failed")

    client.on_connect = on_connect
    client.on_message = on_message
    mqtt_util.start(client)

    while True:
        try:
            port = serial.Serial(config.SERIAL_PORT, config.SERIAL_BAUD, timeout=1)
            time.sleep(2)  # the Arduino resets when the port opens
            port.write(b"sync:1\n")
            log.info("serial connected on %s", config.SERIAL_PORT)
            publish_status()
            while True:
                line = port.readline().decode(errors="ignore").strip()
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                if key in UP and value in UP[key][1]:
                    topic, _, retain = UP[key]
                    client.publish(topic, value, qos=1, retain=retain)
        except (serial.SerialException, OSError) as exc:
            log.warning("serial problem (%s); retrying in 5 s", exc)
            port = None
            publish_status()
            time.sleep(5)


if __name__ == "__main__":
    main()
