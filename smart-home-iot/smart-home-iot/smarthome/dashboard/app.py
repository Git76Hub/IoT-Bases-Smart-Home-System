"""Web dashboard: live state, controls and history charts.

    python -m smarthome.dashboard.app      ->  http://<pi-address>:5000

The browser only talks HTTP to this server; the server talks MQTT to the broker,
so broker credentials never reach the browser.
"""
import hmac
import logging
import time

from flask import Flask, Response, jsonify, render_template, request
from waitress import serve

from .. import config, db, mqtt_util, topics

log = logging.getLogger("dashboard")
app = Flask(__name__)

state: dict[str, str] = {}      # "room/device" -> latest payload
updated: dict[str, float] = {}  # "room/device" -> unix time of last update
devices: dict[str, str] = {}    # device id -> "online" | "offline"
broker = {"connected": False}

# Whitelist of what the browser may command: target -> allowed values
CONTROLS = {
    "livingroom/light": {"ON", "OFF"},
    "livingroom/fan": {"ON", "OFF"},
    "hallway/light": {"ON", "OFF"},
    "frontdoor/lock": {"LOCK", "UNLOCK"},
    "system/auto": {"ON", "OFF"},
}
HISTORY = {"temperature": topics.TEMP, "humidity": topics.HUM}

client = mqtt_util.make_client("smarthome-dashboard")


def on_connect(c, userdata, flags, reason_code, properties):
    broker["connected"] = not reason_code.is_failure
    if broker["connected"]:
        c.subscribe("home/#", 1)


def on_disconnect(c, userdata, flags, reason_code, properties):
    broker["connected"] = False


def on_message(c, userdata, msg):
    parts = msg.topic.split("/")
    if len(parts) != 4 or parts[0] != "home":
        return
    payload = msg.payload.decode(errors="replace")
    if parts[1] == "devices" and parts[3] == "status":
        devices[parts[2]] = payload
    elif parts[3] == "state":
        key = f"{parts[1]}/{parts[2]}"
        state[key] = payload
        updated[key] = time.time()


client.on_connect, client.on_disconnect, client.on_message = on_connect, on_disconnect, on_message


@app.before_request
def require_login():
    if not config.DASH_USER:
        return None
    auth = request.authorization
    if (
        auth
        and hmac.compare_digest(auth.username or "", config.DASH_USER)
        and hmac.compare_digest(auth.password or "", config.DASH_PASS)
    ):
        return None
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Smart Home"'})


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def api_state():
    return jsonify(state=state, updated=updated, devices=devices, broker=broker["connected"], now=time.time())


@app.post("/api/command")
def api_command():
    data = request.get_json(silent=True) or {}
    target, value = data.get("target"), str(data.get("value", "")).upper()
    if target not in CONTROLS or value not in CONTROLS[target]:
        return jsonify(error="Unknown device or value."), 400
    if not broker["connected"]:
        return jsonify(error="The broker is not reachable."), 503
    room, device = target.split("/")
    client.publish(topics.cmd(room, device), value, qos=1)
    return jsonify(ok=True)


@app.get("/api/history/<metric>")
def api_history(metric: str):
    topic = HISTORY.get(metric)
    if topic is None:
        return jsonify(error="Unknown metric."), 404
    minutes = min(max(request.args.get("minutes", 60, type=int), 1), 1440)
    conn = db.connect()
    try:
        points = db.history(conn, topic, time.time() - minutes * 60)
    finally:
        conn.close()
    return jsonify(points=points)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    mqtt_util.start(client)
    log.info("Dashboard on http://%s:%s", config.DASH_HOST, config.DASH_PORT)
    serve(app, host=config.DASH_HOST, port=config.DASH_PORT, threads=8)


if __name__ == "__main__":
    main()
