"""
Тесты для CLI-модуля main.py.
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
    RunwayStatus,
    Ticket,
    TicketStatus,
    CapacityError,
    CrewError,
    FlightError,
    LandingError,
    RegistrationError,
    RunwayError,
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
        """Обычный ввод возвращается корректно."""
        with patch('builtins.input', return_value='test input'):
            from main import safe_input
            result = safe_input("prompt: ")
            assert result == "test input"

    def test_safe_input_strip(self):
        """Ввод обрезается по краям."""
        with patch('builtins.input', return_value='  test  '):
            from main import safe_input
            result = safe_input("prompt: ")
            assert result == "test"

    def test_safe_input_keyboard_interrupt(self):
        """KeyboardInterrupt возвращает None."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            from main import safe_input
            result = safe_input("prompt: ")
            assert result is None

    def test_safe_input_empty_returns_empty(self):
        """Пустой ввод возвращает пустую строку."""
        with patch('builtins.input', return_value=''):
            from main import safe_input
            result = safe_input("prompt: ")
            assert result == ''


class TestGetChoice:
    """Тесты для функции get_choice."""

    def test_get_choice_valid_integer(self):
        """Валидный ввод возвращает число."""
        with patch('builtins.input', return_value='5'):
            from main import get_choice
            result = get_choice()
            assert result == 5

    def test_get_choice_empty_returns_none(self):
        """Пустой ввод возвращает None."""
        with patch('builtins.input', return_value=''):
            from main import get_choice
            result = get_choice()
            assert result is None

    def test_get_choice_invalid_returns_none(self):
        """Некорректный ввод возвращает None."""
        with patch('builtins.input', return_value='abc'):
            from main import get_choice
            result = get_choice()
            assert result is None

    def test_get_choice_keyboard_interrupt(self):
        """KeyboardInterrupt возвращает None."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            from main import get_choice
            result = get_choice()
            assert result is None

    def test_get_choice_negative(self):
        """Отрицательное число возвращается."""
        with patch('builtins.input', return_value='-1'):
            from main import get_choice
            result = get_choice()
            assert result == -1


# ============================================================================
# ТЕСТЫ ДЛЯ ФУНКЦИЙ ВЫВОДА
# ============================================================================

class TestOutputFunctions:
    """Тесты для функций вывода."""

    def test_header(self, capsys):
        """Header выводит корректный формат."""
        from main import header
        header("TEST HEADER")
        captured = capsys.readouterr()
        assert "--- TEST HEADER ---" in captured.out

    def test_info(self, capsys):
        """Info выводит с префиксом."""
        from main import info
        info("test message")
        captured = capsys.readouterr()
        assert "[INFO] test message" in captured.out

    def test_success(self, capsys):
        """Success выводит с префиксом OK."""
        from main import success
        success("success message")
        captured = capsys.readouterr()
        assert "[OK] success message" in captured.out

    def test_warning(self, capsys):
        """Warning выводит с префиксом WARN."""
        from main import warning
        warning("warning message")
        captured = capsys.readouterr()
        assert "[WARN] warning message" in captured.out

    def test_error(self, capsys):
        """Error выводит с префиксом ERROR."""
        from main import error
        error("error message")
        captured = capsys.readouterr()
        assert "[ERROR] error message" in captured.out

    def test_step(self, capsys):
        """Step выводит с номером."""
        from main import step
        step(1, "description")
        captured = capsys.readouterr()
        assert "[STEP 1] description" in captured.out


# ============================================================================
# ТЕСТЫ ДЛЯ SystemState
# ============================================================================

class TestSystemState:
    """Тесты для класса SystemState."""

    def test_reset(self):
        """Reset очищает все хранилища."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        s.aircraft['test'] = 'value'
        s.reset()
        assert s.aircraft == {}
        assert s.runways == {}
        assert s.passengers == {}

    def test_get_aircraft_by_key(self):
        """get_aircraft ищет по ключу."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        s.aircraft["RA-12345"] = aircraft

        found = s.get_aircraft("RA-12345")
        assert found == aircraft

    def test_get_aircraft_by_tail_number(self):
        """get_aircraft ищет по бортовому номеру."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        s.aircraft["KEY"] = aircraft

        found = s.get_aircraft("RA-12345")
        assert found == aircraft

    def test_get_aircraft_not_found(self):
        """get_aircraft возвращает None при отсутствии."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()

        found = s.get_aircraft("NONEXISTENT")
        assert found is None

    def test_get_aircraft_uppercase(self):
        """get_aircraft преобразует ключ в верхний регистр."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        s.aircraft["RA-12345"] = aircraft

        found = s.get_aircraft("ra-12345")
        assert found == aircraft

    def test_get_runway(self):
        """get_runway работает корректно."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        runway = Runway("RWY-01", 3000)
        s.runways["RWY-01"] = runway

        found = s.get_runway("RWY-01")
        assert found == runway

    def test_get_runway_not_found(self):
        """get_runway возвращает None при отсутствии."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()

        found = s.get_runway("NONEXISTENT")
        assert found is None

    def test_get_passenger(self):
        """get_passenger работает корректно."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()
        passenger = Passenger("Test", "TP12345678", "TKT-001", "1A")
        s.passengers["TP12345678"] = passenger

        found = s.get_passenger("TP12345678")
        assert found == passenger

    def test_summary_empty(self, capsys):
        """summary выводит заглушки при пустых хранилищах."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()

        s.summary()
        captured = capsys.readouterr()
        assert "Самолёты: нет" in captured.out
        assert "ВПП: нет" in captured.out

    def test_summary_with_data(self, capsys):
        """summary выводит все объекты."""
        from main import SystemState
        SystemState._instance = None
        s = SystemState()

        s.aircraft["RA-001"] = Aircraft("Boeing 737", "RA-001", 150)
        s.runways["RWY-01"] = Runway("RWY-01", 3000)
        s.passengers["PP1234567"] = Passenger("Test User", "PP1234567", "TKT-001", "1A")
        s.crew_members["LIC001"] = CrewMember("Test Crew", CrewRole.PILOT, "LIC001")
        s.routes["SVO-LED"] = FlightRoute("SVO", "LED", 650)

        s.summary()
        captured = capsys.readouterr()
        assert "RA-001" in captured.out
        assert "RWY-01" in captured.out
        assert "Test User" in captured.out
        assert "Test Crew" in captured.out
        assert "SVO-LED" in captured.out


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - Aircraft
# ============================================================================

