from enum import Enum

from pymongo import MongoClient
from bunnet import Document, init_bunnet, Link
from config import settings


class TurfTypes(str, Enum):
    natural = "natural"
    artificial = "artificial"
    hybrid = "hybrid"


class Pitch(Document):
    name: str
    location: str

    turf_type: TurfTypes

    condition_score: int = 10

    # maintenance
    can_be_maintained: bool = True
    last_maintained: float = 0
    next_maintenance: float = 0

    # replacement
    replacement_date: float = 0
    must_be_replaced: bool = False

    def get_score(self) -> int:
        return self.condition_score

    def set_score(self, new_score: int) -> None:
        self.condition_score = new_score


class MaintenanceStatuses(str, Enum):
    scheduled = "scheduled"
    rescheduled = "rescheduled"
    done = "done"
    canceled = "canceled"


class Maintenance(Document):
    pitch: Link[Pitch]
    timestamp: float
    status: MaintenanceStatuses = MaintenanceStatuses.scheduled


# Bunnet uses Pymongo client under the hood
client = MongoClient(settings.MONGO_CONNECTION_STRING)

# Initialize bunnet with the Product document class
init_bunnet(
    database=client.db_name,
    document_models=[Pitch, Maintenance],
)
