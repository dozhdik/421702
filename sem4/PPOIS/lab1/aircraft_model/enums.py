"""
Перечисления (enums) для модели самолёта.
Содержит статусы и роли, используемые во всей системе.
"""

from enum import Enum, auto


class AircraftStatus(Enum):
    """Статусы самолёта."""
    ON_GROUND = auto()
    BOARDING = auto()
    IN_FLIGHT = auto()
    LANDING = auto()
    MAINTENANCE = auto()


class CrewRole(Enum):
    """Роли членов экипажа."""
    PILOT = auto()
    CO_PILOT = auto()
    NAVIGATOR = auto()
    FLIGHT_ATTENDANT = auto()
    LEAD_ATTENDANT = auto()
    ENGINEER = auto()


class ServiceType(Enum):
    """Типы бортовых услуг."""
    MEAL = auto()
    BEVERAGE = auto()
    ASSISTANCE = auto()
    WIFI = auto()
