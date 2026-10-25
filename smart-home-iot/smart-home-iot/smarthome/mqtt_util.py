"""Shared helpers for creating configured paho-mqtt clients."""
import paho.mqtt.client as mqtt

from . import config


def make_client(client_id: str, will_topic: str | None = None) -> mqtt.Client:
    """Create a client with credentials, optional TLS and an offline Last Will."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    if config.MQTT_USER:
        client.username_pw_set(config.MQTT_USER, config.MQTT_PASS)
    if config.MQTT_CA:
        client.tls_set(ca_certs=config.MQTT_CA)
    if will_topic:
        client.will_set(will_topic, "offline", qos=1, retain=True)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    return client


def start(client: mqtt.Client) -> None:
    """Connect in the background; paho keeps retrying if the broker is down."""
    client.connect_async(config.MQTT_HOST, config.MQTT_PORT, keepalive=30)
    client.loop_start()