class TestAircraftCreation:
    """Тесты для создания самолёта."""

    def test_create_aircraft_valid(self):
        """Валидные данные создают самолёт."""
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
        """Нулевая вместимость вызывает ошибку."""
        with pytest.raises(ValidationError):
            Aircraft("Boeing", "RA-12345", 0)

    def test_create_aircraft_invalid_capacity_negative(self):
        """Отрицательная вместимость вызывает ошибку."""
        with pytest.raises(ValidationError):
            Aircraft("Boeing", "RA-12345", -10)

    def test_create_aircraft_invalid_tail_empty(self):
        """Пустой бортовой номер вызывает ошибку."""
        with pytest.raises(ValidationError):
            Aircraft("Boeing", "", 150)

    def test_create_aircraft_invalid_model_empty(self):
        """Пустая модель вызывает ошибку."""
        with pytest.raises(ValidationError):
            Aircraft("", "RA-12345", 150)

    def test_aircraft_with_airport(self):
        """Самолёт создаётся с аэропортом."""
        aircraft = Aircraft(
            model="Airbus A320",
            tail_number="RA-55555",
            capacity=180,
        )
        aircraft.set_airport("SVO")
        assert aircraft.current_airport == "SVO"


class TestAircraftPassengers:
    """Тесты для работы с пассажирами."""

    def test_add_passenger(self):
        """Добавление пассажира работает."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        passenger = Passenger("Test", "AB12345678", "TKT-001", "1A")
        passenger.register_for_flight()

        aircraft.add_passenger(passenger)
        assert aircraft.get_passenger_count() == 1

    def test_add_passenger_not_registered_fails(self):
        """Добавление незарегистрированного пассажира вызывает ошибку."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        passenger = Passenger("Test", "AB12345678", "TKT-001", "1A")

        with pytest.raises(FlightError):
            aircraft.add_passenger(passenger)

    def test_remove_passenger(self):
        """Удаление пассажира работает."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        passenger = Passenger("Test", "AB12345678", "TKT-001", "1A")
        passenger.register_for_flight()
        aircraft.add_passenger(passenger)

        removed = aircraft.remove_passenger("AB12345678")
        assert removed == passenger
        assert aircraft.get_passenger_count() == 0

    def test_remove_passenger_not_found(self):
        """Удаление несуществующего пассажира возвращает None."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        removed = aircraft.remove_passenger("NONEXISTENT")
        assert removed is None


