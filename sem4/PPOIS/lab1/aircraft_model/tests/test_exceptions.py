"""Тесты для модуля exceptions."""
from aircraft_model import (
    ValidationError, FlightError, CapacityError, CrewError,
    RegistrationError, ServiceError, TakeoffError, LandingError
)


class TestExceptions:
    """Тесты исключений."""

    def test_validation_error(self):
        e = ValidationError("field", "details")
        assert "field" in str(e)
        assert "details" in str(e)

    def test_flight_error(self):
        e = FlightError("test message")
        assert "test message" in e.message

    def test_capacity_error(self):
        e = CapacityError(100, 150)
        assert "150" in str(e)
        assert "100" in str(e)

    def test_crew_error(self):
        e = CrewError("crew issue")
        assert "crew issue" in e.message

    def test_registration_error(self):
        e = RegistrationError("registration issue")
        assert "registration issue" in e.message

    def test_service_error(self):
        e = ServiceError("service issue")
        assert "service issue" in e.message

    def test_takeoff_error(self):
        e = TakeoffError("takeoff issue")
        assert "takeoff issue" in e.message

    def test_landing_error(self):
        e = LandingError("landing issue")
        assert "landing issue" in e.message
