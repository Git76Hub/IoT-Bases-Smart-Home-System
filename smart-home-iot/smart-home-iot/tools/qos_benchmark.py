"""Compare MQTT QoS 0 / 1 / 2: delivery ratio, latency and duration.

    python -m tools.qos_benchmark --n 200 --rate 50

Run it once on a clean network, then again with packet loss added on the Pi
(see docs/experiments.md) to see where QoS 0 starts losing messages.
"""
import argparse
import statistics
import threading
import time

from smarthome import mqtt_util

TOPIC = "bench/qos"


def run(qos: int, n: int, rate: float, settle: float):
    received: dict[int, float] = {}
    ready = threading.Event()
    sub = mqtt_util.make_client(f"bench-sub-{qos}")
    pub = mqtt_util.make_client(f"bench-pub-{qos}")

    def on_connect(c, u, f, rc, p):
        c.subscribe(TOPIC, qos)
        ready.set()

    def on_message(c, u, msg):
        seq, sent = msg.payload.decode().split(":")
        received[int(seq)] = (time.time() - float(sent)) * 1000

    sub.on_connect, sub.on_message = on_connect, on_message
    mqtt_util.start(sub)
    mqtt_util.start(pub)
    if not ready.wait(10):
        raise SystemExit("Could not connect to the broker.")
    time.sleep(0.5)

    start = time.time()
    for i in range(n):
        pub.publish(TOPIC, f"{i}:{time.time()}", qos=qos)
        time.sleep(1 / rate)
    deadline = time.time() + settle
    while len(received) < n and time.time() < deadline:
        time.sleep(0.05)
    elapsed = time.time() - start
    for c in (sub, pub):
        c.loop_stop()
        c.disconnect()
    return received, elapsed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="messages per QoS level")
    ap.add_argument("--rate", type=float, default=50, help="messages per second")
    ap.add_argument("--settle", type=float, default=5, help="seconds to wait for stragglers")
    args = ap.parse_args()

    print(f"{'QoS':<4}{'sent':>6}{'got':>6}{'loss %':>8}{'mean ms':>9}{'p95 ms':>9}{'time s':>8}")
    for qos in (0, 1, 2):
        got, elapsed = run(qos, args.n, args.rate, args.settle)
        lat = sorted(got.values())
        mean = statistics.mean(lat) if lat else float("nan")
        p95 = lat[min(len(lat) - 1, int(len(lat) * 0.95))] if lat else float("nan")
        loss = 100 * (args.n - len(got)) / args.n
        print(f"{qos:<4}{args.n:>6}{len(got):>6}{loss:>8.1f}{mean:>9.1f}{p95:>9.1f}{elapsed:>8.1f}")


if __name__ == "__main__":
    main()