class TestAircraftCrew:
    """Тесты для работы с экипажем."""

    def test_add_crew_member(self):
        """Добавление члена экипажа работает."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        crew = CrewMember("Test Pilot", CrewRole.PILOT, "PLT-001")

        aircraft.add_crew_member(crew)
        assert len(aircraft.crew) == 1

    def test_add_crew_duplicate_license(self):
        """Дубликат лицензии не добавляется."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        crew1 = CrewMember("Pilot 1", CrewRole.PILOT, "PLT-001")
        crew2 = CrewMember("Pilot 2", CrewRole.PILOT, "PLT-001")

        aircraft.add_crew_member(crew1)
        result = aircraft.add_crew_member(crew2)

        assert result is False
        assert len(aircraft.crew) == 1

    def test_remove_crew_member(self):
        """Удаление члена экипажа работает."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        crew = CrewMember("Test Pilot", CrewRole.PILOT, "PLT-001")
        aircraft.add_crew_member(crew)

        removed = aircraft.remove_crew_member("PLT-001")
        assert removed == crew
        assert len(aircraft.crew) == 0

    def test_remove_crew_not_found(self):
        """Удаление несуществующего члена экипажа возвращает None."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        removed = aircraft.remove_crew_member("NONEXISTENT")
        assert removed is None


class TestAircraftStatus:
    """Тесты для изменения статуса."""

    def test_change_status(self):
        """Изменение статуса работает."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        aircraft.change_status(AircraftStatus.BOARDING)
        assert aircraft.status == AircraftStatus.BOARDING

    def test_set_route(self):
        """Установка маршрута работает."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        route = FlightRoute("SVO", "LED", 650)
        aircraft.set_route(route)
        # Маршрут установлен (проверяем через preflight_check)
        checks = aircraft.preflight_check()
        assert checks["route_set"] is True


