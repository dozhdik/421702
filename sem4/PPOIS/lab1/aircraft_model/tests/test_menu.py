"""
Тесты для меню-функций main.py.
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
)


# ============================================================================
# ТЕСТЫ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ
# ============================================================================

class TestHelperFunctions:
    """Тесты вспомогательных функций."""

    @patch('builtins.input', return_value='test value')
    def test_safe_input_returns_value(self, mock_input):
        from main import safe_input
        result = safe_input("")
        assert result == "test value"

    @patch('builtins.input', return_value='   spaces   ')
    def test_safe_input_strips(self, mock_input):
        from main import safe_input
        result = safe_input("")
        assert result == "spaces"

    @patch('builtins.input', return_value='')
    def test_safe_input_empty(self, mock_input):
        from main import safe_input
        result = safe_input("")
        assert result == ""

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_safe_input_keyboard_interrupt(self, mock_input):
        from main import safe_input
        result = safe_input("")
        assert result is None

    @patch('builtins.input', return_value='42')
    def test_get_choice_returns_int(self, mock_input):
        from main import get_choice
        result = get_choice()
        assert result == 42

    @patch('builtins.input', return_value='')
    def test_get_choice_empty_returns_none(self, mock_input):
        from main import get_choice
        result = get_choice()
        assert result is None

    @patch('builtins.input', return_value='not a number')
    def test_get_choice_invalid_returns_none(self, mock_input):
        from main import get_choice
        result = get_choice()
        assert result is None

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_get_choice_keyboard_interrupt(self, mock_input):
        from main import get_choice
        result = get_choice()
        assert result is None


# ============================================================================
# ТЕСТЫ ВЫХОДНЫХ ФУНКЦИЙ
# ============================================================================

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
# ТЕСТЫ Airport
# ============================================================================

class TestAirportClass:
    """Тесты для класса Airport."""

    def test_all_returns_6_airports(self):
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


# ============================================================================
# ТЕСТЫ SystemState
# ============================================================================

class TestSystemStateHelpers:
    """Тесты SystemState."""

    def test_reset(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft['test'] = 'value'
        s.flights['test_flight'] = 'value'
        s.passengers['test_passenger'] = 'value'
        s.reset()
        assert s.aircraft == {}
        assert s.flights == {}
        assert s.passengers == {}

    def test_get_aircraft(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        aircraft = Aircraft("Boeing", "RA-12345", 150)
        s.aircraft["RA-12345"] = aircraft
        found = s.get_aircraft("RA-12345")
        assert found == aircraft
        found = s.get_aircraft("ra-12345")
        assert found == aircraft

    def test_get_aircraft_not_found(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        found = s.get_aircraft("NONEXISTENT")
        assert found is None

    def test_summary_empty(self, capsys):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.summary()
        captured = capsys.readouterr()
        assert "Самолёты: нет" in captured.out
        assert "Рейсы: нет" in captured.out


# ============================================================================
# ТЕСТЫ Flight
# ============================================================================

class TestFlightHelpers:
    """Тесты для класса Flight."""

    def test_flight_calculates_distance(self):
        from main import Flight
        aircraft = Aircraft("Boeing", "RA-12345", 150)
        flight = Flight(
            flight_number="SU123",
            aircraft=aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        assert flight.distance_km == 634.0

    def test_flight_adds_passenger(self):
        from main import Flight
        aircraft = Aircraft("Boeing", "RA-12345", 150)
        flight = Flight(
            flight_number="SU123",
            aircraft=aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        passenger = Passenger("Test", "TP12345678", "TKT-001", "1A")
        passenger.register_for_flight()
        flight.add_passenger(passenger)
        assert flight.get_passenger_count() == 1

    def test_flight_is_seat_taken(self):
        from main import Flight
        aircraft = Aircraft("Boeing", "RA-12345", 150)
        flight = Flight(
            flight_number="SU123",
            aircraft=aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        passenger = Passenger("Test", "TP12345678", "TKT-001", "1A")
        passenger.register_for_flight()
        flight.add_passenger(passenger)
        assert flight.is_seat_taken("1A") is True
        assert flight.is_seat_taken("2B") is False

    def test_flight_is_passenger_on_flight(self):
        from main import Flight
        aircraft = Aircraft("Boeing", "RA-12345", 150)
        flight = Flight(
            flight_number="SU123",
            aircraft=aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=24),
        )
        passenger = Passenger("Test", "TP12345678", "TKT-001", "1A")
        passenger.register_for_flight()
        flight.add_passenger(passenger)
        assert flight.is_passenger_on_flight("TP12345678") is True
        assert flight.is_passenger_on_flight("OTHER") is False


# ============================================================================
# ТЕСТЫ МЕНЮ СОСТОЯНИЯ
# ============================================================================

class TestMenuStateOutput:
    """Тесты вывода состояния через меню."""

    def test_show_empty_state(self, capsys):
        from main import menu_show_state, SystemState
        SystemState._instance = None
        SystemState()
        menu_show_state()
        captured = capsys.readouterr()
        assert "СОСТОЯНИЕ СИСТЕМЫ" in captured.out


# ============================================================================
# ТЕСТЫ МЕНЮ БЕЗОПАСНОСТИ
# ============================================================================

class TestMenuSafetyCheck:
    """Тесты проверки безопасности."""

    def test_safety_no_aircraft(self, capsys):
        from main import menu_safety_check, SystemState
        SystemState._instance = None
        SystemState()
        with patch('builtins.input', side_effect=[KeyboardInterrupt]):
            menu_safety_check()
        captured = capsys.readouterr()
        assert "Нет доступных самолётов" in captured.out


# ============================================================================
# ТЕСТЫ МЕНЮ СЕРВИСА
# ============================================================================

class TestMenuService:
    """Тесты меню сервиса."""

    def test_service_no_aircraft(self, capsys):
        from main import menu_inflight_service, SystemState
        SystemState._instance = None
        SystemState()
        with patch('builtins.input', side_effect=[KeyboardInterrupt]):
            menu_inflight_service()
        captured = capsys.readouterr()
        assert "Нет доступных самолётов" in captured.out


# ============================================================================
# ТЕСТЫ PRINT_MENU
# ============================================================================

class TestPrintMenu:
    """Тесты функции print_menu."""

    def test_print_menu(self, capsys):
        from main import print_menu
        print_menu()
        captured = capsys.readouterr()
        assert "МЕНЮ" in captured.out
        assert "1. Создать самолёт" in captured.out
        assert "2. Добавить члена экипажа" in captured.out
        assert "3. Выпустить рейс" in captured.out
        assert "4. Зарегистрировать пассажира на рейс" in captured.out
        assert "5. Запросить взлёт или посадку" in captured.out
        assert "6. Бортовое обслуживание" in captured.out
        assert "7. Проверка безопасности" in captured.out
        assert "8. Состояние системы" in captured.out
        assert "9. Загрузить демо-данные" in captured.out
        assert "0. Выход" in captured.out


# ============================================================================
# ЗАПУСК ТЕСТОВ
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
