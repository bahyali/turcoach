import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from models import Pitch, TurfTypes
from services import PitchManager, MaintenanceManager
import listeners

listeners.listen()


@pytest.fixture
def pitch():
    return Pitch(
        name="Test Pitch",
        location="Test Location",
        turf_type=TurfTypes.natural,
    ).insert()


@pytest.fixture
def pitch_manager(pitch):
    return PitchManager(pitch)


@pytest.fixture
def maintenance_manager(pitch):
    return MaintenanceManager(pitch)


def test_add_to_score(pitch_manager, pitch):
    # Initial condition score is 10
    pitch_manager.add_to_score(-3)
    assert pitch.condition_score == 7


def test_trigger_damage_event_rain_natural(pitch_manager, pitch):
    pitch.turf_type = TurfTypes.natural
    pitch_manager.add_rain_damage(12)

    # Check if the score has been decreased according to the damage
    expected_damage = 8
    assert pitch.condition_score == 10 - expected_damage


@patch("services.MaintenanceManager.delay_maintenance_when_applicable")
def test_trigger_damage_event_delay_maintenance(
    mock_delay_maintenance, pitch, pitch_manager
):
    old_time = pitch.next_maintenance
    pitch_manager.add_rain_damage(6)

    fresh_pitch = Pitch.find_one(Pitch.id == pitch.id).run()
    assert fresh_pitch.next_maintenance > old_time


def test_trigger_damage_event_dont_delay_maintenance(pitch_manager, pitch):
    old_time = pitch.next_maintenance
    pitch_manager.add_rain_damage(2)

    fresh_pitch = Pitch.find_one(Pitch.id == pitch.id).run()
    assert fresh_pitch.next_maintenance == old_time


@patch("services.MaintenanceManager.list_scheduled_events")
def test_maintenance_manager_delay_maintenance(
    mock_list_scheduled_events, maintenance_manager
):
    # Setup a mock Maintenance query
    mock_event = MagicMock()
    mock_event.timestamp = datetime.now().timestamp()

    mock_list_scheduled_events.return_value = [mock_event]

    # Mock save method to avoid database interactions
    mock_event.save = MagicMock()

    maintenance_manager.delay_maintenance_when_applicable(48)  # Adding 48 hours
    updated_time = datetime.now() + timedelta(hours=48)

    # Assert that the event timestamp was updated
    assert datetime.fromtimestamp(mock_event.timestamp).hour == updated_time.hour
    assert datetime.fromtimestamp(mock_event.timestamp).minute == updated_time.minute

    mock_event.save.assert_called_once()