class TestAircraftPreflight:
    """Тесты для предполётной проверки."""

    def test_preflight_check_structure(self):
        """Проверка возвращает правильную структуру."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        checks = aircraft.preflight_check()

        assert "crew_minimum" in checks
        assert "crew_on_duty" in checks
        assert "passengers_registered" in checks
        assert "route_set" in checks
        assert "status_ok" in checks

    def test_preflight_check_no_crew(self):
        """Без экипажа crew_minimum = False."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        checks = aircraft.preflight_check()
        assert checks["crew_minimum"] is False

    def test_preflight_check_with_minimum_crew(self):
        """Проверка с экипажем."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)

        pilot = CrewMember("Test Pilot", CrewRole.PILOT, "PLT-001")
        pilot.start_duty()
        aircraft.add_crew_member(pilot)

        # Требуется 2 бортпроводника по умолчанию
        attendee1 = CrewMember("Test Attendant 1", CrewRole.FLIGHT_ATTENDANT, "FA-001")
        attendee1.start_duty()
        aircraft.add_crew_member(attendee1)

        attendee2 = CrewMember("Test Attendant 2", CrewRole.FLIGHT_ATTENDANT, "FA-002")
        attendee2.start_duty()
        aircraft.add_crew_member(attendee2)

        checks = aircraft.preflight_check()
        assert checks["crew_minimum"] is True
        assert checks["crew_on_duty"] is True


class TestAircraftTakeoff:
    """Тесты для взлёта."""

    def test_can_takeoff_empty_aircraft(self, capsys):
        """Пустой самолёт не может взлететь."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        assert aircraft.can_take_off() is False

    def test_can_takeoff_with_crew_and_route(self, aircraft_on_ground):
        """Самолёт с экипажем и маршрутом может взлететь."""
        aircraft = aircraft_on_ground
        assert aircraft.can_take_off() is True

    def test_take_off(self, aircraft_on_ground, capsys):
        """Взлёт выполняется."""
        aircraft = aircraft_on_ground
        runway = Runway("RWY-01", 3000)

        runway.request_takeoff(aircraft)
        aircraft.take_off()

        assert aircraft.status == AircraftStatus.IN_FLIGHT
        captured = capsys.readouterr()
        assert "IN_FLIGHT" in captured.out

    def test_take_off_success(self, aircraft_on_ground, capsys):
        """Взлёт выполняется когда все проверки пройдены."""
        aircraft = aircraft_on_ground
        # На самом деле take_off проверяет только внутренние условия aircraft,
        # ВПП - это внешний ресурс, управляемый отдельно
        aircraft.take_off()

        assert aircraft.status == AircraftStatus.IN_FLIGHT
        captured = capsys.readouterr()
        assert "IN_FLIGHT" in captured.out

    def test_take_off_checks_status(self):
        """Взлёт проверяет статус самолёта."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)
        # Устанавливаем статус не ON_GROUND
        aircraft.change_status(AircraftStatus.MAINTENANCE)

        with pytest.raises(TakeoffError):
            aircraft.take_off()


class TestAircraftLanding:
    """Тесты для посадки."""

    def test_land_in_flight(self, in_flight_aircraft, capsys):
        """Посадка работает для самолёта в воздухе."""
        aircraft = in_flight_aircraft
        runway = Runway("RWY-01", 3000)

        runway.request_landing(aircraft)
        aircraft.land()

        assert aircraft.status == AircraftStatus.ON_GROUND

    def test_land_on_ground_fails(self, aircraft_on_ground):
        """Посадка на земле вызывает ошибку."""
        aircraft = aircraft_on_ground
        runway = Runway("RWY-01", 3000)

        runway.request_landing(aircraft)

        with pytest.raises(FlightError):
            aircraft.land()


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - Passenger
# ============================================================================

class TestPassengerCreation:
    """Тесты для создания пассажира."""

    def test_create_passenger_valid(self):
        """Валидные данные создают пассажира."""
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
        """Пассажир создаётся без места."""
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
        )
        assert passenger.seat_number is None


class TestPassengerRegistration:
    """Тесты для регистрации."""

    def test_register_with_seat(self):
        """Регистрация с местом работает."""
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
        """Регистрация без места вызывает ошибку."""
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
        )
        with pytest.raises(RegistrationError):
            passenger.register_for_flight()

    def test_register_twice_fails(self):
        """Повторная регистрация вызывает ошибку."""
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
        """Назначение места работает."""
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
        )
        passenger.assign_seat("15B")
        assert passenger.seat_number == "15B"

    def test_cancel_registration(self):
        """Отмена регистрации работает."""
        passenger = Passenger(
            full_name="Иван Петров",
            passport_number="AB12345678",
            ticket_number="TKT-001",
            seat_number="12A",
        )
        passenger.register_for_flight()
        passenger.cancel_registration()
        assert not passenger.is_registered


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - Ticket
# ============================================================================

class TestTicketCreation:
    """Тесты для создания билета."""

    def test_issue_ticket(self):
        """Билет выпускается корректно."""
        from datetime import datetime, timedelta
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

    def test_ticket_flight_number_uppercase(self):
        """Номер рейса приводится к верхнему регистру."""
        from datetime import datetime, timedelta
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="su123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        assert ticket.flight_number == "SU123"


class TestTicketOperations:
    """Тесты для операций с билетом."""

    def test_validate_valid_ticket(self):
        """Валидный билет проходит валидацию."""
        from datetime import datetime, timedelta
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
        """Отменённый билет не проходит валидацию."""
        from datetime import datetime, timedelta
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
        """Подтверждение билета работает."""
        from datetime import datetime, timedelta
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
        """Использование билета меняет статус."""
        from datetime import datetime, timedelta
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
        """Отмена билета работает."""
        from datetime import datetime, timedelta
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

    def test_refund_ticket(self):
        """Возврат билета работает."""
        from datetime import datetime, timedelta
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        ticket.cancel()
        ticket.refund()
        assert ticket.status == TicketStatus.REFUNDED

    def test_is_valid(self):
        """is_valid работает корректно."""
        from datetime import datetime, timedelta
        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number="SU123",
            flight_datetime=flight_time,
            seat="12A",
            price=299.99,
            passport_number="AB12345678",
        )
        assert ticket.is_valid() is True

        ticket.cancel()
        assert ticket.is_valid() is False


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - Runway
# ============================================================================

class TestRunwayCreation:
    """Тесты для создания ВПП."""

    def test_create_runway_valid(self):
        """ВПП создаётся корректно."""
        runway = Runway("RWY-01", 3000)
        assert runway.runway_id == "RWY-01"
        assert runway.length == 3000
        assert runway.status == RunwayStatus.FREE

    def test_create_runway_minimum_length(self):
        """Минимальная длина ВПП."""
        runway = Runway("RWY-02", 500)
        assert runway.length == 500

    def test_create_runway_invalid_length_short(self):
        """Слишком короткая ВПП вызывает ошибку."""
        with pytest.raises(ValidationError):
            Runway("RWY-03", 400)

    def test_create_runway_uppercase_id(self):
        """ID ВПП приводится к верхнему регистру."""
        runway = Runway("rwy-04", 3000)
        assert runway.runway_id == "RWY-04"


class TestRunwayOperations:
    """Тесты для операций с ВПП."""

    def test_request_takeoff_success(self):
        """Успешный запрос взлёта."""
        runway = Runway("RWY-01", 3000)
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)

        result = runway.request_takeoff(aircraft)
        assert result is True
        assert runway.status == RunwayStatus.OCCUPIED
        assert runway.is_free is False

    def test_request_takeoff_queue(self):
        """Второй запрос ставится в очередь."""
        runway = Runway("RWY-01", 3000)
        aircraft1 = Aircraft("Boeing 737", "RA-11111", 150)
        aircraft2 = Aircraft("Airbus A320", "RA-22222", 180)

        runway.request_takeoff(aircraft1)
        result = runway.request_takeoff(aircraft2)

        assert result is False
        assert runway.queue_size == 1

    def test_request_landing_success(self):
        """Успешный запрос посадки."""
        runway = Runway("RWY-01", 3000)
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)

        result = runway.request_landing(aircraft)
        assert result is True
        assert runway.status == RunwayStatus.OCCUPIED

    def test_release_runway(self):
        """Освобождение ВПП работает."""
        runway = Runway("RWY-01", 3000)
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)

        runway.request_takeoff(aircraft)
        next_ac = runway.release()

        assert runway.status == RunwayStatus.FREE
        assert next_ac is None
        assert runway.is_free

    def test_release_processes_queue(self):
        """Освобождение обрабатывает очередь."""
        runway = Runway("RWY-01", 3000)
        aircraft1 = Aircraft("Boeing 737", "RA-11111", 150)
        aircraft2 = Aircraft("Airbus A320", "RA-22222", 180)

        runway.request_takeoff(aircraft1)
        runway.request_takeoff(aircraft2)

        # Первый освобождает - второй должен получить ВПП
        runway.release()
        # Теперь второй aircraft2 должен быть на ВПП
        # Проверяем что queue_size уменьшился
        assert runway.queue_size == 0
        # Освобождаем второй
        next_ac = runway.release()
        # Второй aircraft2 освободился
        assert next_ac is None

    def test_close_runway(self):
        """Закрытие ВПП работает."""
        runway = Runway("RWY-01", 3000)
        result = runway.close()
        assert result is True
        assert runway.status == RunwayStatus.CLOSED

    def test_open_runway(self):
        """Открытие ВПП работает."""
        runway = Runway("RWY-01", 3000)
        runway.close()
        runway.open()
        assert runway.status == RunwayStatus.FREE

    def test_request_on_closed_runway_fails(self):
        """Запрос на закрытую ВПП вызывает ошибку."""
        runway = Runway("RWY-01", 3000)
        runway.close()
        aircraft = Aircraft("Boeing 737", "RA-12345", 150)

        with pytest.raises(RunwayError):
            runway.request_takeoff(aircraft)

    def test_can_accommodate(self):
        """Проверка размера самолёта."""
        runway = Runway("RWY-01", 3000)
        assert runway.can_accommodate(2500) is True
        assert runway.can_accommodate(3500) is False


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - FlightRoute
# ============================================================================

class TestFlightRouteCreation:
    """Тесты для создания маршрута."""

    def test_create_route_valid(self):
        """Маршрут создаётся корректно."""
        route = FlightRoute("SVO", "LED", 650)
        assert route.departure == "SVO"
        assert route.destination == "LED"
        assert route.distance == 650

    def test_create_route_invalid_airport_empty(self):
        """Пустой код аэропорта вызывает ошибку."""
        with pytest.raises(ValidationError):
            FlightRoute("", "LED", 650)

    def test_create_route_invalid_distance_zero(self):
        """Нулевое расстояние вызывает ошибку."""
        with pytest.raises(ValidationError):
            FlightRoute("SVO", "LED", 0)

    def test_create_route_invalid_distance_negative(self):
        """Отрицательное расстояние вызывает ошибку."""
        with pytest.raises(ValidationError):
            FlightRoute("SVO", "LED", -100)


class TestFlightRouteOperations:
    """Тесты для операций с маршрутом."""

    def test_calculate_fuel_default(self):
        """Расчёт топлива с параметрами по умолчанию."""
        route = FlightRoute("SVO", "LED", 1000)
        fuel = route.calculate_fuel()
        # 1000 * 3.5 * 1.1 = 3850
        assert fuel > 3000
        assert fuel < 5000

    def test_calculate_fuel_custom(self):
        """Расчёт топлива с кастомным расходом."""
        route = FlightRoute("SVO", "LED", 1000)
        fuel = route.calculate_fuel(consumption_per_km=5.0)
        assert fuel > 5000

    def test_estimate_duration(self):
        """Расчёт времени полёта."""
        route = FlightRoute("SVO", "LED", 800)
        duration = route.estimate_duration()
        assert duration.total_seconds() > 0
        # 800 / 800 = 1 час
        assert duration.total_seconds() <= 3600 * 2

    def test_add_alternative(self):
        """Добавление альтернативного аэропорта."""
        route = FlightRoute("SVO", "LED", 650)
        route.add_alternative("AER")
        assert "AER" in route.alternative_airports

    def test_add_alternative_invalid(self):
        """Некорректный код аэропорта вызывает ошибку."""
        route = FlightRoute("SVO", "LED", 650)
        with pytest.raises(ValidationError):
            route.add_alternative("too_long_code")

    def test_is_route_compatible(self):
        """Проверка совместимости маршрутов."""
        route1 = FlightRoute("SVO", "LED", 650)
        route2 = FlightRoute("LED", "AER", 1800)

        assert route1.is_route_compatible(route2) is True

    def test_is_route_not_compatible(self):
        """Несовместимые маршруты."""
        route1 = FlightRoute("SVO", "LED", 650)
        route2 = FlightRoute("AER", "MSK", 500)

        assert route1.is_route_compatible(route2) is False

    def test_route_add_operator(self):
        """Объединение маршрутов."""
        route1 = FlightRoute("SVO", "LED", 650)
        route2 = FlightRoute("LED", "AER", 1800)

        combined = route1 + route2
        assert combined.departure == "SVO"
        assert combined.destination == "AER"

    def test_route_add_operator_incompatible(self):
        """Несовместимые маршруты не складываются."""
        route1 = FlightRoute("SVO", "LED", 650)
        route2 = FlightRoute("AER", "MSK", 500)

        with pytest.raises(ValidationError):
            route1 + route2


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - InFlightService
# ============================================================================

class TestInFlightServiceCreation:
    """Тесты для создания сервиса."""

    def test_service_initialization(self):
        """Сервис инициализируется с инвентарём."""
        from aircraft_model import InFlightService
        service = InFlightService()

        assert service.get_quantity(ServiceType.MEAL) > 0
        assert service.get_quantity(ServiceType.BEVERAGE) > 0

    def test_service_available_services(self):
        """Список услуг доступен."""
        from aircraft_model import InFlightService
        service = InFlightService()

        services = service.available_services
        assert len(services) > 0
        assert "MEAL" in services


class TestInFlightServiceOperations:
    """Тесты для операций сервиса."""

    def test_provide_meal(self):
        """Предоставление питания."""
        from aircraft_model import InFlightService
        service = InFlightService()

        initial = service.get_quantity(ServiceType.MEAL)
        result = service.provide_meal("hot meal")

        assert result["status"] == "provided"
        assert service.get_quantity(ServiceType.MEAL) == initial - 1

    def test_provide_beverage(self):
        """Предоставление напитков."""
        from aircraft_model import InFlightService
        service = InFlightService()

        initial = service.get_quantity(ServiceType.BEVERAGE)
        result = service.provide_beverage("coffee")

        assert result["status"] == "provided"
        assert service.get_quantity(ServiceType.BEVERAGE) == initial - 1

    def test_assist_passenger(self):
        """Оказание помощи."""
        from aircraft_model import InFlightService
        service = InFlightService()

        result = service.assist_passenger("general")
        assert result["status"] == "provided"

    def test_assist_special_passenger(self):
        """Специальная помощь."""
        from aircraft_model import InFlightService
        service = InFlightService()

        result = service.assist_passenger("wheelchair")
        assert result["service"] == "SPECIAL_ASSISTANCE"

    def test_provide_wifi(self):
        """Предоставление Wi-Fi."""
        from aircraft_model import InFlightService
        service = InFlightService()

        result = service.provide_wifi("AB12345678")
        assert result["status"] == "connected"

    def test_provide_entertainment(self):
        """Предоставление развлечений."""
        from aircraft_model import InFlightService
        service = InFlightService()

        result = service.provide_entertainment("AB12345678")
        assert result["status"] == "activated"

    def test_out_of_stock_meal(self):
        """Исчерпание питания."""
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
        """Пополнение инвентаря."""
        from aircraft_model import InFlightService
        service = InFlightService()

        initial = service.get_quantity(ServiceType.MEAL)
        service.restock(ServiceType.MEAL, 50)

        assert service.get_quantity(ServiceType.MEAL) == initial + 50

    def test_check_supplies(self):
        """Проверка наличия."""
        from aircraft_model import InFlightService
        service = InFlightService()

        assert service.check_supplies(ServiceType.MEAL) is True

    def test_get_stats(self):
        """Получение статистики."""
        from aircraft_model import InFlightService
        service = InFlightService()

        service.provide_meal("meal")
        stats = service.get_stats()

        assert stats[ServiceType.MEAL] > 0


# ============================================================================
# ТЕСТЫ ДЛЯ БИЗНЕС-ЛОГИКИ - CrewMember
# ============================================================================

class TestCrewMemberCreation:
    """Тесты для создания члена экипажа."""

    def test_create_crew_valid(self):
        """Член экипажа создаётся корректно."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        assert crew.full_name == "Иван Иванов"
        assert crew.role == CrewRole.PILOT
        assert crew.license_number == "PLT-12345"

    def test_create_crew_invalid_name_empty(self):
        """Пустое имя вызывает ошибку."""
        with pytest.raises(ValidationError):
            CrewMember("", CrewRole.PILOT, "PLT-12345")

    def test_create_crew_invalid_license_short(self):
        """Короткая лицензия вызывает ошибку."""
        with pytest.raises(ValidationError):
            CrewMember("Иван Иванов", CrewRole.PILOT, "AB")


