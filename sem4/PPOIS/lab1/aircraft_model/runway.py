"""
Класс Runway (Взлётно-посадочная полоса).
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .enums import RunwayStatus
from .exceptions import RunwayError, ValidationError

if TYPE_CHECKING:
    from aircraft import Aircraft


class Runway:
    """
    Представляет взлётно-посадочную полосу аэропорта.

    Атрибуты:
        runway_id: Уникальный идентификатор ВПП.
        length: Длина полосы в метрах.
        status: Текущий статус ВПП.
        current_aircraft: Самолёт, занимающий ВПП.
    """

    MIN_LENGTH = 500
    MAX_LENGTH = 6000

    def __init__(
        self,
        runway_id: str,
        length: int,
        status: Optional[RunwayStatus] = None,
    ) -> None:
        self._validate_id(runway_id)
        self._validate_length(length)

        self._runway_id = runway_id.upper()
        self._length = length
        self._status = status or RunwayStatus.FREE
        self._current_aircraft: Optional[str] = None
        self._queue: list[str] = []

    @staticmethod
    def _validate_id(runway_id: str) -> None:
        """Валидация идентификатора ВПП."""
        if not runway_id or not runway_id.strip():
            raise ValidationError("runway_id", "Runway ID cannot be empty")

    @staticmethod
    def _validate_length(length: int) -> None:
        """Валидация длины ВПП."""
        if length < Runway.MIN_LENGTH:
            raise ValidationError(
                "length",
                f"Runway must be at least {Runway.MIN_LENGTH}m",
            )
        if length > Runway.MAX_LENGTH:
            raise ValidationError(
                "length",
                f"Runway cannot exceed {Runway.MAX_LENGTH}m",
            )

    @property
    def runway_id(self) -> str:
        """Получить идентификатор ВПП."""
        return self._runway_id

    @property
    def length(self) -> int:
        """Получить длину ВПП."""
        return self._length

    @property
    def status(self) -> RunwayStatus:
        """Получить статус ВПП."""
        return self._status

    @property
    def is_free(self) -> bool:
        """Проверить, свободна ли ВПП."""
        return self._status == RunwayStatus.FREE

    @property
    def queue_size(self) -> int:
        """Получить размер очереди."""
        return len(self._queue)

    def request_takeoff(self, aircraft: Aircraft) -> bool:
        """
        Запросить взлёт.

        Args:
            aircraft: Самолёт, запрашивающий взлёт.

        Returns:
            True если взлёт разрешён сразу.

        Raises:
            RunwayError: Если ВПП закрыта.
        """
        if self._status == RunwayStatus.CLOSED:
            raise RunwayError(f"Runway {self._runway_id} is closed")

        if self._status == RunwayStatus.MAINTENANCE:
            raise RunwayError(
                f"Runway {self._runway_id} is under maintenance"
            )

        if self._status == RunwayStatus.FREE:
            self._status = RunwayStatus.OCCUPIED
            self._current_aircraft = aircraft.tail_number
            return True

        # Добавляем в очередь
        self._queue.append(aircraft.tail_number)
        return False

    def request_landing(self, aircraft: Aircraft) -> bool:
        """
        Запросить посадку.

        Args:
            aircraft: Самолёт, запрашивающий посадку.

        Returns:
            True если посадка разрешена сразу.

        Raises:
            RunwayError: Если ВПП закрыта.
        """
        if self._status == RunwayStatus.CLOSED:
            raise RunwayError(f"Runway {self._runway_id} is closed")

        if self._status == RunwayStatus.MAINTENANCE:
            raise RunwayError(
                f"Runway {self._runway_id} is under maintenance"
            )

        if self._status == RunwayStatus.FREE:
            self._status = RunwayStatus.OCCUPIED
            self._current_aircraft = aircraft.tail_number
            return True

        self._queue.append(aircraft.tail_number)
        return False

    def release(self) -> Optional[str]:
        """
        Освободить ВПП.

        Returns:
            Идентификатор следующего самолёта в очереди или None.
        """
        self._current_aircraft = None

        if self._queue:
            self._current_aircraft = self._queue.pop(0)
            return self._current_aircraft

        self._status = RunwayStatus.FREE
        return None

    def close(self) -> bool:
        """Закрыть ВПП."""
        if self._queue:
            raise RunwayError(
                "Cannot close runway with aircraft in queue"
            )
        self._status = RunwayStatus.CLOSED
        return True

    def open(self) -> bool:
        """Открыть ВПП."""
        if self._status == RunwayStatus.CLOSED:
            self._status = RunwayStatus.FREE
            return True
        return False

    def set_maintenance(self) -> None:
        """Установить статус технического обслуживания."""
        if self._current_aircraft:
            raise RunwayError(
                "Cannot set maintenance while aircraft is on runway"
            )
        self._status = RunwayStatus.MAINTENANCE

    def can_accommodate(self, required_length: int) -> bool:
        """Проверить, подходит ли длина для самолёта."""
        return self._length >= required_length

    def __repr__(self) -> str:
        return (
            f"Runway(id={self._runway_id!r}, "
            f"length={self._length}, "
            f"status={self._status.name})"
        )

    def __str__(self) -> str:
        current = self._current_aircraft or "None"
        return (
            f"Runway {self._runway_id} | "
            f"Length: {self._length}m | "
            f"Status: {self._status.name} | "
            f"Aircraft: {current} | "
            f"Queue: {self.queue_size}"
        )
