"""
Pytest fixtures для тестов aircraft_model.
"""

import sys
from pathlib import Path

# Добавляем путь
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import pytest
from datetime import datetime, timedelta

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
)
from aircraft_model.enums import ServiceType


# ============================================================================
# ФИКСТУРЫ ДЛЯ ОБЪЕКТОВ
# ============================================================================

@pytest.fixture
def sample_aircraft():
    """Фикстура для тестового самолёта."""
    return Aircraft(
        model="Boeing 737-800",
        tail_number="RA-737TEST",
        capacity=150,
    )


@pytest.fixture
def sample_passenger():
    """Фикстура для тестового пассажира."""
    return Passenger(
        full_name="Тестов Пассажир",
        passport_number="TP12345678",
        ticket_number="TKT-TEST001",
        seat_number="1A",
    )


@pytest.fixture
def registered_passenger():
    """Фикстура для зарегистрированного пассажира."""
    p = Passenger(
        full_name="Тестов Регистрированный",
        passport_number="TR12345678",
        ticket_number="TKT-TEST002",
        seat_number="2B",
    )
    p.register_for_flight()
    return p


@pytest.fixture
def sample_crew():
    """Фикстура для тестового члена экипажа."""
    return CrewMember(
        full_name="Тестов Пилот",
        role=CrewRole.PILOT,
        license_number="PLT-TEST001",
    )


@pytest.fixture
def crew_on_duty(sample_crew):
    """Член экипажа на дежурстве."""
    sample_crew.start_duty()
    return sample_crew


@pytest.fixture
def sample_ticket():
    """Фикстура для тестового билета."""
    return Ticket.issue(
        flight_number="TEST123",
        flight_datetime=datetime.now() + timedelta(hours=24),
        seat="3C",
        price=199.99,
        passport_number="TICKET12345",
    )


@pytest.fixture
def sample_runway():
    """Фикстура для тестовой ВПП."""
    return Runway("RWY-TEST", 3000)


@pytest.fixture
def sample_route():
    """Фикстура для тестового маршрута."""
    return FlightRoute("TST", "DST", 1000)


@pytest.fixture
def aircraft_on_ground(sample_aircraft):
    """Самолёт на земле с экипажем и пассажиром."""
    # Добавляем пилотов (2 требуется для полёта)
    pilot1 = CrewMember("Пилот", CrewRole.PILOT, "PLT-ONGR001")
    pilot1.start_duty()
    pilot2 = CrewMember("Второй пилот", CrewRole.CO_PILOT, "PLT-ONGR002")
    pilot2.start_duty()
    sample_aircraft.add_crew_member(pilot1)
    sample_aircraft.add_crew_member(pilot2)

    # Добавляем 2 бортпроводников (минимум 2)
    att1 = CrewMember("Бортпроводник 1", CrewRole.FLIGHT_ATTENDANT, "FA-ONGR001")
    att1.start_duty()
    att2 = CrewMember("Бортпроводник 2", CrewRole.FLIGHT_ATTENDANT, "FA-ONGR002")
    att2.start_duty()
    sample_aircraft.add_crew_member(att1)
    sample_aircraft.add_crew_member(att2)

    # Добавляем пассажира
    reg_p = Passenger("Пассажир", "ONGR12345678", "TKT-ONGR", "1A")
    reg_p.register_for_flight()
    sample_aircraft.add_passenger(reg_p)

    # Устанавливаем маршрут
    route = FlightRoute("SVO", "LED", 650)
    sample_aircraft.set_route(route)

    return sample_aircraft


@pytest.fixture
def in_flight_aircraft(sample_aircraft):
    """Самолёт в полёте с экипажем и пассажиром."""
    # Добавляем экипаж
    pilot1 = CrewMember("Пилот", CrewRole.PILOT, "PLT-IF001")
    pilot1.start_duty()
    pilot2 = CrewMember("Второй пилот", CrewRole.CO_PILOT, "PLT-IF002")
    pilot2.start_duty()
    sample_aircraft.add_crew_member(pilot1)
    sample_aircraft.add_crew_member(pilot2)

    att1 = CrewMember("Бортпроводник 1", CrewRole.FLIGHT_ATTENDANT, "FA-IF001")
    att1.start_duty()
    att2 = CrewMember("Бортпроводник 2", CrewRole.FLIGHT_ATTENDANT, "FA-IF002")
    att2.start_duty()
    sample_aircraft.add_crew_member(att1)
    sample_aircraft.add_crew_member(att2)

    # Добавляем пассажира
    reg_p = Passenger("Пассажир", "IF12345678", "TKT-IF", "1A")
    reg_p.register_for_flight()
    sample_aircraft.add_passenger(reg_p)

    # У��танавливаем маршрут
    route = FlightRoute("SVO", "LED", 650)
    sample_aircraft.set_route(route)

    # Меняем статус на IN_FLIGHT
    sample_aircraft.change_status(AircraftStatus.IN_FLIGHT)
    return sample_aircraft


# ============================================================================
# ФИКСТУРЫ ДЛЯ МОКОВ
# ============================================================================

@pytest.fixture
def mock_input():
    """Мок для input()."""
    from unittest.mock import patch
    return patch('builtins.input')


@pytest.fixture
def mock_safe_input(mock_input):
    """Мок для safe_input."""
    def _mock(value):
        mock_input.return_value = value
        return mock_input
    return _mock


# ============================================================================
# ФИКСТУРЫ ДЛЯ ОЧИСТКИ СОСТОЯНИЯ
# ============================================================================

@pytest.fixture(autouse=True)
def reset_system_state():
    """Очищает SystemState перед каждым тестом."""
    from main import SystemState
    SystemState._instance = None
    yield
    SystemState._instance = None