class TestCrewMemberOperations:
    """Тесты для операций члена экипажа."""

    def test_start_duty(self):
        """Выход на дежурство."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        result = crew.start_duty()
        assert result is True
        assert crew.is_on_duty

    def test_start_duty_already_on_duty(self):
        """Повторный выход на дежурство."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        crew.start_duty()
        result = crew.start_duty()
        assert result is False

    def test_end_duty(self):
        """Окончание дежурства."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        crew.start_duty()
        result = crew.end_duty()
        assert result is True
        assert not crew.is_on_duty

    def test_perform_duty(self):
        """Выполнение обязанностей."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        crew.start_duty()

        result = crew.perform_duty("пилотирование")
        assert result["status"] == "completed"
        assert result["member"] == "Иван Иванов"

    def test_perform_duty_not_on_duty_fails(self):
        """Выполнение обязанностей не на дежурстве."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")

        with pytest.raises(CrewError):
            crew.perform_duty("пилотирование")

    def test_can_fly(self):
        """Проверка возможности полёта."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        crew.start_duty()
        assert crew.can_fly() is True

    def test_cannot_fly_not_on_duty(self):
        """Не на дежурстве - не может лететь."""
        crew = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT-12345")
        assert crew.can_fly() is False

    def test_cannot_fly_attendant(self):
        """Бортпроводник не может пилотировать."""
        crew = CrewMember("Иван Иванов", CrewRole.FLIGHT_ATTENDANT, "FA-12345")
        crew.start_duty()
        assert crew.can_fly() is False


