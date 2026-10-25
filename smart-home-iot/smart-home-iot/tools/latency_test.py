"""Measure command -> acknowledgement latency (works with real devices or the simulator).

    python -m tools.latency_test --n 50 --qos 1

Toggles the living-room light and times how long until the device reports the new state.
"""
import argparse
import statistics
import threading
import time

from smarthome import mqtt_util, topics


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="number of round trips")
    ap.add_argument("--qos", type=int, choices=(0, 1, 2), default=1)
    ap.add_argument("--timeout", type=float, default=5.0)
    args = ap.parse_args()

    client = mqtt_util.make_client("latency-test")
    ack, expected, ready = threading.Event(), {"v": None}, threading.Event()

    def on_connect(c, u, f, rc, p):
        c.subscribe(topics.LIGHT_STATE, args.qos)
        ready.set()

    def on_message(c, u, msg):
        if msg.payload.decode() == expected["v"]:
            ack.set()

    client.on_connect, client.on_message = on_connect, on_message
    mqtt_util.start(client)
    if not ready.wait(10):
        raise SystemExit("Could not connect to the broker.")

    samples, lost, value = [], 0, "ON"
    for _ in range(args.n):
        expected["v"] = value
        ack.clear()
        start = time.perf_counter()
        client.publish(topics.LIGHT_SET, value, qos=args.qos)
        if ack.wait(args.timeout):
            samples.append((time.perf_counter() - start) * 1000)
        else:
            lost += 1
        value = "OFF" if value == "ON" else "ON"
        time.sleep(0.2)
    client.loop_stop()

    if not samples:
        raise SystemExit("No acknowledgements received. Is a device or the simulator running?")
    samples.sort()
    p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
    print(f"QoS {args.qos}: n={len(samples)} lost={lost}  min={samples[0]:.1f} ms  "
          f"mean={statistics.mean(samples):.1f} ms  p95={p95:.1f} ms  max={samples[-1]:.1f} ms")


if __name__ == "__main__":
    main()
