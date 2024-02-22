from models import Maintenance, MaintenanceStatuses, Pitch
from datetime import datetime, timedelta
from utils import event_listener


class PitchManager:
    pitch: Pitch = None

    def __init__(self, pitch: Pitch) -> None:
        self.pitch = pitch

    def add_to_score(self, number: int):
        new_score = self.pitch.get_score() + number
        self.pitch.set_score(new_score)

        # persist
        self.pitch.save()

        event_listener.trigger_event("score_changed", self.pitch, new_score)

    def add_rain_damage(self, hours: int):
        event_listener.trigger_event(
            "add_damage", self.pitch, event_type="rain", hours=hours
        )

    def set_property(self, property_name, value):
        self.pitch.set({property_name: value})


class MaintenanceManager:
    pitch: Pitch = None
    pitch_manager = None

    def __init__(self, pitch_manager: PitchManager) -> None:
        self.pitch_manager = pitch_manager
        self.pitch = pitch_manager.pitch

    def delay_maintenance_when_applicable(self, hours):
        scheduled_events = self.list_scheduled_events()
        if len(scheduled_events) > 0:
            for event in scheduled_events:
                new_time = datetime.now() + timedelta(hours=hours)
                if event.timestamp < new_time.timestamp():
                    event.timestamp = new_time.timestamp()
                    self.pitch_manager.set_property(
                        "next_maintenance", new_time.timestamp()
                    )
                    event.save()

    def complete_scheduled_maintenance(self, maintenance: Maintenance):
        maintenance.status = MaintenanceStatuses.done
        self.pitch.last_maintained = maintenance.timestamp

        maintenance.save()
        self.pitch.save()

        event_listener.trigger_event("maintenance_completed", self.pitch)

    def add_scheduled_maintenance(self, timestamp: float):
        scheduled_maintenance = Maintenance(pitch=self.pitch, timestamp=timestamp)

        events = self.list_scheduled_events()

        if len(events) > 0:
            raise "A maintenance event is already scheduled."

        self.pitch.next_maintenance = timestamp
        self.pitch.save()

        scheduled_maintenance.insert()

    def remove_scheduled_maintenance(self):
        self.pitch.next_maintenance = 0
        self.pitch.save()

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
