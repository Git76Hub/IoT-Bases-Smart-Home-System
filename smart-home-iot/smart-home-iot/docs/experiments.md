# Network experiments

Run these for the networking part of the report. Each one lists what to capture.

All commands assume the repo root, a running broker and a populated `.env`.
Use `python3 -m ...` (or the virtualenv's python).

## 1. Watch MQTT in Wireshark

On the Pi: `sudo tcpdump -i wlan0 -w mqtt.pcap port 1883` (stop with Ctrl+C), then open
`mqtt.pcap` in Wireshark on your laptop. Display filter: `mqtt`.

Screenshot and explain: `Connect Command` / `Connect Ack`, `Subscribe Request`, `Publish Message`
(topic, QoS, retain flag), `Ping Request/Response` (keep-alive), and the `Will` fields in a CONNECT.
In plain MQTT you can read the username, password and every payload.

## 2. QoS comparison

```bash
python3 -m tools.qos_benchmark --n 200 --rate 50
```
Record the table. QoS 0 = at most once, QoS 1 = at least once (PUBACK), QoS 2 = exactly once
(four-packet handshake). Expect latency and duration to rise with QoS. Capture one message at each
level in Wireshark and count the packets.

## 3. Behaviour under bad network conditions

Add delay and loss on the Pi's interface (replace `wlan0` if needed), rerun the benchmark, then remove it:

```bash
sudo tc qdisc add dev wlan0 root netem delay 100ms 20ms loss 5%
python3 -m tools.qos_benchmark --n 200 --rate 20
sudo tc qdisc del dev wlan0 root
```
Note: loss on a TCP link shows up as retransmission delay, not as missing messages, so QoS 0 mostly
loses messages when the *connection* drops. Try it too: `sudo systemctl stop mosquitto`, publish at
QoS 0 and QoS 1 from a client with a queue, restart, and compare what arrives.

## 4. Command latency (click to relay)

```bash
python3 -m tools.latency_test --n 50 --qos 1
```
Run against the simulator, then against the ESP32 over WiFi, and compare. Include min / mean / p95.

## 5. MQTT vs HTTP overhead

```bash
python3 -m tools.overhead_calc
```
Then verify with a capture: send one reading with `mosquitto_pub` and one with `curl -X POST`
and compare the application-layer bytes in Wireshark (Statistics > Conversations).

## 6. Resilience: Last Will, retained messages, reconnection

- Unplug the ESP32. The dashboard should show `esp32-living: offline` after the keep-alive expires
  (about 1.5 x the keep-alive; PubSubClient defaults to 15 s).
- Reopen the dashboard: the lights and lock show their state at once (retained messages).
- Restart `mosquitto`: clients should reconnect on their own (see `reconnect_delay_set`).

## 7. Security

1. Plain `mosquitto_sub` without credentials is refused (`allow_anonymous false`).
2. The `node` user cannot command devices: `mosquitto_pub -u node -P ... -t home/livingroom/fan/set -m ON` is silently dropped by the ACL.
3. TLS: run `tools/gen_certs.sh <pi-ip>`, enable the 8883 listener, set `MQTT_PORT=8883` and `MQTT_CA=certs/ca.crt`.
   Capture again and show that payloads are now unreadable.
4. Remote access: use WireGuard or Tailscale instead of port-forwarding. Never expose 1883 to the internet.

## Results template

| Experiment | Setup | Result | Observation |
|---|---|---|---|
| QoS 0/1/2 | clean LAN | | |
| QoS 0/1/2 | 100 ms + 5 % loss | | |
| Command latency | simulator vs ESP32 | | |
| MQTT vs HTTP bytes | one sensor update | | |
