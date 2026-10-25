"""Compare on-the-wire size of one sensor update sent via MQTT vs. HTTP.

    python -m tools.overhead_calc

Application-layer bytes only (TCP/IP headers are identical for both). Validate the
numbers against a Wireshark capture (see docs/experiments.md).
"""
import json


def mqtt_publish_qos0(topic: str, payload: str) -> int:
    remaining = 2 + len(topic) + len(payload)          # topic length prefix + topic + payload
    length_bytes = 1 if remaining < 128 else 2
    return 1 + length_bytes + remaining                # fixed header + remaining length + body


def http_post(path: str, body: str) -> tuple[int, int]:
    request = (
        f"POST {path} HTTP/1.1\r\nHost: 192.168.1.50:5000\r\nUser-Agent: python-requests/2.32\r\n"
        "Accept: */*\r\nContent-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n\r\n{body}"
    )
    response = "HTTP/1.1 200 OK\r\nServer: waitress\r\nContent-Type: application/json\r\nContent-Length: 12\r\n\r\n{\"ok\": true}\n"
    return len(request.encode()), len(response.encode())


def main() -> None:
    topic, value = "home/livingroom/temperature/state", "24.5"
    mqtt_bytes = mqtt_publish_qos0(topic, value)
    mqtt_ack = 4  # PUBACK for QoS 1
    req, resp = http_post("/api/sensors", json.dumps({"topic": topic, "value": value}))
    print(f"Payload itself             : {len(value)} bytes")
    print(f"MQTT PUBLISH (QoS 0)       : {mqtt_bytes} bytes")
    print(f"MQTT PUBLISH + PUBACK (QoS1): {mqtt_bytes + mqtt_ack} bytes")
    print(f"HTTP POST request+response : {req + resp} bytes ({req} + {resp})")
    print(f"HTTP / MQTT(QoS 0) ratio   : {(req + resp) / mqtt_bytes:.1f}x")
    print("Note: MQTT also pays one CONNECT/CONNACK once per session; HTTP/1.1 keep-alive reduces, but does not remove, per-request headers.")


if __name__ == "__main__":
    main()
