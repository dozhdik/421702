"""Тесты для модуля enums."""
from aircraft_model import (
    AircraftStatus, CrewRole, ServiceType
)


class TestEnums:
    """Тесты перечислений."""

    def test_aircraft_status_values(self):
        assert AircraftStatus.ON_GROUND.name == "ON_GROUND"
        assert AircraftStatus.IN_FLIGHT.name == "IN_FLIGHT"

    def test_crew_role_values(self):
        assert CrewRole.PILOT.name == "PILOT"
        assert CrewRole.FLIGHT_ATTENDANT.name == "FLIGHT_ATTENDANT"

    def test_service_type_count(self):
        assert len(list(ServiceType)) == 4
