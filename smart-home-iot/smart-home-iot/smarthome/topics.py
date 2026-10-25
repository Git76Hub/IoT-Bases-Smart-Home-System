"""MQTT topic scheme: home/<room>/<device>/<state|set>, home/devices/<id>/status."""


def state(room: str, device: str) -> str:
    """Topic a device publishes its current value/state to."""
    return f"home/{room}/{device}/state"


def cmd(room: str, device: str) -> str:
    """Topic a controller publishes commands to."""
    return f"home/{room}/{device}/set"


def status(device_id: str) -> str:
    """Online/offline topic (retained, offline set as Last Will)."""
    return f"home/devices/{device_id}/status"


TEMP = state("livingroom", "temperature")
HUM = state("livingroom", "humidity")
LIGHT_STATE, LIGHT_SET = state("livingroom", "light"), cmd("livingroom", "light")
FAN_STATE, FAN_SET = state("livingroom", "fan"), cmd("livingroom", "fan")

MOTION = state("hallway", "motion")
HALL_LIGHT_STATE, HALL_LIGHT_SET = state("hallway", "light"), cmd("hallway", "light")

DOOR_LOCK_STATE, DOOR_LOCK_SET = state("frontdoor", "lock"), cmd("frontdoor", "lock")

AUTO_STATE, AUTO_SET = state("system", "auto"), cmd("system", "auto")
