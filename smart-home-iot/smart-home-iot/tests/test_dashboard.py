from smarthome.dashboard import app as dash


def client():
    dash.broker["connected"] = True
    return dash.app.test_client()


def test_rejects_unknown_target_and_bad_value():
    c = client()
    assert c.post("/api/command", json={"target": "kitchen/oven", "value": "ON"}).status_code == 400
    assert c.post("/api/command", json={"target": "frontdoor/lock", "value": "ON"}).status_code == 400


def test_refuses_commands_when_broker_is_down():
    c = client()
    dash.broker["connected"] = False
    assert c.post("/api/command", json={"target": "livingroom/fan", "value": "ON"}).status_code == 503


def test_state_endpoint_shape():
    data = client().get("/api/state").get_json()
    assert {"state", "updated", "devices", "broker", "now"} <= set(data)


def test_unknown_history_metric_is_404():
    assert client().get("/api/history/pressure").status_code == 404
