"""
Модель самолёта - пакет для моделирования авиационной системы.
"""

from .aircraft import Aircraft
from .crew_member import CrewMember
from .enums import (
    AircraftStatus,
    CrewRole,
    ServiceType,
)
from .exceptions import (
    CapacityError,
    CrewError,
    FlightError,
    LandingError,
    RegistrationError,
    ServiceError,
    TakeoffError,
    ValidationError,
)
from .flight_route import FlightRoute
from .in_flight_service import InFlightService
from .passenger import Passenger

__all__ = [
    # Classes
    "Aircraft",
    "CrewMember",
    "FlightRoute",
    "InFlightService",
    "Passenger",
    # Enums
    "AircraftStatus",
    "CrewRole",
    "ServiceType",
    # Exceptions
    "CapacityError",
    "CrewError",
    "FlightError",
    "LandingError",
    "RegistrationError",
    "ServiceError",
    "TakeoffError",
    "ValidationError",
]

__version__ = "1.0.0"
