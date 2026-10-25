"""Automation rules + data logger. Runs on the Raspberry Pi.

    python -m smarthome.automation

Rules (active while auto mode is ON):
  * Living-room temperature >= FAN_ON_TEMP        -> fan ON
  * Temperature <= FAN_ON_TEMP - FAN_HYSTERESIS   -> fan OFF
  * Motion in the hallway                          -> hallway light ON,
    switched OFF again after LIGHT_OFF_DELAY seconds without motion.
"""
import logging
import threading
import time

from . import config, db, mqtt_util, topics

log = logging.getLogger("automation")

Action = tuple[str, str, bool]  # (topic, payload, retain)


class RuleEngine:
    """Pure logic, no I/O: feed it messages, it returns the commands to publish."""

    def __init__(self, fan_on: float, hysteresis: float, light_delay: float):
        self.fan_on = fan_on
        self.hysteresis = hysteresis
        self.light_delay = light_delay
        self.auto = True
        self.fan = "OFF"
        self.hall_light = "OFF"
        self.light_by_rule = False
        self.last_motion: float | None = None

    def handle(self, topic: str, payload: str, now: float) -> list[Action]:
        actions: list[Action] = []
        if topic == topics.AUTO_SET:
            self.auto = payload.upper() == "ON"
            actions.append((topics.AUTO_STATE, "ON" if self.auto else "OFF", True))
        elif topic == topics.AUTO_STATE:  # restores mode after a restart
            self.auto = payload.upper() == "ON"
        elif topic == topics.FAN_STATE:
            self.fan = payload
        elif topic == topics.HALL_LIGHT_STATE:
            self.hall_light = payload
            if payload == "OFF":
                self.light_by_rule = False
        elif topic == topics.TEMP and self.auto:
            try:
                temp = float(payload)
            except ValueError:
                return actions
            if temp >= self.fan_on and self.fan != "ON":
                actions.append((topics.FAN_SET, "ON", False))
            elif temp <= self.fan_on - self.hysteresis and self.fan != "OFF":
                actions.append((topics.FAN_SET, "OFF", False))
        elif topic == topics.MOTION and payload == "1":
            self.last_motion = now
            if self.auto and self.hall_light != "ON":
                self.light_by_rule = True
                actions.append((topics.HALL_LIGHT_SET, "ON", False))
        return actions

    def tick(self, now: float) -> list[Action]:
        """Called about once per second to handle timers."""
        if (
            self.auto
            and self.light_by_rule
            and self.last_motion is not None
            and now - self.last_motion >= self.light_delay
        ):
            self.light_by_rule = False
            return [(topics.HALL_LIGHT_SET, "OFF", False)]
        return []


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    conn = db.connect()
    db.prune(conn)
    engine = RuleEngine(config.FAN_ON_TEMP, config.FAN_HYSTERESIS, config.LIGHT_OFF_DELAY)
    lock = threading.Lock()
    client = mqtt_util.make_client("smarthome-automation")

    def publish(actions: list[Action]) -> None:
        for topic, payload, retain in actions:
            log.info("rule -> %s = %s", topic, payload)
            client.publish(topic, payload, qos=1, retain=retain)

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("MQTT connect failed: %s", reason_code)
            return
        log.info("connected to broker")
        c.subscribe([("home/+/+/state", 1), (topics.AUTO_SET, 1)])

    def on_message(c, userdata, msg):
        payload = msg.payload.decode(errors="replace")
        if msg.topic.endswith("/state") and not msg.retain:  # skip replayed retained values
            db.log_message(conn, msg.topic, payload)
        with lock:
            actions = engine.handle(msg.topic, payload, time.time())
        publish(actions)

    def ticker() -> None:
        while True:
            time.sleep(1)
            with lock:
                actions = engine.tick(time.time())
            publish(actions)

    client.on_connect = on_connect
    client.on_message = on_message
    threading.Thread(target=ticker, daemon=True).start()
    mqtt_util.start(client)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
