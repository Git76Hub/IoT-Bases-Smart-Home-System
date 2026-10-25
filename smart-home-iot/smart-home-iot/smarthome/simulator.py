"""Virtual devices so the whole system can be demonstrated without hardware.

    python -m smarthome.simulator

Behaves like the ESP32 living-room node and the Arduino hallway node: publishes
sensor values, obeys commands, reports state and sets Last Will messages.
The temperature rises on its own and drops while the fan is on, so the
automation rule is easy to watch.
"""
import logging
import random
import time

from . import mqtt_util, topics

log = logging.getLogger("simulator")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    st = {"light": "OFF", "fan": "OFF", "hall": "OFF", "lock": "LOCKED"}

    esp = mqtt_util.make_client("sim-esp32", will_topic=topics.status("sim-esp32"))
    ard = mqtt_util.make_client("sim-arduino", will_topic=topics.status("sim-arduino"))

    def esp_connect(c, u, flags, rc, p):
        c.subscribe([(topics.LIGHT_SET, 1), (topics.FAN_SET, 1)])
        c.publish(topics.status("sim-esp32"), "online", qos=1, retain=True)
        c.publish(topics.LIGHT_STATE, st["light"], qos=1, retain=True)
        c.publish(topics.FAN_STATE, st["fan"], qos=1, retain=True)

    def esp_message(c, u, msg):
        value = msg.payload.decode(errors="replace").strip().upper()
        if value not in ("ON", "OFF"):
            return
        key, topic = ("light", topics.LIGHT_STATE) if msg.topic == topics.LIGHT_SET else ("fan", topics.FAN_STATE)
        st[key] = value
        c.publish(topic, value, qos=1, retain=True)
        log.info("living room %s -> %s", key, value)

    def ard_connect(c, u, flags, rc, p):
        c.subscribe([(topics.HALL_LIGHT_SET, 1), (topics.DOOR_LOCK_SET, 1)])
        c.publish(topics.status("sim-arduino"), "online", qos=1, retain=True)
        c.publish(topics.HALL_LIGHT_STATE, st["hall"], qos=1, retain=True)
        c.publish(topics.DOOR_LOCK_STATE, st["lock"], qos=1, retain=True)

    def ard_message(c, u, msg):
        value = msg.payload.decode(errors="replace").strip().upper()
        if msg.topic == topics.HALL_LIGHT_SET and value in ("ON", "OFF"):
            st["hall"] = value
            c.publish(topics.HALL_LIGHT_STATE, value, qos=1, retain=True)
        elif msg.topic == topics.DOOR_LOCK_SET and value in ("LOCK", "UNLOCK"):
            st["lock"] = "LOCKED" if value == "LOCK" else "UNLOCKED"
            c.publish(topics.DOOR_LOCK_STATE, st["lock"], qos=1, retain=True)
        log.info("hallway/door state: %s", st)

    esp.on_connect, esp.on_message = esp_connect, esp_message
    ard.on_connect, ard.on_message = ard_connect, ard_message
    mqtt_util.start(esp)
    mqtt_util.start(ard)

    temp, moving = 26.0, False
    try:
        while True:
            time.sleep(2)
            temp += -0.4 if st["fan"] == "ON" else 0.2
            temp = min(max(temp + random.uniform(-0.05, 0.05), 22.0), 34.0)
            hum = 55 + random.uniform(-3, 3)
            esp.publish(topics.TEMP, f"{temp:.1f}", qos=1)
            esp.publish(topics.HUM, f"{hum:.0f}", qos=1)
            if not moving and random.random() < 0.1:
                moving = True
                ard.publish(topics.MOTION, "1", qos=1)
            elif moving and random.random() < 0.5:
                moving = False
                ard.publish(topics.MOTION, "0", qos=1)
    except KeyboardInterrupt:
        pass
    finally:
        for c in (esp, ard):
            c.loop_stop()
            c.disconnect()


if __name__ == "__main__":
    main()
