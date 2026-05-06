"""Тесты для модуля main.py с CLI."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from aircraft_model.main import (
    SystemState, Flight, get_airport_distance,
    menu_create_aircraft, menu_add_crew_member, menu_create_flight,
    menu_register_passenger, menu_inflight_service,
    safe_input, input_while_empty, input_number
)
from aircraft_model import Aircraft, CrewMember, CrewRole, Passenger


class TestSystemState:
    """Тесты SystemState."""

    def test_singleton(self):
        state1 = SystemState()
        state2 = SystemState()
        assert state1 is state2

    def test_reset(self):
        state = SystemState()
        state.aircraft["TEST"] = MagicMock()
        state.reset()
        assert len(state.aircraft) == 0

    def test_is_tail_number_exists(self):
        state = SystemState()
        state.reset()
        ac = Aircraft("Test", "RA-TEST", 100)
        state.aircraft["RA-TEST"] = ac
        assert state.is_tail_number_exists("RA-TEST") is True
        assert state.is_tail_number_exists("RA-NONE") is False

    def test_get_aircraft(self):
        state = SystemState()
        state.reset()
        ac = Aircraft("Test", "RA-TEST", 100)
        state.aircraft["RA-TEST"] = ac
        assert state.get_aircraft("RA-TEST") == ac
        assert state.get_aircraft("NONE") is None


class TestFlight:
    """Тесты класса Flight."""

    def test_create_flight(self):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        assert flight.flight_number == "SU123"
        assert flight.departure == "SVO"
        assert flight.destination == "LED"

    def test_add_passenger(self):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        p = Passenger("Test", "PASS1234", "12A")
        flight.add_passenger(p)
        assert flight.get_passenger_count() == 1

    def test_is_seat_taken(self):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())
        p = Passenger("Test", "PASS1234", "12A")
        flight.add_passenger(p)
        assert flight.is_seat_taken("12A") is True
        assert flight.is_seat_taken("12B") is False


class TestHelperFunctions:
    """Тесты вспомогательных функций."""

    def test_get_airport_distance(self):
        dist = get_airport_distance("SVO", "LED")
        assert dist == 634.0

    def test_get_airport_distance_reverse(self):
        dist = get_airport_distance("LED", "SVO")
        assert dist == 634.0

    def test_get_airport_distance_default(self):
        dist = get_airport_distance("XXX", "YYY")
        assert dist == 800.0

    def test_safe_input_normal(self):
        with patch('builtins.input', return_value='test'):
            result = safe_input("prompt")
            assert result == "test"

    def test_safe_input_keyboard_interrupt(self):
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            result = safe_input("prompt")
            assert result is None

    def test_input_while_empty(self):
        with patch('builtins.input', side_effect=['', '  ', 'valid']):
            result = input_while_empty("prompt")
            assert result == "valid"

    def test_input_number(self):
        with patch('builtins.input', side_effect=['abc', '42']):
            result = input_number("prompt")
            assert result == 42


class TestMenuCreateAircraft:
    """Тесты menu_create_aircraft."""

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    @patch('aircraft_model.main.input_menu_choice')
    def test_create_aircraft_success(self, mock_choice, mock_input, mock_state):
        mock_state.is_tail_number_exists.return_value = False
        mock_choice.return_value = 1
        mock_input.return_value = "RA-12345"

        menu_create_aircraft()

        assert mock_state.aircraft.__setitem__.called

    @patch('aircraft_model.main.safe_input', return_value=None)
    def test_create_aircraft_cancel(self, mock_input):
        menu_create_aircraft()


class TestMenuAddCrewMember:
    """Тесты menu_add_crew_member."""

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    @patch('aircraft_model.main.input_menu_choice')
    @patch('aircraft_model.main.input_valid_fio')
    def test_add_crew_no_aircraft(self, mock_fio, mock_choice, mock_input, mock_state):
        mock_state.aircraft = {}
        menu_add_crew_member()

    @patch('aircraft_model.main.state')
    def test_add_crew_pilot_limit(self, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        pilot = CrewMember("Pilot", CrewRole.PILOT, "PLT001")
        ac.add_crew_member(pilot)
        mock_state.aircraft = {"RA-TEST": ac}
        mock_state.get_aircraft.return_value = ac

        with patch('aircraft_model.main.safe_input', side_effect=["RA-TEST", None]):
            with patch('aircraft_model.main.input_menu_choice', return_value=1):
                menu_add_crew_member()


class TestMenuCreateFlight:
    """Тесты menu_create_flight."""

    @patch('aircraft_model.main.state')
    def test_create_flight_no_aircraft(self, mock_state):
        mock_state.aircraft = {}
        menu_create_flight()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    @patch('aircraft_model.main.input_menu_choice')
    def test_create_flight_success(self, mock_choice, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        mock_state.aircraft = {"RA-TEST": ac}
        mock_state.get_aircraft.return_value = ac
        mock_state.get_flight_by_aircraft.return_value = None
        mock_state.is_flight_number_exists.return_value = False

        mock_input.side_effect = ["RA-TEST", "SU123"]
        mock_choice.side_effect = [1, 2]

        menu_create_flight()


class TestMenuRegisterPassenger:
    """Тесты menu_register_passenger."""

    @patch('aircraft_model.main.state')
    def test_register_no_flights(self, mock_state):
        mock_state.flights = {}
        menu_register_passenger()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    @patch('aircraft_model.main.input_valid_fio')
    @patch('aircraft_model.main.input_valid_passport')
    @patch('aircraft_model.main.input_until_valid_seat')
    def test_register_passenger_success(self, mock_seat, mock_passport, mock_fio, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())

        mock_state.flights = {"SU123": flight}
        mock_state.get_flight.return_value = flight
        mock_state.is_passport_exists.return_value = False
        mock_state.is_license_exists.return_value = False

        mock_input.return_value = "SU123"
        mock_fio.return_value = "Test User"
        mock_passport.return_value = "PASS1234"
        mock_seat.return_value = "12A"

        menu_register_passenger()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    @patch('aircraft_model.main.input_valid_fio')
    @patch('aircraft_model.main.input_valid_passport')
    def test_register_duplicate_passport(self, mock_passport, mock_fio, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        flight = Flight("SU123", ac, "SVO", "LED", datetime.now())

        mock_state.flights = {"SU123": flight}
        mock_state.get_flight.return_value = flight
        mock_state.is_passport_exists.return_value = True

        mock_input.return_value = "SU123"
        mock_fio.return_value = "Test User"
        mock_passport.return_value = "PASS1234"

        menu_register_passenger()


class TestMenuInflightService:
    """Тесты menu_inflight_service."""

    @patch('aircraft_model.main.state')
    def test_service_no_aircraft(self, mock_state):
        mock_state.aircraft = {}
        menu_inflight_service()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    def test_service_show_inventory(self, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        mock_state.aircraft = {"RA-TEST": ac}
        mock_state.get_aircraft.return_value = ac

        mock_input.side_effect = ["RA-TEST", ""]

        menu_inflight_service()

    @patch('aircraft_model.main.state')
    @patch('aircraft_model.main.safe_input')
    def test_service_provide_meal(self, mock_input, mock_state):
        ac = Aircraft("Test", "RA-TEST", 100)
        p = Passenger("Test", "PASS1234", "12A")
        p.register_for_flight()
        ac.add_passenger(p)

        mock_state.aircraft = {"RA-TEST": ac}
        mock_state.get_aircraft.return_value = ac
        mock_state.is_passport_exists.return_value = True
        mock_state.passengers = {"PASS1234": p}

        mock_input.side_effect = ["RA-TEST", "1", "PASS1234"]

        menu_inflight_service()
