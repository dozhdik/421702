"""
Модель самолёта - пакет для моделирования авиационной системы.
"""

from .aircraft import Aircraft
from .crew_member import CrewMember
from .enums import (
    AircraftStatus,
    CrewRole,
    RunwayStatus,
    ServiceType,
    TicketStatus,
)
from .exceptions import (
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
from .flight_route import FlightRoute
from .in_flight_service import InFlightService
from .passenger import Passenger
from .runway import Runway
from .ticket import Ticket

__all__ = [
    # Classes
    "Aircraft",
    "CrewMember",
    "FlightRoute",
    "InFlightService",
    "Passenger",
    "Runway",
    "Ticket",
    # Enums
    "AircraftStatus",
    "CrewRole",
    "RunwayStatus",
    "ServiceType",
    "TicketStatus",
    # Exceptions
    "CapacityError",
    "CrewError",
    "FlightError",
    "LandingError",
    "RegistrationError",
    "RunwayError",
    "ServiceError",
    "TakeoffError",
    "ValidationError",
]

__version__ = "1.0.0"
