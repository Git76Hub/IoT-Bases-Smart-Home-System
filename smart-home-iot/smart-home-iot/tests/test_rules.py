from smarthome import topics
from smarthome.automation import RuleEngine


def engine():
    return RuleEngine(fan_on=28, hysteresis=1.5, light_delay=30)


def test_fan_turns_on_at_threshold_and_off_below_hysteresis():
    e = engine()
    assert e.handle(topics.TEMP, "28.1", 0) == [(topics.FAN_SET, "ON", False)]
    e.handle(topics.FAN_STATE, "ON", 1)
    assert e.handle(topics.TEMP, "27.5", 2) == []                 # inside the hysteresis band
    assert e.handle(topics.TEMP, "26.4", 3) == [(topics.FAN_SET, "OFF", False)]


def test_fan_not_commanded_again_when_already_on():
    e = engine()
    e.handle(topics.FAN_STATE, "ON", 0)
    assert e.handle(topics.TEMP, "30", 1) == []


def test_bad_temperature_payload_is_ignored():
    assert engine().handle(topics.TEMP, "nan?", 0) == []


def test_motion_turns_light_on_then_off_after_delay():
    e = engine()
    assert e.handle(topics.MOTION, "1", 100) == [(topics.HALL_LIGHT_SET, "ON", False)]
    e.handle(topics.HALL_LIGHT_STATE, "ON", 101)
    assert e.tick(120) == []                                       # 20 s: still waiting
    assert e.tick(131) == [(topics.HALL_LIGHT_SET, "OFF", False)]
    assert e.tick(140) == []                                       # only once


def test_new_motion_restarts_the_timer():
    e = engine()
    e.handle(topics.MOTION, "1", 0)
    e.handle(topics.HALL_LIGHT_STATE, "ON", 1)
    e.handle(topics.MOTION, "1", 25)
    assert e.tick(40) == []
    assert e.tick(56) == [(topics.HALL_LIGHT_SET, "OFF", False)]


def test_manually_switched_light_is_not_turned_off_by_rule():
    e = engine()
    e.handle(topics.HALL_LIGHT_STATE, "ON", 0)                     # user turned it on
    assert e.handle(topics.MOTION, "1", 1) == []
    assert e.tick(500) == []


def test_auto_mode_off_disables_rules_and_is_published_retained():
    e = engine()
    assert e.handle(topics.AUTO_SET, "OFF", 0) == [(topics.AUTO_STATE, "OFF", True)]
    assert e.handle(topics.TEMP, "35", 1) == []
    assert e.handle(topics.MOTION, "1", 2) == []
    e.handle(topics.AUTO_SET, "ON", 3)
    assert e.handle(topics.TEMP, "35", 4) == [(topics.FAN_SET, "ON", False)]


def test_auto_mode_restored_from_retained_state():
    e = engine()
    assert e.handle(topics.AUTO_STATE, "OFF", 0) == []
    assert e.auto is False