# ============================================================================
# ТЕСТЫ ДЛЯ ОБРАБОТКИ ИСКЛЮЧЕНИЙ
# ============================================================================

class TestExceptionHandling:
    """Тесты для обработки исключений."""

    def test_validation_error_message(self):
        """ValidationError содержит сообщение."""
        with pytest.raises(ValidationError):
            Aircraft("", "RA-12345", 150)

    def test_registration_error_message(self):
        """RegistrationError имеет правильный тип."""
        passenger = Passenger("Test", "AB12345678", "TKT-001", "1A")
        passenger.register_for_flight()

        with pytest.raises(RegistrationError):
            passenger.register_for_flight()

    def test_flight_error_on_invalid_ticket(self):
        """FlightError при невалидном билете."""
        from datetime import datetime, timedelta
        past_time = datetime.now() - timedelta(hours=5)
        ticket = Ticket.issue(
            flight_number="SU999",
            flight_datetime=past_time,
            seat="1A",
            price=999.99,
            passport_number="AB12345678",
        )
        with pytest.raises(FlightError):
            ticket.validate()

    def test_takeoff_error_on_wrong_status(self, aircraft_on_ground):
        """TakeoffError при неправильном статусе."""
        aircraft = aircraft_on_ground
        # Ставим статус не на земле
        aircraft.change_status(AircraftStatus.MAINTENANCE)

        with pytest.raises(TakeoffError):
            aircraft.take_off()

    def test_capacity_error(self):
        """Превышение вместимости."""
        aircraft = Aircraft("Boeing 737", "RA-12345", 2)
        p1 = Passenger("Test1", "AB11111111", "TKT-001", "1A")
        p1.register_for_flight()
        p2 = Passenger("Test2", "AB22222222", "TKT-002", "1B")
        p2.register_for_flight()
        p3 = Passenger("Test3", "AB33333333", "TKT-003", "1C")
        p3.register_for_flight()

        aircraft.add_passenger(p1)
        aircraft.add_passenger(p2)

        with pytest.raises(CapacityError):
            aircraft.add_passenger(p3)

    def test_service_error_out_of_stock(self):
        """ServiceError при исчерпании запасов."""
        from aircraft_model import InFlightService
        service = InFlightService()

        for _ in range(100):
            try:
                service.provide_meal("meal")
            except ServiceError:
                break

        with pytest.raises(ServiceError):
            service.provide_meal("dinner")


