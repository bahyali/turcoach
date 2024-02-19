from events import (
    trigger_complete_maintenance,
    trigger_damage_event,
    trigger_score_change,
)
from utils import event_listener

event_listener.add_listener("maintenance_completed", trigger_complete_maintenance)

event_listener.add_listener("score_changed", trigger_score_change)

event_listener.add_listener("add_damage", trigger_damage_event)


def listen():
    pass
