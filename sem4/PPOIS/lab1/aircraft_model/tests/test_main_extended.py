"""Расширенные тесты для main.py."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from aircraft_model.main import (
    SystemState, Flight, get_airport_list,
    menu_takeoff_landing, menu_safety_check, menu_show_state, menu_load_demo,
    input_menu_choice, input_valid_fio, input_valid_passport, input_until_valid_seat,
    is_valid_fio, is_valid_passport
)
from aircraft_model import Aircraft, CrewMember, CrewRole, Passenger, AircraftStatus


class TestSystemStateExtended:
    """Расширенные тесты SystemState."""

    def test_is_passport_exists(self):
        state = SystemState()
        state.reset()
        p = Passenger("Test", "PASS1234", "12A")
        state.passengers["PASS1234"] = p
        assert state.is_passport_exists("PASS1234") is True
        assert state.is_passport_exists("NONE") is False

    def test_is_license_exists(self):
        state = SystemState()
        state.reset()
        cm = CrewMember("Test", CrewRole.PILOT, "PLT12345")
        state.crew_members["PLT12345"] = cm
        assert state.is_license_exists("PLT12345") is True
        assert state.is_license_exists("NONE") is False

    def test_is_flight_number_exists(self):
        state = SystemState()
        state.reset()
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        state.flights["SU123"] = flight
        assert state.is_flight_number_exists("SU123") is True
        assert state.is_flight_number_exists("NONE") is False

    def test_get_flight(self):
        state = SystemState()
        state.reset()
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        state.flights["SU123"] = flight
        assert state.get_flight("SU123") == flight
        assert state.get_flight("NONE") is None

    def test_get_flight_by_aircraft(self):
        state = SystemState()
        state.reset()
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        state.flights["SU123"] = flight
        assert state.get_flight_by_aircraft(ac) == flight

    def test_summary(self, capsys):
        state = SystemState()
        state.reset()
        state.summary()
        out = capsys.readouterr().out
        assert "Состояние системы" in out


class TestFlightExtended:
    """Расширенные тесты Flight."""

    def test_is_passenger_on_flight(self):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        p = Passenger("Test", "PASS1234", "12A")
        flight.add_passenger(p)
        assert flight.is_passenger_on_flight("PASS1234") is True
        assert flight.is_passenger_on_flight("NONE") is False

    def test_calculate_route(self):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        assert flight.distance_km > 0
        assert flight.fuel_needed > 0
        assert flight.duration_hours > 0


class TestValidationFunctions:
    """Тесты функций валидации."""

    def test_is_valid_fio(self):
        assert is_valid_fio("Иван Иванов") is True
        assert is_valid_fio("") is False
        assert is_valid_fio("AB") is False
        assert is_valid_fio("A" * 100) is False

    def test_is_valid_passport(self):
        assert is_valid_passport("PASS1234") is True
        assert is_valid_passport("") is False
        assert is_valid_passport("P1") is False
        assert is_valid_passport("P" * 20) is False
        assert is_valid_passport("PASS!234") is False


class TestInputFunctions:
    """Тесты функций ввода."""

    def test_input_menu_choice(self):
        with patch('builtins.input', side_effect=['abc', '0', '2']):
            result = input_menu_choice(3)
            assert result == 2

    def test_input_valid_fio(self):
        with patch('builtins.input', side_effect=['', 'AB', 'Иван Иванов']):
            result = input_valid_fio("prompt")
            assert result == "Иван Иванов"

    def test_input_valid_passport(self):
        with patch('builtins.input', side_effect=['', 'P1', 'PASS1234']):
            result = input_valid_passport("prompt")
            assert result == "PASS1234"

    def test_input_until_valid_seat(self):
        with patch('builtins.input', side_effect=['', '1', '12A']):
            result = input_until_valid_seat("prompt", set(), 150)
            assert result == "12A"


class TestMenuTakeoffLanding:
    """Тесты menu_takeoff_landing."""

    @patch('aircraft_model.main.state')
    def test_no_aircraft(self, mock_state):
        mock_state.aircraft = {}
        with patch('aircraft_model.main.safe_input', return_value="1"):
            menu_takeoff_landing()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    def test_takeoff_success(self, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        pilot = CrewMember("Pilot", CrewRole.PILOT, "PLT001")
        copilot = CrewMember("CoPilot", CrewRole.CO_PILOT, "CPT001")
        fa1 = CrewMember("FA1", CrewRole.FLIGHT_ATTENDANT, "FA001")
        fa2 = CrewMember("FA2", CrewRole.FLIGHT_ATTENDANT, "FA002")

        pilot.start_duty()
        copilot.start_duty()
        fa1.start_duty()
        fa2.start_duty()

        ac.add_crew_member(pilot)
        ac.add_crew_member(copilot)
        ac.add_crew_member(fa1)
        ac.add_crew_member(fa2)

        p = Passenger("Test", "PASS1234", "12A")
        p.register_for_flight()
        ac.add_passenger(p)

        from aircraft_model import FlightRoute
        route = FlightRoute("SVO", "LED", 634.0)
        ac.set_route(route)

        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())

        mock_state.aircraft = {"RA-TEST": ac}
        mock_state.get_aircraft.return_value = ac
        mock_state.get_flight_by_aircraft.return_value = flight

        mock_input.side_effect = ["1", "RA-TEST"]

        menu_takeoff_landing()


class TestMenuSafetyCheck:
    """Тесты menu_safety_check."""

    @patch('aircraft_model.main.state')
    def test_no_aircraft(self, mock_state):
        mock_state.aircraft = {}
        menu_safety_check()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    def test_safety_check(self, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        mock_state.aircraft = {"RA-TEST": ac}
        mock_state.get_aircraft.return_value = ac
        mock_input.return_value = "RA-TEST"

        menu_safety_check()


class TestMenuShowState:
    """Тесты menu_show_state."""

    @patch('aircraft_model.main.state')
    def test_show_state(self, mock_state):
        mock_state.summary = MagicMock()
        menu_show_state()
        assert mock_state.summary.called


class TestMenuLoadDemo:
    """Тесты menu_load_demo."""

    @patch('aircraft_model.main.state')
    def test_load_demo(self, mock_state):
        mock_state.reset = MagicMock()
        mock_state.aircraft = {}
        mock_state.flights = {}
        mock_state.passengers = {}

        menu_load_demo()


class TestGetAirportList:
    """Тесты get_airport_list."""

    def test_get_airport_list(self):
        airports = get_airport_list()
        assert len(airports) > 0
        assert "SVO" in airports
