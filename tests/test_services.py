import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from models import Pitch, TurfTypes, Maintenance
from services import PitchManager, MaintenanceManager, RainDamageEvent


# This file is mostly generated using my friend and mentor ChatGPT.
@pytest.fixture
def pitch():
    return Pitch(
        name="Test Pitch", location="Test Location", turf_type=TurfTypes.natural
    )


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
    pitch_manager.add_teardown("rain", 12)  # Expecting damage calculation based on hours

    # Check if the score has been decreased according to the damage
    expected_damage = RainDamageEvent.calculate_damage(pitch, 12)
    assert pitch.condition_score == 10 - expected_damage


@patch("services.MaintenanceManager.delay_maintenance")
def test_trigger_damage_event_delay_maintenance(mock_delay_maintenance, pitch_manager):
    pitch_manager.add_teardown("rain", 6)
    mock_delay_maintenance.assert_called()


def test_maintenance_manager_delay_maintenance(maintenance_manager, pitch):
    # Setup a mock Maintenance query
    mock_event = MagicMock()
    mock_event.timestamp = datetime.now()
    Maintenance.find = MagicMock(return_value=[mock_event])

    # Mock save method to avoid database interactions
    mock_event.save = MagicMock()

    maintenance_manager.delay_maintenance(48)  # Adding 48 hours
    updated_time = datetime.now() + timedelta(hours=48)

    # Assert that the event timestamp was updated
    assert mock_event.timestamp.hour == updated_time.hour
    mock_event.save.assert_called_once()
