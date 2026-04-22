"""
Тесты для CLI-модуля main.py и бизнес-логики aircraft_model.
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from aircraft_model import (
    Aircraft,
    AircraftStatus,
    CrewMember,
    CrewRole,
    FlightRoute,
    Passenger,
    Ticket,
    TicketStatus,
    CapacityError,
    CrewError,
    FlightError,
    LandingError,
    RegistrationError,
    ServiceError,
    TakeoffError,
    ValidationError,
)
from aircraft_model.enums import ServiceType


# ============================================================================
# ТЕСТЫ ДЛЯ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ main.py
# ============================================================================

class TestSafeInput:
    """Тесты для функции safe_input."""

    def test_safe_input_normal(self):
        with patch('builtins.input', return_value='test input'):
            from main import safe_input
            result = safe_input("")
            assert result == "test input"

    def test_safe_input_strips(self):
        with patch('builtins.input', return_value='  spaces  '):
            from main import safe_input
            result = safe_input("")
            assert result == "spaces"

    def test_safe_input_empty(self):
        with patch('builtins.input', return_value=''):
            from main import safe_input
            result = safe_input("")
            assert result == ""

    def test_safe_input_keyboard_interrupt(self):
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            from main import safe_input
            result = safe_input("")
            assert result is None


class TestGetChoice:
    """Тесты для функции get_choice."""

    def test_get_choice_returns_int(self):
        with patch('builtins.input', return_value='42'):
            from main import get_choice
            result = get_choice()
            assert result == 42

    def test_get_choice_empty_returns_none(self):
        with patch('builtins.input', return_value=''):
            from main import get_choice
            result = get_choice()
            assert result is None

    def test_get_choice_invalid_returns_none(self):
        with patch('builtins.input', return_value='not a number'):
            from main import get_choice
            result = get_choice()
            assert result is None

    def test_get_choice_keyboard_interrupt(self):
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            from main import get_choice
            result = get_choice()
            assert result is None


class TestOutputFunctions:
    """Тесты выходных функций."""

    def test_header(self, capsys):
        from main import header
        header("TEST")
        captured = capsys.readouterr()
        assert "--- TEST ---" in captured.out

    def test_info(self, capsys):
        from main import info
        info("test")
        captured = capsys.readouterr()
        assert "[INFO] test" in captured.out

    def test_success(self, capsys):
        from main import success
        success("ok")
        captured = capsys.readouterr()
        assert "[OK] ok" in captured.out

    def test_warning(self, capsys):
        from main import warning
        warning("warn")
        captured = capsys.readouterr()
        assert "[WARN] warn" in captured.out

    def test_error(self, capsys):
        from main import error
        error("err")
        captured = capsys.readouterr()
        assert "[ERROR] err" in captured.out

    def test_step(self, capsys):
        from main import step
        step(1, "desc")
        captured = capsys.readouterr()
        assert "[STEP 1] desc" in captured.out


# ============================================================================
# ТЕСТЫ ДЛЯ Airport И AIRPORT_DISTANCES
# ============================================================================

class TestAirport:
    """Тесты для класса Airport."""

    def test_all_airports(self):
        from main import Airport
        airports = Airport.all()
        assert len(airports) == 6
        assert "SVO" in airports
        assert "LED" in airports
        assert "AER" in airports

    def test_display_all(self):
        from main import Airport
        display = Airport.display_all()
        assert "SVO" in display
        assert "LED" in display

    def test_get_name(self):
        from main import Airport
        name = Airport.get_name("SVO")
        assert "Шереметьево" in name or "SVO" in name


class TestAirportDistances:
    """Тесты для расстояний между аэропортами."""

    def test_get_distance_moscow_petersburg(self):
        from main import get_distance
        dist = get_distance("SVO", "LED")
        assert dist == 634.0

    def test_get_distance_petersburg_moscow(self):
        from main import get_distance
        dist = get_distance("LED", "SVO")
        assert dist == 634.0

    def test_get_distance_unknown_route(self):
        from main import get_distance
        dist = get_distance("XXX", "YYY")
        assert dist == 800.0  # default


# ============================================================================
# ТЕСТЫ ДЛЯ Flight
# ============================================================================

class TestFlightCreation:
    """Тесты для создания рейса."""

    def test_flight_creation(self, sample_aircraft):
        from main import Flight
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        assert flight.flight_number == "SU123"
        assert flight.departure == "SVO"
        assert flight.destination == "LED"
        assert flight.distance_km > 0

    def test_flight_calculates_route(self, sample_aircraft):
        from main import Flight
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        assert flight.distance_km == 634.0
        assert flight.fuel_needed > 0
        assert flight.duration_hours > 0


class TestFlightPassengers:
    """Тесты для пассажиров рейса."""

    def test_add_passenger(self, sample_aircraft, sample_passenger):
        from main import Flight
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        sample_passenger.register_for_flight()
        flight.add_passenger(sample_passenger)
        assert flight.get_passenger_count() == 1

    def test_is_seat_taken(self, sample_aircraft, sample_passenger):
        from main import Flight
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        sample_passenger.register_for_flight()
        flight.add_passenger(sample_passenger)
        assert flight.is_seat_taken("1A") is True
        assert flight.is_seat_taken("2B") is False

    def test_is_passenger_on_flight(self, sample_aircraft, sample_passenger):
        from main import Flight
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        sample_passenger.register_for_flight()
        flight.add_passenger(sample_passenger)
        assert flight.is_passenger_on_flight("TP12345678") is True
        assert flight.is_passenger_on_flight("OTHER") is False


# ============================================================================
# ТЕСТЫ ДЛЯ SystemState
# ============================================================================

class TestSystemState:
    """Тесты для SystemState."""

    def test_reset(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft['test'] = 'value'
        s.reset()
        assert s.aircraft == {}
        assert s.flights == {}
        assert s.passengers == {}

    def test_is_tail_number_exists(self, sample_aircraft):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft["RA-737TEST"] = sample_aircraft
        assert s.is_tail_number_exists("RA-737TEST") is True
        assert s.is_tail_number_exists("OTHER") is False

    def test_is_flight_number_exists(self, sample_aircraft):
        from main import SystemState
        from main import Flight
        SystemState._instance = None
        s = SystemState()
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        s.flights["SU123"] = flight
        assert s.is_flight_number_exists("SU123") is True
        assert s.is_flight_number_exists("OTHER") is False

    def test_is_passport_exists(self, sample_passenger):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.passengers["TP12345678"] = sample_passenger
        assert s.is_passport_exists("TP12345678") is True
        assert s.is_passport_exists("OTHER") is False

    def test_get_aircraft(self, sample_aircraft):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft["RA-737TEST"] = sample_aircraft
        found = s.get_aircraft("RA-737TEST")
        assert found == sample_aircraft
        found = s.get_aircraft("ra-737test")
        assert found == sample_aircraft

    def test_get_flight(self, sample_aircraft):
        from main import SystemState
        from main import Flight
        SystemState._instance = None
        s = SystemState()
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        s.flights["SU123"] = flight
        found = s.get_flight("SU123")
        assert found == flight

    def test_get_flight_by_aircraft(self, sample_aircraft):
        from main import SystemState
        from main import Flight
        SystemState._instance = None
        s = SystemState()
        flight = Flight(
            flight_number="SU123",
            aircraft=sample_aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        s.flights["SU123"] = flight
        found = s.get_flight_by_aircraft(sample_aircraft)
        assert found == flight


# ============================================================================
# ТЕСТЫ ДЛЯ Aircraft
# ============================================================================

class TestAircraftCreation:
    """Тесты для создания самолёта."""

    def test_create_aircraft_valid(self):
        aircraft = Aircraft(
            model="Boeing 737-800",
            tail_number="RA-12345",
            capacity=150,
        )
        assert aircraft.model == "Boeing 737-800"
        assert aircraft.tail_number == "RA-12345"
        assert aircraft.capacity == 150
        assert aircraft.status == AircraftStatus.ON_GROUND

    def test_create_aircraft_invalid_capacity_zero(self):
        with pytest.raises(ValidationError):
            Aircraft("Boeing", "RA-12345", 0)

    def test_create_aircraft_invalid_capacity_negative(self):
        with pytest.raises(ValidationError):
            Aircraft("Boeing", "RA-12345", -10)

    def test_create_aircraft_invalid_tail_empty(self):
        with pytest.raises(ValidationError):
            Aircraft("Boeing", "", 150)


class TestAircraftPassengers:
    """Тесты для работы с пассажирами."""

    def test_add_passenger(self, aircraft_on_ground, registered_passenger):
        count = aircraft_on_ground.get_passenger_count()
        assert count >= 1

    def test_remove_passenger(self, aircraft_on_ground):
        passengers = aircraft_on_ground._passengers
        if passengers:
            removed = aircraft_on_ground.remove_passenger(
                passengers[0].passport_number
            )
            assert removed is not None


class TestAircraftCrew:
    """Тесты для работы с экипажем."""

    def test_add_crew_member(self, sample_aircraft, sample_crew):
        result = sample_aircraft.add_crew_member(sample_crew)
        assert result is True
        assert len(sample_aircraft.crew) == 1

    def test_add_crew_duplicate_license(self, sample_aircraft, sample_crew):
        sample_aircraft.add_crew_member(sample_crew)
        result = sample_aircraft.add_crew_member(sample_crew)
        assert result is False


class TestAircraftStatus:
    """Тесты для изменения статуса."""

    def test_change_status(self, sample_aircraft):
        sample_aircraft.change_status(AircraftStatus.BOARDING)
        assert sample_aircraft.status == AircraftStatus.BOARDING

    def test_set_route(self, sample_aircraft, sample_route):
        sample_aircraft.set_route(sample_route)
        assert sample_aircraft._flight_route == sample_route


class TestAircraftPreflight:
    """Тесты для предполётной проверки."""

    def test_preflight_check_structure(self, aircraft_on_ground):
        checks = aircraft_on_ground.preflight_check()
        assert "crew_minimum" in checks
        assert "crew_on_duty" in checks
        assert "passengers_registered" in checks
        assert "route_set" in checks
        assert "status_ok" in checks

    def test_preflight_check_no_crew(self, sample_aircraft):
        checks = sample_aircraft.preflight_check()
        assert checks["crew_minimum"] is False


class TestAircraftTakeoff:
    """Тесты для взлёта."""

    def test_takeoff_requires_crew(self, aircraft_on_ground):
        # Убираем экипаж
        aircraft_on_ground._crew.clear()
        with pytest.raises(TakeoffError):
            aircraft_on_ground.take_off()

    def test_takeoff_requires_on_ground(self, in_flight_aircraft):
        with pytest.raises(TakeoffError):
            in_flight_aircraft.take_off()

    def test_takeoff_requires_route(self, sample_aircraft, crew_on_duty, registered_passenger):
        # Требуется маршрут
        attendee = CrewMember("Attendant", CrewRole.FLIGHT_ATTENDANT, "FA-TEST001")
        attendee.start_duty()
        sample_aircraft.add_crew_member(crew_on_duty)
        sample_aircraft.add_crew_member(attendee)
        sample_aircraft.add_passenger(registered_passenger)
        # Без маршрута взлёт невозможен
        with pytest.raises(TakeoffError):
            sample_aircraft.take_off()


class TestAircraftLanding:
    """Тесты для посадки."""

    def test_land_in_flight(self, in_flight_aircraft):
        in_flight_aircraft.land()
        assert in_flight_aircraft.status == AircraftStatus.ON_GROUND

    def test_land_on_ground_fails(self, aircraft_on_ground):
        with pytest.raises(FlightError):
            aircraft_on_ground.land()


# ============================================================================
# ТЕСТЫ ДЛЯ Passenger
# ============================================================================

class TestPassengerCreation:
    """Тесты для создания пассажира."""

    def test_create_passenger_valid(self):
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
            seat_number="12A",
        )
        assert passenger.full_name == "Иван Петров"
        assert passenger.passport_number == "AB12345678"
        assert passenger.seat_number == "12A"

    def test_create_passenger_no_seat(self):
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
        )
        assert passenger.seat_number is None


class TestPassengerRegistration:
    """Тесты для регистрации."""

    def test_register_with_seat(self):
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
            seat_number="12A",
        )
        result = passenger.register_for_flight()
        assert result is True
        assert passenger.is_registered

    def test_register_without_seat_fails(self):
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
        )
        with pytest.raises(RegistrationError):
            passenger.register_for_flight()

    def test_register_twice_fails(self):
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
            seat_number="12A",
        )
        passenger.register_for_flight()
        with pytest.raises(RegistrationError):
            passenger.register_for_flight()

    def test_assign_seat(self):
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
        )
        passenger.assign_seat("15B")
        assert passenger.seat_number == "15B"


# ============================================================================
# ТЕСТЫ ДЛЯ Ticket
# ============================================================================

class TestTicketCreation:
    """Тесты для создания билета."""

    def test_issue_ticket(self):
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        assert ticket.flight_number == "SU123"
        assert ticket.seat == "12A"
        assert ticket.status == TicketStatus.BOOKED


class TestTicketOperations:
    """Тесты для операций с билетом."""

    def test_validate_valid_ticket(self):
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        assert ticket.validate() is True

    def test_validate_cancelled_ticket_fails(self):
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        ticket.cancel()
        with pytest.raises(FlightError):
            ticket.validate()

    def test_confirm_ticket(self):
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        ticket.confirm()
        assert ticket.status == TicketStatus.CONFIRMED

    def test_use_ticket(self):
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        ticket.use()
        assert ticket.status == TicketStatus.USED

    def test_cancel_ticket(self):
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        result = ticket.cancel()
        assert result is True
        assert ticket.status == TicketStatus.CANCELLED


# ============================================================================
# ТЕСТЫ ДЛЯ CrewMember
# ============================================================================

class TestCrewMemberCreation:
    """Тесты для создания члена экипажа."""

    def test_create_crew_valid(self):
        crew = CrewMember(
            full_name="Иван Иванов",
            role=CrewRole.PILOT,
            license_number="PLT-12345",
        )
        assert crew.full_name == "Иван Иванов"
        assert crew.role == CrewRole.PILOT
        assert crew.license_number == "PLT-12345"

    def test_create_crew_invalid_name_empty(self):
        with pytest.raises(ValidationError):
            CrewMember("", CrewRole.PILOT, "PLT-12345")


class TestCrewMemberOperations:
    """Тесты для операций члена экипажа."""

    def test_start_duty(self, sample_crew):
        result = sample_crew.start_duty()
        assert result is True
        assert sample_crew.is_on_duty

    def test_end_duty(self, sample_crew):
        sample_crew.start_duty()
        result = sample_crew.end_duty()
        assert result is True
        assert not sample_crew.is_on_duty

    def test_perform_duty_on_duty(self, crew_on_duty):
        result = crew_on_duty.perform_duty("пилотирование")
        assert result["status"] == "completed"

    def test_perform_duty_not_on_duty_fails(self, sample_crew):
        with pytest.raises(CrewError):
            sample_crew.perform_duty("пилотирование")

    def test_can_fly_pilot_on_duty(self, crew_on_duty):
        assert crew_on_duty.can_fly() is True

    def test_can_fly_pilot_not_on_duty(self, sample_crew):
        assert sample_crew.can_fly() is False

    def test_can_fly_attendant(self):
        crew = CrewMember("Иван", CrewRole.FLIGHT_ATTENDANT, "FA-001")
        crew.start_duty()
        assert crew.can_fly() is False


# ============================================================================
# ТЕСТЫ ДЛЯ FlightRoute
# ============================================================================

class TestFlightRouteCreation:
    """Тесты для создания маршрута."""

    def test_create_route_valid(self):
        route = FlightRoute("SVO", "LED", 650)
        assert route.departure == "SVO"
        assert route.destination == "LED"
        assert route.distance == 650

    def test_create_route_invalid_airport_empty(self):
        with pytest.raises(ValidationError):
            FlightRoute("", "LED", 650)

    def test_create_route_invalid_distance_zero(self):
        with pytest.raises(ValidationError):
            FlightRoute("SVO", "LED", 0)


class TestFlightRouteOperations:
    """Тесты для операций с маршрутом."""

    def test_calculate_fuel_default(self):
        route = FlightRoute("SVO", "LED", 1000)
        fuel = route.calculate_fuel()
        assert fuel > 3000

    def test_estimate_duration(self):
        route = FlightRoute("SVO", "LED", 800)
        duration = route.estimate_duration()
        assert duration.total_seconds() > 0

    def test_add_alternative(self):
        route = FlightRoute("SVO", "LED", 650)
        route.add_alternative("AER")
        assert "AER" in route.alternative_airports

    def test_is_route_compatible(self):
        route1 = FlightRoute("SVO", "LED", 650)
        route2 = FlightRoute("LED", "AER", 1800)
        assert route1.is_route_compatible(route2) is True

    def test_route_add_operator(self):
        route1 = FlightRoute("SVO", "LED", 650)
        route2 = FlightRoute("LED", "AER", 1800)
        combined = route1 + route2
        assert combined.departure == "SVO"
        assert combined.destination == "AER"


# ============================================================================
# ТЕСТЫ ДЛЯ InFlightService
# ============================================================================

class TestInFlightServiceCreation:
    """Тесты для создания сервиса."""

    def test_service_initialization(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        assert service.get_quantity(ServiceType.MEAL) > 0
        assert service.get_quantity(ServiceType.BEVERAGE) > 0


class TestInFlightServiceOperations:
    """Тесты для операций сервиса."""

    def test_provide_meal(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        initial = service.get_quantity(ServiceType.MEAL)
        result = service.provide_meal("горячее питание")
        assert result["status"] == "provided"
        assert service.get_quantity(ServiceType.MEAL) == initial - 1

    def test_provide_beverage(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        initial = service.get_quantity(ServiceType.BEVERAGE)
        result = service.provide_beverage("кофе")
        assert result["status"] == "provided"
        assert service.get_quantity(ServiceType.BEVERAGE) == initial - 1

    def test_assist_passenger(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        result = service.assist_passenger("general")
        assert result["status"] == "provided"

    def test_provide_wifi(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        result = service.provide_wifi("AB12345678")
        assert result["status"] == "connected"

    def test_out_of_stock_meal(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        # Используем всё питание
        for _ in range(100):
            try:
                service.provide_meal("meal")
            except ServiceError:
                break
        with pytest.raises(ServiceError):
            service.provide_meal("dinner")

    def test_restock(self):
        from aircraft_model import InFlightService
        service = InFlightService()
        initial = service.get_quantity(ServiceType.MEAL)
        service.restock(ServiceType.MEAL, 50)
        assert service.get_quantity(ServiceType.MEAL) == initial + 50


# ============================================================================
# ТЕСТЫ ДЛЯ ОБРАБОТКИ ИСКЛЮЧЕНИЙ
# ============================================================================

class TestExceptionHandling:
    """Тесты для обработки исключений."""

    def test_validation_error_message(self):
        with pytest.raises(ValidationError):
            Aircraft("", "RA-12345", 150)

    def test_registration_error(self):
        passenger = Passenger("Test", "AB12345678", "TKT-001", "1A")
        passenger.register_for_flight()
        with pytest.raises(RegistrationError):
            passenger.register_for_flight()

    def test_capacity_error(self):
        aircraft = Aircraft("Boeing 737", "RA-12345", 2)
        p1 = Passenger("Test1", "AB11111111", "TKT-001", "1A")
        p1.register_for_flight()
        p2 = Passenger("Test2", "AB22222222", "TKT-002", "1B")
        p2.register_for_flight()
        aircraft.add_passenger(p1)
        aircraft.add_passenger(p2)
        p3 = Passenger("Test3", "AB33333333", "TKT-003", "1C")
        p3.register_for_flight()
        with pytest.raises(CapacityError):
            aircraft.add_passenger(p3)


# ============================================================================
# ТЕСТЫ ДЛЯ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ ВВОДА
# ============================================================================

class TestInputHelpers:
    """Тесты для вспомогательных функций ввода."""

    def test_input_while_empty_valid(self):
        with patch('builtins.input', return_value='valid input'):
            from main import input_while_empty
            result = input_while_empty("Prompt: ")
            assert result == "valid input"

    def test_input_while_empty_retry_on_empty(self):
        from main import input_while_empty
        inputs = iter(['', '', 'valid'])
        with patch('builtins.input', side_effect=lambda p: next(inputs)):
            result = input_while_empty("Prompt: ")
            assert result == "valid"

    def test_input_while_not_number_valid(self):
        with patch('builtins.input', return_value='42'):
            from main import input_while_not_number
            result = input_while_not_number("Number: ")
            assert result == 42

    def test_input_while_not_number_float(self):
        with patch('builtins.input', return_value='3.14'):
            from main import input_while_not_number
            result = input_while_not_number("Number: ", is_float=True)
            assert result == 3.14

    def test_input_while_not_number_retry_on_invalid(self):
        from main import input_while_not_number
        inputs = iter(['abc', '', '42'])
        with patch('builtins.input', side_effect=lambda p: next(inputs)):
            result = input_while_not_number("Number: ")
            assert result == 42


# ============================================================================
# ТЕСТЫ ДЛЯ PRINT_MENU
# ============================================================================

class TestPrintMenu:
    """Тесты для функции print_menu."""

    def test_print_menu(self, capsys):
        from main import print_menu
        print_menu()
        captured = capsys.readouterr()
        assert "МЕНЮ" in captured.out
        assert "1. Создать самолёт" in captured.out
        assert "9. Загрузить демо-данные" in captured.out
        assert "0. Выход" in captured.out
        # Проверяем что нет пункта ВПП
        assert "ВПП" not in captured.out or "Состояние системы" in captured.out


# ============================================================================
# ЗАПУСК ТЕСТОВ
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
