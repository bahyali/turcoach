from datetime import datetime, timedelta
import math
from models import Maintenance, MaintenanceStatuses, Pitch, TurfTypes


class PitchManager:
    pitch: Pitch = None

    def __init__(self, pitch: Pitch) -> None:
        self.pitch = pitch

    def add_to_score(self, number: int):
        old_score = self.pitch.get_score()
        new_score = self.pitch.get_score() + number
        self.pitch.set_score(new_score)

        # persist
        self.pitch.save()

        # trigger event
        trigger_score_change(self.pitch, new_score, old_score)

    def add_teardown(self, event_type, hours):
        trigger_damage_event(self.pitch, event_type, hours)


class MaintenanceManager:
    pitch: Pitch = None

    def __init__(self, pitch: Pitch) -> None:
        self.pitch = pitch

    def delay_maintenance_when_applicable(self, hours):
        scheduled_events = self.list_scheduled_events()
        if len(scheduled_events) > 0:
            for event in scheduled_events:
                new_time = datetime.now() + timedelta(hours=hours)
                if event.timestamp < new_time.timestamp():
                    event.timestamp = new_time.timestamp()
                    print("event", event)
                    event.save()

    def complete_scheduled_maintenance(self, maintenance: Maintenance):
        maintenance.status = MaintenanceStatuses.done
        self.pitch.last_maintained = maintenance.timestamp

        maintenance.save(maintenance)
        self.pitch.save()

        manager = PitchManager(self.pitch)
        manager.add_to_score(4)

    def add_scheduled_maintenance(self, timestamp: int):
        scheduled_maintenance = Maintenance(pitch=self.pitch, timestamp=timestamp)

        events = self.list_scheduled_events()

        if len(events) > 0:
            raise "A maintenance event is already scheduled."

        self.pitch.next_maintenance = timestamp
        self.pitch.save()

        scheduled_maintenance.insert()

    def remove_scheduled_maintenance(self):
        Maintenance.find(
            Maintenance.pitch.id == self.pitch.id,
            Maintenance.status == MaintenanceStatuses.scheduled,
        ).delete().run()

    def add_scheduled_replacement(self, timestamp):
        self.pitch.replacement_date = timestamp
        self.pitch.save()

    def list_scheduled_events(self):
        return Maintenance.find(
            Maintenance.pitch.id == self.pitch.id,
            Maintenance.status == MaintenanceStatuses.scheduled,
        ).to_list()

    def stop_maintenance(self):
        self.pitch.can_be_maintained = False
        self.pitch.save()
        self.remove_scheduled_maintenance()

    def continue_maintenance(self):
        self.pitch.can_be_maintained = True
        new_time = datetime.now() + timedelta(hours=6)
        self.add_scheduled_maintenance(new_time.timestamp())
        self.pitch.save()


# TODO resolve cyclic dependencies.

# ----------------- Event Triggers


def trigger_score_change(pitch, new_score, old_score):
    check_maintainability(pitch, new_score)


def trigger_damage_event(pitch, event_type, hours):
    if event_type == "rain":
        RainDamageEvent(pitch, hours)


# ----------------- Events


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
