"""Тесты для модуля FlightRoute."""
import pytest
from aircraft_model import FlightRoute, ValidationError


class TestFlightRouteValidation:
    """Тесты валидации FlightRoute."""

    def test_create_valid(self):
        route = FlightRoute("SVO", "LED", 634.0)
        assert route.departure == "SVO"
        assert route.destination == "LED"
        assert route.distance == 634.0

    def test_invalid_airport_code(self):
        with pytest.raises(ValidationError, match="IATA"):
            FlightRoute("INVALID", "LED", 100)

    def test_negative_distance(self):
        with pytest.raises(ValidationError, match="positive"):
            FlightRoute("SVO", "LED", -100)

    def test_excessive_distance(self):
        with pytest.raises(ValidationError, match="exceeds"):
            FlightRoute("SVO", "LED", 25000)


class TestFlightRouteProperties:
    """Тесты свойств FlightRoute."""

    def test_properties(self, flight_route):
        assert flight_route.departure == "SVO"
        assert flight_route.destination == "LED"
        assert flight_route.distance == 634.0
        assert flight_route.estimated_duration.total_seconds() > 0

    def test_alternative_airports(self, flight_route):
        assert len(flight_route.alternative_airports) == 0