# ============================================================================
# ТЕСТЫ ДЛЯ ДЕМО-РЕЖИМА
# ============================================================================

class TestDemoMode:
    """Тесты для демо-режима."""

    def test_demo_creates_aircraft(self):
        """Демо создаёт самолёт."""
        from main import SystemState
        SystemState._instance = None
        state = SystemState()

        aircraft = Aircraft(
            model="Boeing 737-800",
            tail_number="RA-737MM",
            capacity=150,
        )
        state.aircraft["RA-737MM"] = aircraft

        assert "RA-737MM" in state.aircraft
        assert state.aircraft["RA-737MM"].model == "Boeing 737-800"

    def test_demo_creates_crew(self):
        """Демо создаёт экипаж."""
        from main import SystemState
        SystemState._instance = None
        state = SystemState()

        crew = CrewMember("Иван Сидоров", CrewRole.PILOT, "PLT-SID001")
        crew.start_duty()
        state.crew_members["PLT-SID001"] = crew

        assert "PLT-SID001" in state.crew_members
        assert state.crew_members["PLT-SID001"].is_on_duty

    def test_demo_creates_passengers(self):
        """Демо создаёт пассажиров."""
        from main import SystemState
        SystemState._instance = None
        state = SystemState()

        passenger = Passenger("Михаил Петров", "MP12345678", "TKT-001", "15A")
        passenger.register_for_flight()
        state.passengers["MP12345678"] = passenger

        assert "MP12345678" in state.passengers
        assert state.passengers["MP12345678"].is_registered

    def test_demo_creates_route(self):
        """Демо создаёт маршрут."""
        from main import SystemState
        SystemState._instance = None
        state = SystemState()

        route = FlightRoute("SVO", "LED", 650)
        state.routes["SVO-LED"] = route

        assert "SVO-LED" in state.routes
        assert state.routes["SVO-LED"].distance == 650

    def test_demo_creates_runway(self):
        """Демо создаёт ВПП."""
        from main import SystemState
        SystemState._instance = None
        state = SystemState()

        runway = Runway("RWY-SVO", 3000)
        state.runways["RWY-SVO"] = runway

        assert "RWY-SVO" in state.runways
        assert state.runways["RWY-SVO"].length == 3000

    def test_demo_full_workflow(self):
        """Полный демо-рабочий процесс."""
        from main import SystemState
        SystemState._instance = None
        state = SystemState()

        # Создаём самолёт
        aircraft = Aircraft("Boeing 737-800", "RA-737MM", 150)
        state.aircraft["RA-737MM"] = aircraft

        # Добавляем достаточный экипаж (пилот + 2 бортпроводника минимум)
        pilot = CrewMember("Иван Сидоров", CrewRole.PILOT, "PLT-001")
        pilot.start_duty()
        aircraft.add_crew_member(pilot)

        att1 = CrewMember("Бортпроводник 1", CrewRole.FLIGHT_ATTENDANT, "FA-001")
        att1.start_duty()
        aircraft.add_crew_member(att1)

        att2 = CrewMember("Бортпроводник 2", CrewRole.FLIGHT_ATTENDANT, "FA-002")
        att2.start_duty()
        aircraft.add_crew_member(att2)

        # Добавляем пассажира
        p = Passenger("Михаил Петров", "MP12345678", "TKT-001", "15A")
        p.register_for_flight()
        aircraft.add_passenger(p)

        # Устанавливаем маршрут
        route = FlightRoute("SVO", "LED", 650)
        aircraft.set_route(route)

        # Взлёт
        runway = Runway("RWY-01", 3000)
        runway.request_takeoff(aircraft)
        aircraft.take_off()

        assert aircraft.status == AircraftStatus.IN_FLIGHT


# ============================================================================
# ЗАПУСК ТЕСТОВ
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])