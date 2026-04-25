"""Фикстуры для тестов."""
import pytest
from datetime import datetime, timedelta
from aircraft_model import (
    Aircraft, CrewMember, CrewRole, Passenger, FlightRoute,
    InFlightService, Ticket, Runway, RunwayStatus, TicketStatus
)


@pytest.fixture
def aircraft():
    """Создать тестовый самолёт."""
    return Aircraft("Boeing 737-800", "RA-TEST1", 150)


@pytest.fixture
def crew_member():
    """Создать тестового члена экипажа."""
    return CrewMember("Иван Иванов", CrewRole.PILOT, "PLT12345")


@pytest.fixture
def passenger():
    """Создать тестового пассажира."""
    return Passenger("Пётр Петров", "PASS1234", "TKT001", "12A")


@pytest.fixture
def registered_passenger():
    """Создать зарегистрированного пассажира."""
    p = Passenger("Пётр Петров", "PASS1234", "TKT001", "12A")
    p.register_for_flight()
    return p


@pytest.fixture
def flight_route():
    """Создать тестовый маршрут."""
    return FlightRoute("SVO", "LED", 634.0)


@pytest.fixture
def in_flight_service():
    """Создать тестовый сервис."""
    return InFlightService()


@pytest.fixture
def ticket():
    """Создать тестовый билет."""
    return Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")


@pytest.fixture
def runway():
    """Создать тестовую ВПП."""
    return Runway("RWY01", 3000)


@pytest.fixture
def aircraft_with_crew(aircraft):
    """Самолёт с минимальным экипажем."""
    pilot = CrewMember("Пилот", CrewRole.PILOT, "PLT001")
    copilot = CrewMember("Второй пилот", CrewRole.CO_PILOT, "CPT001")
    fa1 = CrewMember("Бортпроводник 1", CrewRole.FLIGHT_ATTENDANT, "FA001")
    fa2 = CrewMember("Бортпроводник 2", CrewRole.FLIGHT_ATTENDANT, "FA002")

    pilot.start_duty()
    copilot.start_duty()
    fa1.start_duty()
    fa2.start_duty()

    aircraft.add_crew_member(pilot)
    aircraft.add_crew_member(copilot)
    aircraft.add_crew_member(fa1)
    aircraft.add_crew_member(fa2)

    return aircraft


@pytest.fixture
def aircraft_ready_for_takeoff(aircraft_with_crew, registered_passenger, flight_route):
    """Самолёт готовый к взлёту."""
    aircraft_with_crew.add_passenger(registered_passenger)
    aircraft_with_crew.set_route(flight_route)
    return aircraft_with_crew
