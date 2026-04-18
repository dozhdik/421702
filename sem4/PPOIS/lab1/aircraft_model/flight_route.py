"""
Класс FlightRoute (Маршрут полёта).
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Optional

from .exceptions import ValidationError


class FlightRoute:
    """
    Представляет маршрут авиарейса.

    Атрибуты:
        departure: Код аэропорта вылета (IATA).
        destination: Код аэропорта прилёта (IATA).
        distance: Расстояние в километрах.
        estimated_duration: Расчётное время полёта.
        alternative_airports: Список альтернативных аэропортов.
    """

    # Средняя скорость гражданского самолёта (км/ч)
    AVERAGE_SPEED_KMH = 800.0
    # Средний расход топлива (л/км)
    AVERAGE_FUEL_CONSUMPTION = 3.5

    def __init__(
        self,
        departure: str,
        destination: str,
        distance: float,
        estimated_duration: Optional[timedelta] = None,
    ) -> None:
        self._validate_airport_code(departure, "departure")
        self._validate_airport_code(destination, "destination")
        self._validate_distance(distance)

        self._departure = departure.upper()
        self._destination = destination.upper()
        self._distance = distance

        if estimated_duration:
            self._estimated_duration = estimated_duration
        else:
            self._estimated_duration = timedelta(
                hours=distance / self.AVERAGE_SPEED_KMH
            )

        self._alternative_airports: list[str] = []

    @staticmethod
    def _validate_airport_code(code: str, field_name: str) -> None:
        """Валидация IATA-кода аэропорта."""
        if not code or not code.strip():
            raise ValidationError(field_name, "Airport code cannot be empty")
        if not re.match(r"^[A-Z]{3}$", code.upper()):
            raise ValidationError(
                field_name,
                "Airport code must be 3 letters (IATA format, e.g., SVO)",
            )

    @staticmethod
    def _validate_distance(distance: float) -> None:
        """Валидация расстояния."""
        if distance <= 0:
            raise ValidationError("distance", "Distance must be positive")
        if distance > 20000:  # Максимум ~половина окружности Земли
            raise ValidationError(
                "distance", "Distance exceeds maximum possible"
            )

    @property
    def departure(self) -> str:
        """Получить код аэропорта вылета."""
        return self._departure

    @property
    def destination(self) -> str:
        """Получить код аэропорта прилёта."""
        return self._destination

    @property
    def distance(self) -> float:
        """Получить расстояние в км."""
        return self._distance

    @property
    def estimated_duration(self) -> timedelta:
        """Получить расчётное время полёта."""
        return self._estimated_duration

    @property
    def alternative_airports(self) -> list[str]:
        """Получить список альтернативных аэропортов."""
        return self._alternative_airports.copy()

    def add_alternative(self, airport_code: str) -> None:
        """
        Добавить альтернативный аэропорт.

        Args:
            airport_code: IATA-код аэропорта.
        """
        self._validate_airport_code(airport_code, "alternative_airport")
        if airport_code not in self._alternative_airports:
            self._alternative_airports.append(airport_code.upper())

    def calculate_fuel(
        self,
        consumption_per_km: Optional[float] = None,
    ) -> float:
        """
        Рассчитать необходимое топливо.

        Args:
            consumption_per_km: Расход топлива (л/км).
                             Если None, используется средний.

        Returns:
            Необходимое количество топлива в литрах.
        """
        consumption = consumption_per_km or self.AVERAGE_FUEL_CONSUMPTION
        # Добавляем 10% резерв
        return self._distance * consumption * 1.1

    def estimate_duration(
        self,
        average_speed: Optional[float] = None,
    ) -> timedelta:
        """
        Рассчитать расчётное время полёта.

        Args:
            average_speed: Средняя скорость (км/ч).
                          Если None, используется средняя.

        Returns:
            Расчётное время полёта.
        """
        speed = average_speed or self.AVERAGE_SPEED_KMH
        return timedelta(hours=self._distance / speed)

    def is_route_compatible(self, other: FlightRoute) -> bool:
        """
        Проверить совместимость маршрутов.

        Args:
            other: Другой маршрут.

        Returns:
            True если маршруты совместимы для стыковки.
        """
        return self._destination == other.departure

    def __repr__(self) -> str:
        return (
            f"FlightRoute("
            f"departure={self._departure!r}, "
            f"destination={self._destination!r}, "
            f"distance={self._distance})"
        )

    def __str__(self) -> str:
        hours = int(self._estimated_duration.total_seconds() // 3600)
        minutes = int(
            (self._estimated_duration.total_seconds() % 3600) // 60
        )
        alternatives = (
            f", Alternatives: {', '.join(self._alternative_airports)}"
            if self._alternative_airports
            else ""
        )

        return (
            f"Route: {self._departure} → {self._destination} | "
            f"Distance: {self._distance:.0f} km | "
            f"Duration: ~{hours}h {minutes}m{alternatives}"
        )

    def __add__(self, other: FlightRoute) -> FlightRoute:
        """Объединить два маршрута (stitching)."""
        if not self.is_route_compatible(other):
            raise ValidationError(
                "routes",
                "Routes are not compatible for stitching",
            )

        combined = FlightRoute(
            self._departure,
            other.destination,
            self._distance + other.distance,
        )

        for alt in self._alternative_airports:
            combined.add_alternative(alt)
        for alt in other.alternative_airports:
            combined.add_alternative(alt)

        return combined
