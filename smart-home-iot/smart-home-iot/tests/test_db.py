import time

from smarthome import config, db


def test_history_returns_numeric_points_in_range(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    conn = db.connect()
    now = time.time()
    db.log_message(conn, "home/livingroom/temperature/state", "20.5", now - 7200)  # too old
    db.log_message(conn, "home/livingroom/temperature/state", "24.0", now - 60)
    db.log_message(conn, "home/livingroom/temperature/state", "25.5", now - 30)
    db.log_message(conn, "home/livingroom/humidity/state", "50", now - 30)         # other topic
    points = db.history(conn, "home/livingroom/temperature/state", now - 3600)
    assert [round(p[1], 1) for p in points] == [24.0, 25.5]


def test_history_is_thinned(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    conn = db.connect()
    now = time.time()
    for i in range(1000):
        db.log_message(conn, "t", str(i), now - 1000 + i)
    assert len(db.history(conn, "t", now - 2000, max_points=100)) == 100


def test_prune_removes_old_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    conn = db.connect()
    db.log_message(conn, "t", "1", time.time() - 10 * 86400)
    db.log_message(conn, "t", "2")
    db.prune(conn, days=7)
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
