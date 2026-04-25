"""Тесты для модуля Aircraft."""
import pytest
from aircraft_model import (
    Aircraft, AircraftStatus, CrewMember, CrewRole, Passenger,
    CapacityError, FlightError, TakeoffError, ValidationError
)


class TestAircraftValidation:
    """Тесты валидации Aircraft."""

    def test_create_valid(self):
        ac = Aircraft("Boeing 737", "RA-12345", 150)
        assert ac.model == "Boeing 737"
        assert ac.tail_number == "RA-12345"
        assert ac.capacity == 150

    def test_empty_model(self):
        with pytest.raises(ValidationError, match="модели"):
            Aircraft("", "RA-12345", 150)

    def test_short_tail_number(self):
        with pytest.raises(ValidationError, match="Бортовой номер"):
            Aircraft("Boeing 737", "RA1", 150)

    def test_zero_capacity(self):
        with pytest.raises(ValidationError, match="положительным"):
            Aircraft("Boeing 737", "RA-12345", 0)

    def test_excessive_capacity(self):
        with pytest.raises(ValidationError, match="превышает"):
            Aircraft("Boeing 737", "RA-12345", 1000)


class TestAircraftProperties:
    """Тесты свойств Aircraft."""

    def test_readonly_properties(self, aircraft):
        assert aircraft.model == "Boeing 737-800"
        assert aircraft.capacity == 150
        assert aircraft.status == AircraftStatus.ON_GROUND

    def test_passengers_copy(self, aircraft, registered_passenger):
        aircraft.add_passenger(registered_passenger)
        p_list = aircraft.passengers
        p_list.clear()
        assert aircraft.get_passenger_count() == 1


class TestAircraftPassengers:
    """Тесты управления пассажирами."""

    def test_add_passenger_success(self, aircraft, registered_passenger):
        assert aircraft.add_passenger(registered_passenger) is True
        assert aircraft.get_passenger_count() == 1

    def test_add_unregistered_passenger_fails(self, aircraft, passenger):
        with pytest.raises(FlightError, match="не зарегистрирован"):
            aircraft.add_passenger(passenger)

    def test_add_over_capacity_fails(self, aircraft, registered_passenger):
        aircraft._capacity = 1
        aircraft.add_passenger(registered_passenger)
        p2 = Passenger("Test User", "X12345", "T1", "1B")
        p2.register_for_flight()
        with pytest.raises(CapacityError):
            aircraft.add_passenger(p2)

    def test_remove_passenger(self, aircraft, registered_passenger):
        aircraft.add_passenger(registered_passenger)
        removed = aircraft.remove_passenger(registered_passenger.passport_number)
        assert removed is not None
        assert aircraft.get_passenger_count() == 0

    def test_clear_passengers(self, aircraft, registered_passenger):
        aircraft.add_passenger(registered_passenger)
        aircraft.clear_passengers()
        assert aircraft.get_passenger_count() == 0


class TestAircraftCrew:
    """Тесты управления экипажем."""

    def test_add_crew_success(self, aircraft, crew_member):
        assert aircraft.add_crew_member(crew_member) is True
        assert len(aircraft.crew) == 1

    def test_add_duplicate_crew_fails(self, aircraft, crew_member):
        aircraft.add_crew_member(crew_member)
        assert aircraft.add_crew_member(crew_member) is False

    def test_remove_crew(self, aircraft, crew_member):
        aircraft.add_crew_member(crew_member)
        removed = aircraft.remove_crew_member(crew_member.license_number)
        assert removed is not None
        assert len(aircraft.crew) == 0


class TestAircraftPreflight:
    """Тесты предполётной проверки."""

    def test_preflight_all_pass(self, aircraft_ready_for_takeoff):
        checks = aircraft_ready_for_takeoff.preflight_check()
        assert all(checks.values())

    def test_preflight_no_crew(self, aircraft, flight_route, registered_passenger):
        aircraft.set_route(flight_route)
        aircraft.add_passenger(registered_passenger)
        checks = aircraft.preflight_check()
        assert checks["crew_minimum"] is False

    def test_preflight_no_passengers(self, aircraft_with_crew, flight_route):
        aircraft_with_crew.set_route(flight_route)
        checks = aircraft_with_crew.preflight_check()
        assert checks["passengers_registered"] is False

    def test_preflight_no_route(self, aircraft_with_crew, registered_passenger):
        aircraft_with_crew.add_passenger(registered_passenger)
        checks = aircraft_with_crew.preflight_check()
        assert checks["route_set"] is False


class TestAircraftTakeoffLanding:
    """Тесты взлёта и посадки."""

    def test_takeoff_success(self, aircraft_ready_for_takeoff):
        aircraft_ready_for_takeoff.take_off()
        assert aircraft_ready_for_takeoff.status == AircraftStatus.IN_FLIGHT

    def test_takeoff_fails_checks(self, aircraft):
        with pytest.raises(TakeoffError, match="проверки"):
            aircraft.take_off()

    def test_land_success(self, aircraft_ready_for_takeoff):
        aircraft_ready_for_takeoff.take_off()
        aircraft_ready_for_takeoff.land()
        assert aircraft_ready_for_takeoff.status == AircraftStatus.ON_GROUND

    def test_land_wrong_status(self, aircraft):
        with pytest.raises(FlightError, match="Посадка невозможна"):
            aircraft.land()

    def test_reset_after_landing(self, aircraft_ready_for_takeoff):
        aircraft_ready_for_takeoff.take_off()
        aircraft_ready_for_takeoff.land()
        aircraft_ready_for_takeoff.reset_after_landing()
        assert aircraft_ready_for_takeoff.get_passenger_count() == 0
