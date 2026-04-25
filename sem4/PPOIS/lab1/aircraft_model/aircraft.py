"""
Класс Aircraft (Самолёт).
Управляет состоянием воздушного судна, экипажем, пассажирами и полётными операциями.
"""

from __future__ import annotations

from typing import Optional

from .crew_member import CrewMember
from .enums import AircraftStatus, CrewRole
from .exceptions import CapacityError, CrewError, FlightError, TakeoffError, ValidationError
from .flight_route import FlightRoute
from .in_flight_service import InFlightService
from .passenger import Passenger


class Aircraft:
    """
    Представляет самолёт и управляет его состоянием.
    """

    # Минимальные требования к экипажу для вылета
    MIN_CREW_REQUIREMENTS: dict[CrewRole, int] = {
        CrewRole.PILOT: 1,
        CrewRole.FLIGHT_ATTENDANT: 2,
    }

    def __init__(
        self,
        model: str,
        tail_number: str,
        capacity: int,
        status: Optional[AircraftStatus] = None,
        current_airport: Optional[str] = None,
    ) -> None:
        self._validate_model(model)
        self._validate_tail_number(tail_number)
        self._validate_capacity(capacity)

        self._model: str = model.strip()
        self._tail_number: str = tail_number.upper().strip()
        self._capacity: int = capacity
        self._status: AircraftStatus = status or AircraftStatus.ON_GROUND
        self._current_airport: str = (current_airport or "").upper().strip()

        self._passengers: list[Passenger] = []
        self._crew: list[CrewMember] = []
        self._flight_route: Optional[FlightRoute] = None
        self._service: InFlightService = InFlightService()

    # ========================================================================
    # ВАЛИДАЦИЯ
    # ========================================================================
    @staticmethod
    def _validate_model(model: str) -> None:
        if not model or not model.strip():
            raise ValidationError("model", "Название модели не может быть пустым")

    @staticmethod
    def _validate_tail_number(tail_num: str) -> None:
        if not tail_num or not tail_num.strip():
            raise ValidationError("tail_number", "Бортовой номер не может быть пустым")
        if len(tail_num.strip()) < 5:
            raise ValidationError("tail_number", "Бортовой номер слишком короткий (минимум 5 символов)")

    @staticmethod
    def _validate_capacity(capacity: int) -> None:
        if capacity <= 0:
            raise ValidationError("capacity", "Вместимость должна быть положительным числом")
        if capacity > 850:
            raise ValidationError("capacity", "Вместимость превышает максимальный предел (850 мест)")

    # ========================================================================
    # СВОЙСТВА (READ-ONLY)
    # ========================================================================
    @property
    def model(self) -> str:
        return self._model

    @property
    def tail_number(self) -> str:
        return self._tail_number

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def status(self) -> AircraftStatus:
        return self._status

    @property
    def current_airport(self) -> str:
        return self._current_airport

    @property
    def passengers(self) -> list[Passenger]:
        return self._passengers.copy()

    @property
    def crew(self) -> list[CrewMember]:
        return self._crew.copy()

    # ========================================================================
    # БАЗОВЫЕ МЕТОДЫ
    # ========================================================================
    def get_passenger_count(self) -> int:
        return len(self._passengers)

    def get_available_seats(self) -> int:
        return self._capacity - len(self._passengers)

    def set_airport(self, airport: str) -> None:
        self._current_airport = airport.upper().strip()

    def set_route(self, route: FlightRoute) -> None:
        self._flight_route = route

    def change_status(self, new_status: AircraftStatus) -> None:
        old_status = self._status
        self._status = new_status
        print(f"Статус({self._tail_number}): {old_status.name} -> {new_status.name}")

    def get_service(self) -> InFlightService:
        return self._service

    # ========================================================================
    # УПРАВЛЕНИЕ ПАССАЖИРАМИ
    # ========================================================================
    def add_passenger(self, passenger: Passenger) -> bool:
        if len(self._passengers) >= self._capacity:
            raise CapacityError(self._capacity, len(self._passengers) + 1)

        if not passenger.is_registered:
            raise FlightError(f"Пассажир {passenger.full_name} не зарегистрирован на рейс")

        self._passengers.append(passenger)
        return True

    def remove_passenger(self, passport_number: str) -> Optional[Passenger]:
        passport_number = passport_number.upper()
        for i, p in enumerate(self._passengers):
            if p.passport_number == passport_number:
                return self._passengers.pop(i)
        return None

    def clear_passengers(self) -> None:
        """Полностью очистить список пассажиров (используется после завершения рейса)."""
        self._passengers.clear()

    # ========================================================================
    # УПРАВЛЕНИЕ ЭКИПАЖЕМ
    # ========================================================================
    def add_crew_member(self, member: CrewMember) -> bool:
        for m in self._crew:
            if m.license_number == member.license_number:
                return False  # Дубликат лицензии
        self._crew.append(member)
        return True

    def remove_crew_member(self, license_number: str) -> Optional[CrewMember]:
        license_number = license_number.upper()
        for i, m in enumerate(self._crew):
            if m.license_number == license_number:
                return self._crew.pop(i)
        return None

    def _check_minimum_crew(self) -> bool:
        crew_count: dict[CrewRole, int] = {}
        for member in self._crew:
            crew_count[member.role] = crew_count.get(member.role, 0) + 1

        for role, required in self.MIN_CREW_REQUIREMENTS.items():
            if crew_count.get(role, 0) < required:
                return False
        return True

    def _all_crew_on_duty(self) -> bool:
        return all(member.is_on_duty for member in self._crew)

    # ========================================================================
    # ПРЕДПОЛЁТНАЯ ПРОВЕРКА И УПРАВЛЕНИЕ ПОЛЁТОМ
    # ========================================================================
    def preflight_check(self) -> dict[str, bool]:
        """
        Выполнить предполётную проверку.
        Возвращает словарь с результатами. Взлёт возможен только если все значения True.
        """
        return {
            "crew_minimum": self._check_minimum_crew(),
            "crew_on_duty": self._all_crew_on_duty(),
            "passengers_registered": len(self._passengers) >= 1,
            "route_set": self._flight_route is not None,
            "status_ok": self._status == AircraftStatus.ON_GROUND,
        }

    def can_take_off(self) -> bool:
        return all(self.preflight_check().values())

    def take_off(self) -> None:
        if not self.can_take_off():
            failed = [k for k, v in self.preflight_check().items() if not v]
            raise TakeoffError(f"Взлёт невозможен. Не пройдены проверки: {', '.join(failed)}")

        self.change_status(AircraftStatus.IN_FLIGHT)
        for member in self._crew:
            if member.role in (CrewRole.PILOT, CrewRole.CO_PILOT):
                member.perform_duty("piloting")

    def land(self) -> None:
        if self._status != AircraftStatus.IN_FLIGHT:
            raise FlightError(f"Посадка невозможна: текущий статус {self._status.name}")

        self.change_status(AircraftStatus.ON_GROUND)
        for member in self._crew:
            if member.role in (CrewRole.PILOT, CrewRole.CO_PILOT):
                member.perform_duty("landing_complete")

    def reset_after_landing(self) -> None:
        """
        Сбросить состояние самолёта после успешной посадки.
        Очищает пассажиров и маршрут, оставляя борт и экипаж для повторного использования.
        """
        self.clear_passengers()
        self._flight_route = None

    # ========================================================================
    # ПРЕДСТАВЛЕНИЕ
    # ========================================================================
    def __repr__(self) -> str:
        return (
            f"Aircraft(model={self._model!r}, "
            f"tail={self._tail_number!r}, "
            f"capacity={self._capacity}, "
            f"status={self._status.name})"
        )

    def __str__(self) -> str:
        return (
            f"Aircraft: {self._model} ({self._tail_number}) | "
            f"Status: {self._status.name} | "
            f"Passengers: {len(self._passengers)}/{self._capacity} | "
            f"Crew: {len(self._crew)} | "
            f"Airport: {self._current_airport or 'N/A'}"
        )