"""Тесты для модуля InFlightService."""
import pytest
from aircraft_model import InFlightService, ServiceType, ServiceError, ValidationError


class TestInFlightServiceInit:
    """Тесты инициализации InFlightService."""

    def test_default_inventory(self, in_flight_service):
        assert in_flight_service.get_quantity(ServiceType.MEAL) == 150
        assert in_flight_service.get_quantity(ServiceType.BEVERAGE) == 150
        assert in_flight_service.get_quantity(ServiceType.ASSISTANCE) == 150
        assert in_flight_service.get_quantity(ServiceType.WIFI) == 150

    def test_available_services_list(self, in_flight_service):
        services = in_flight_service.available_services
        assert "MEAL" in services
        assert len(services) == 4


class TestInFlightServiceOperations:
    """Тесты операций InFlightService."""

    def test_provide_meal_success(self, in_flight_service):
        result = in_flight_service.provide_meal("hot", "PASS123")
        assert result["status"] == "provided"
        assert in_flight_service.get_quantity(ServiceType.MEAL) == 149

    def test_provide_meal_out_of_stock(self, in_flight_service):
        for i in range(150):
            in_flight_service.provide_meal("drain", f"PASS{i}")
        with pytest.raises(ServiceError, match="out of stock"):
            in_flight_service.provide_meal("last", "PASS999")

    def test_provide_beverage(self, in_flight_service):
        result = in_flight_service.provide_beverage("coffee", "PASS123")
        assert result["status"] == "provided"

    def test_assist_passenger(self, in_flight_service):
        result = in_flight_service.assist_passenger("wheelchair", "PASS123")
        assert result["service"] == "ASSISTANCE"

    def test_provide_wifi(self, in_flight_service):
        result = in_flight_service.provide_wifi("PASS123")
        assert result["status"] == "connected"

    def test_restock(self, in_flight_service):
        in_flight_service.restock(ServiceType.MEAL, 50)
        assert in_flight_service.get_quantity(ServiceType.MEAL) == 200

    def test_restock_invalid_quantity(self, in_flight_service):
        with pytest.raises(ValidationError, match="positive"):
            in_flight_service.restock(ServiceType.MEAL, -10)

    def test_get_stats(self, in_flight_service):
        in_flight_service.provide_meal("test", "PASS123")
        stats = in_flight_service.get_stats()
        assert stats[ServiceType.MEAL] == 1


class TestServiceLimits:
    """Тесты лимитов услуг."""

    def test_meal_limit_per_passenger(self, in_flight_service):
        in_flight_service.provide_meal("meal1", "PASS123")
        with pytest.raises(ServiceError, match="лимит"):
            in_flight_service.provide_meal("meal2", "PASS123")

    def test_beverage_limit_per_passenger(self, in_flight_service):
        for i in range(5):
            in_flight_service.provide_beverage(f"drink{i}", "PASS123")
        with pytest.raises(ServiceError, match="лимит"):
            in_flight_service.provide_beverage("drink6", "PASS123")

    def test_wifi_limit_per_passenger(self, in_flight_service):
        in_flight_service.provide_wifi("PASS123")
        with pytest.raises(ServiceError, match="лимит"):
            in_flight_service.provide_wifi("PASS123")

    def test_assistance_limit_per_passenger(self, in_flight_service):
        for i in range(5):
            in_flight_service.assist_passenger(f"help{i}", "PASS123")
        with pytest.raises(ServiceError, match="лимит"):
            in_flight_service.assist_passenger("help6", "PASS123")

    def test_different_passengers_independent_limits(self, in_flight_service):
        in_flight_service.provide_meal("meal1", "PASS123")
        result = in_flight_service.provide_meal("meal2", "PASS456")
        assert result["status"] == "provided"
