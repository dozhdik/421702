"""
Класс Aircraft (Самолёт).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .crew_member import CrewMember
from .enums import AircraftStatus, CrewRole
from .exceptions import (
    CapacityError,
    CrewError,
    FlightError,
    TakeoffError,
    ValidationError,
)
from .flight_route import FlightRoute
from .in_flight_service import InFlightService
from .passenger import Passenger


class Aircraft:
    """
    Представляет самолёт и управляет его состоянием.

    Атрибуты:
        model: Модель самолёта.
        tail_number: Бортовой номер.
        capacity: Вместимость (количество пассажиров).
        status: Текущий статус.
        current_airport: Текущий аэропорт.
    """

    # Минимальные требования к экипажу
    MIN_CREW_REQUIREMENTS: Dict[CrewRole, int] = {
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

        self._model = model
        self._tail_number = tail_number.upper()
        self._capacity = capacity
        self._status = status or AircraftStatus.ON_GROUND
        self._current_airport = current_airport or ""

        self._passengers: List[Passenger] = []
        self._crew: List[CrewMember] = []
        self._flight_route: Optional[FlightRoute] = None
        self._service = InFlightService()

    @staticmethod
    def _validate_model(model: str) -> None:
        """Валидация модели."""
        if not model or not model.strip():
            raise ValidationError("model", "Model cannot be empty")

    @staticmethod
    def _validate_tail_number(tail_num: str) -> None:
        """Валидация бортового номера."""
        if not tail_num or not tail_num.strip():
            raise ValidationError(
                "tail_number", "Tail number cannot be empty"
            )
        if len(tail_num) < 5:
            raise ValidationError(
                "tail_number", "Tail number too short (min 5 chars)"
            )

    @staticmethod
    def _validate_capacity(capacity: int) -> None:
        """Валидация вместимости."""
        if capacity <= 0:
            raise ValidationError("capacity", "Capacity must be positive")
        if capacity > 850:
            raise ValidationError(
                "capacity", "Capacity exceeds maximum (850)"
            )

    @property
    def model(self) -> str:
        """Получить модель."""
        return self._model

    @property
    def tail_number(self) -> str:
        """Получить бортовой номер."""
        return self._tail_number

    @property
    def capacity(self) -> int:
        """Получить вместимость."""
        return self._capacity

    @property
    def status(self) -> AircraftStatus:
        """Получить статус."""
        return self._status

    @property
    def current_airport(self) -> str:
        """Получить текущий аэропорт."""
        return self._current_airport

    @property
    def passengers(self) -> List[Passenger]:
        """Получить список пассажиров."""
        return self._passengers.copy()

    @property
    def crew(self) -> List[CrewMember]:
        """Получить список экипажа."""
        return self._crew.copy()

    def get_status(self) -> AircraftStatus:
        """Получить статус (метод-версия)."""
        return self._status

    def get_model(self) -> str:
        """Получить модель (метод-версия)."""
        return self._model

    def get_capacity(self) -> int:
        """Получить вместимость (метод-версия)."""
        return self._capacity

    def get_passenger_count(self) -> int:
        """Получить количество пассажиров."""
        return len(self._passengers)

    def get_available_seats(self) -> int:
        """Получить количество свободных мест."""
        return self._capacity - len(self._passengers)

    def change_status(self, status: AircraftStatus) -> None:
        """
        Изменить статус самолёта.

        Args:
            status: Новый статус.
        """
        old_status = self._status
        self._status = status
        print(f"  [STATUS] {self._tail_number}: {old_status.name} → {status.name}")

    def set_airport(self, airport: str) -> None:
        """Установить текущий аэропорт."""
        self._current_airport = airport.upper()

    def set_route(self, route: FlightRoute) -> None:
        """Установить маршрут полёта."""
        self._flight_route = route

    def add_passenger(self, passenger: Passenger) -> bool:
        """
        Добавить пассажира на борт.

        Args:
            passenger: Пассажир для добавления.

        Returns:
            True если успешно.

        Raises:
            CapacityError: Если нет свободных мест.
        """
        if len(self._passengers) >= self._capacity:
            raise CapacityError(
                self._capacity, len(self._passengers) + 1
            )

        if not passenger.is_registered:
            raise FlightError(
                f"Passenger {passenger.full_name} is not registered"
            )

        self._passengers.append(passenger)
        return True

    def remove_passenger(self, passport_number: str) -> Optional[Passenger]:
        """
        Удалить пассажира с борта.

        Args:
            passport_number: Номер паспорта.

        Returns:
            Удалённый пассажир или None.
        """
        for i, p in enumerate(self._passengers):
            if p.passport_number == passport_number.upper():
                return self._passengers.pop(i)
        return None

    def add_crew_member(self, member: CrewMember) -> bool:
        """
        Добавить члена экипажа.

        Args:
            member: Член экипажа.

        Returns:
            True если успешно.
        """
        # Проверяем дубликат
        for m in self._crew:
            if m.license_number == member.license_number:
                return False

        self._crew.append(member)
        return True

    def remove_crew_member(self, license_number: str) -> Optional[CrewMember]:
        """
        Удалить члена экипажа.

        Args:
            license_number: Номер лицензии.

        Returns:
            Удалённый член экипажа или None.
        """
        for i, m in enumerate(self._crew):
            if m.license_number == license_number:
                return self._crew.pop(i)
        return None

    def _check_minimum_crew(self) -> bool:
        """Проверить минимальный состав экипажа."""
        crew_count: Dict[CrewRole, int] = {}
        for member in self._crew:
            crew_count[member.role] = crew_count.get(member.role, 0) + 1

        for role, required in self.MIN_CREW_REQUIREMENTS.items():
            if crew_count.get(role, 0) < required:
                return False
        return True

    def _all_crew_on_duty(self) -> bool:
        """Проверить, все ли члены экипажа на дежурстве."""
        return all(member.is_on_duty for member in self._crew)

    def preflight_check(self) -> Dict[str, bool]:
        """
        Выполнить предполётную проверку.

        Returns:
            Словарь с результатами проверок.
        """
        results = {
            "crew_minimum": self._check_minimum_crew(),
            "crew_on_duty": self._all_crew_on_duty(),
            "passengers_registered": len(self._passengers) > 0,
            "route_set": self._flight_route is not None,
            "status_ok": self._status == AircraftStatus.ON_GROUND,
        }
        return results

    def can_take_off(self) -> bool:
        """
        Проверить готовность к взлёту.

        Returns:
            True если можно взлетать.
        """
        checks = self.preflight_check()
        return all(checks.values())

    def take_off(self) -> None:
        """
        Выполнить взлёт.

        Raises:
            TakeoffError: Если взлёт невозможен.
        """
        if not self.can_take_off():
            checks = self.preflight_check()
            failed = [k for k, v in checks.items() if not v]
            raise TakeoffError(
                f"Cannot take off. Failed checks: {', '.join(failed)}"
            )

        self.change_status(AircraftStatus.IN_FLIGHT)
        for member in self._crew:
            # Пилоты начинают выполнение полётных обязанностей
            if member.role in (CrewRole.PILOT, CrewRole.CO_PILOT):
                member.perform_duty("piloting")

    def land(self) -> None:
        """
        Выполнить посадку.

        Raises:
            FlightError: Если посадка невозможна.
        """
        if self._status != AircraftStatus.IN_FLIGHT:
            raise FlightError(
                f"Cannot land: aircraft is {self._status.name}"
            )

        self.change_status(AircraftStatus.ON_GROUND)
        for member in self._crew:
            if member.role in (CrewRole.PILOT, CrewRole.CO_PILOT):
                member.perform_duty("landing_complete")

    def start_boarding(self) -> None:
        """Начать посадку пассажиров."""
        if self._status != AircraftStatus.ON_GROUND:
            raise FlightError("Can only start boarding when on ground")
        self.change_status(AircraftStatus.BOARDING)

    def end_boarding(self) -> None:
        """Завершить посадку пассажиров."""
        if self._status != AircraftStatus.BOARDING:
            raise FlightError("Can only end boarding when boarding")
        self.change_status(AircraftStatus.ON_GROUND)

    def get_service(self) -> InFlightService:
        """Получить доступ к бортовому сервису."""
        return self._service

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
