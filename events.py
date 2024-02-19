import math
from models import TurfTypes
from services import PitchManager, MaintenanceManager
from datetime import datetime


def trigger_complete_maintenance(pitch):
    manager = PitchManager(pitch)
    manager.add_to_score(4)
    trigger_score_change(pitch, pitch.get_score())


def trigger_score_change(pitch, new_score):
    check_maintainability(pitch, new_score)


def trigger_damage_event(pitch, event_type, hours):
    if event_type == "rain":
        RainDamageEvent(pitch, hours)


def check_maintainability(pitch, new_score):
    manager = MaintenanceManager(pitch)

    if new_score <= 2:
        manager.stop_maintenance()

        pitch.must_be_replaced = True
        pitch.save()

    elif new_score == 10:
        manager.stop_maintenance()
    else:
        if pitch.can_be_maintained is False:
            manager.continue_maintenance()
            pitch.must_be_replaced = False
            pitch.save()
        else:
            scheduled_events = manager.list_scheduled_events()

            if len(scheduled_events) == 0:
                manager.add_scheduled_maintenance(datetime.now().timestamp())


class RainDamageEvent:

    def __init__(self, pitch, hours):
        damage = self.calculate_damage(pitch, hours)
        pitch_manager = PitchManager(pitch)
        pitch_manager.add_to_score(damage * -1)

        if pitch.can_be_maintained:
            time_to_dry = self.calculate_time_to_dry(pitch)
            maintenance_manager = MaintenanceManager(pitch)
            maintenance_manager.delay_maintenance_when_applicable(time_to_dry)

    @staticmethod
    def calculate_time_to_dry(pitch):
        match pitch.turf_type:
            case TurfTypes.natural:
                return 36
            case TurfTypes.hybrid:
                return 24
            case TurfTypes.artificial:
                return 12

    @staticmethod
    def calculate_damage(pitch, hours):
        match pitch.turf_type:
            case TurfTypes.natural:
                return RainDamageEvent.calculate_cycles(3, hours) * 2
            case TurfTypes.hybrid:
                return RainDamageEvent.calculate_cycles(4, hours) * 2
            case TurfTypes.artificial:
                return RainDamageEvent.calculate_cycles(6, hours) * 2
            case _:
                raise "Turf type is not supported."

    @staticmethod
    def calculate_cycles(cycle, hours):
        return math.floor(hours / cycle)
