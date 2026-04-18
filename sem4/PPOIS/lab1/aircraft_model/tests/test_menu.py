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

from aircraft_model import (
    Aircraft,
    AircraftStatus,
    CrewMember,
    CrewRole,
    FlightRoute,
    Passenger,
    Runway,
)


class TestOutputFunctions:
    """Тесты выходных функций."""

    def test_header(self, capsys):
        """Header выводит текст."""
        from main import header
        header("TEST")
        captured = capsys.readouterr()
        assert "--- TEST ---" in captured.out

    def test_info(self, capsys):
        """Info выводит с префиксом."""
        from main import info
        info("test")
        captured = capsys.readouterr()
        assert "[INFO] test" in captured.out

    def test_success(self, capsys):
        """Success выводит с префиксом."""
        from main import success
        success("ok")
        captured = capsys.readouterr()
        assert "[OK] ok" in captured.out

    def test_warning(self, capsys):
        """Warning выводит с префиксом."""
        from main import warning
        warning("warn")
        captured = capsys.readouterr()
        assert "[WARN] warn" in captured.out

    def test_error(self, capsys):
        """Error выводит с префиксом."""
        from main import error
        error("err")
        captured = capsys.readouterr()
        assert "[ERROR] err" in captured.out

    def test_step(self, capsys):
        """Step выводит с номером."""
        from main import step
        step(1, "desc")
        captured = capsys.readouterr()
        assert "[STEP 1] desc" in captured.out


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


class TestPrintMenu:
    """Тесты функции print_menu."""

    def test_print_menu(self, capsys):
        from main import print_menu
        print_menu()
        captured = capsys.readouterr()
        assert "МЕНЮ" in captured.out
        assert "1. Создать самолёт" in captured.out
        assert "0. Выход" in captured.out


class TestSystemStateHelpers:
    """Тесты SystemState."""

    def test_reset(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft['test'] = 'value'
        s.reset()
        assert s.aircraft == {}
        assert s.runways == {}
        assert s.passengers == {}

    def test_get_aircraft(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        aircraft = Aircraft("Boeing", "RA-12345", 150)
        s.aircraft["RA-12345"] = aircraft

        # По ключу
        found = s.get_aircraft("RA-12345")
        assert found == aircraft

        # По бортовому номеру
        found = s.get_aircraft("ra-12345")
        assert found == aircraft

        # Не найден
        found = s.get_aircraft("NONEXISTENT")
        assert found is None

    def test_get_runway(self):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        runway = Runway("RWY-01", 3000)
        s.runways["RWY-01"] = runway

        found = s.get_runway("RWY-01")
        assert found == runway

        found = s.get_runway("nonexistent")
        assert found is None

    def test_summary_empty(self, capsys):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.summary()
        captured = capsys.readouterr()
        assert "Самолёты: нет" in captured.out
        assert "ВПП: нет" in captured.out

    def test_summary_with_data(self, capsys):
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft["RA-001"] = Aircraft("Boeing", "RA-001", 150)
        s.runways["RWY-01"] = Runway("RWY-01", 3000)
        s.passengers["PP12345678"] = Passenger("Test", "PP12345678", "TKT", "1A")
        s.crew_members["LIC001"] = CrewMember("Test", CrewRole.PILOT, "LIC001")
        s.routes["SVO-LED"] = FlightRoute("SVO", "LED", 650)

        s.summary()
        captured = capsys.readouterr()
        assert "RA-001" in captured.out
        assert "RWY-01" in captured.out
        assert "Test" in captured.out
        assert "SVO-LED" in captured.out


class TestMenuStateOutput:
    """Тесты вывода состояния через меню."""

    def test_show_empty_state(self, capsys):
        from main import menu_show_state, SystemState
        SystemState._instance = None
        state = SystemState()

        menu_show_state()
        captured = capsys.readouterr()
        assert "СОСТОЯНИЕ СИСТЕМЫ" in captured.out


class TestMenuSafetyCheck:
    """Тесты проверки безопасности."""

    def test_safety_no_aircraft(self, capsys):
        from main import menu_safety_check, SystemState
        SystemState._instance = None
        state = SystemState()

        with patch('builtins.input', side_effect=[KeyboardInterrupt]):
            menu_safety_check()

        captured = capsys.readouterr()
        assert "Нет доступных самолётов" in captured.out


class TestMenuTakeoff:
    """Тесты меню взлёта."""

    def test_takeoff_no_aircraft(self, capsys):
        from main import menu_takeoff_landing, SystemState
        SystemState._instance = None
        state = SystemState()

        with patch('builtins.input', side_effect=['1', KeyboardInterrupt]):
            menu_takeoff_landing()

        captured = capsys.readouterr()
        assert "Нет доступных самолётов" in captured.out


class TestMenuService:
    """Тесты меню сервиса."""

    def test_service_no_aircraft(self, capsys):
        from main import menu_inflight_service, SystemState
        SystemState._instance = None
        state = SystemState()

        with patch('builtins.input', side_effect=[KeyboardInterrupt]):
            menu_inflight_service()

        captured = capsys.readouterr()
        assert "Нет доступных самолётов" in captured.out


class TestMenuRoute:
    """Тесты меню маршрута."""

    @patch('builtins.input', side_effect=['SVO', 'LED', '650', '', KeyboardInterrupt])
    def test_plan_route(self, mock_input, capsys):
        from main import menu_plan_route, SystemState
        SystemState._instance = None
        state = SystemState()

        menu_plan_route()
        captured = capsys.readouterr()
        assert "SVO -> LED" in captured.out or "SVO-LED" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])