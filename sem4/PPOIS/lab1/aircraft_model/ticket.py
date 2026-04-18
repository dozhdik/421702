"""
Класс Ticket (Билет).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

from .enums import TicketStatus
from .exceptions import FlightError, ValidationError


class Ticket:
    """
    Представляет билет на авиарейс.

    Атрибуты:
        flight_number: Номер рейса.
        flight_datetime: Дата и время вылета.
        seat: Место в салоне.
        price: Цена билета.
        status: Статус билета.
        passport_number: Номер паспорта пассажира.
    """

    def __init__(
        self,
        flight_number: str,
        flight_datetime: datetime,
        seat: str,
        price: float,
        passport_number: str,
    ) -> None:
        self._validate_flight_number(flight_number)
        self._validate_seat(seat)
        self._validate_price(price)
        self._validate_passport(passport_number)

        self._flight_number = flight_number.upper()
        self._flight_datetime = flight_datetime
        self._seat = seat.upper()
        self._price = price
        self._passport_number = passport_number.upper()
        self._status = TicketStatus.BOOKED
        self._issued_at = datetime.now()

    @staticmethod
    def _validate_flight_number(flight_num: str) -> None:
        """Валидация номера рейса."""
        if not flight_num or not flight_num.strip():
            raise ValidationError(
                "flight_number", "Flight number cannot be empty"
            )
        # Формат: буквы IATA кода + номер (например, SU123, BA4567)
        pattern = r"^[A-Z]{2}\d{1,4}$"
        if not re.match(pattern, flight_num.upper()):
            raise ValidationError(
                "flight_number",
                "Flight number must be 2 letters + 1-4 digits (e.g., SU123)",
            )

    @staticmethod
    def _validate_seat(seat: str) -> None:
        """Валидация места."""
        if not seat:
            raise ValidationError("seat", "Seat cannot be empty")
        pattern = r"^\d{1,2}[A-HJK]$"
        if not re.match(pattern, seat.upper()):
            raise ValidationError(
                "seat", "Seat must be in format: row + letter (e.g., 12A)"
            )

    @staticmethod
    def _validate_price(price: float) -> None:
        """Валидация цены."""
        if price < 0:
            raise ValidationError("price", "Price cannot be negative")

    @staticmethod
    def _validate_passport(passport: str) -> None:
        """Валидация паспорта."""
        if not passport or not passport.strip():
            raise ValidationError(
                "passport_number", "Passport number cannot be empty"
            )

    @classmethod
    def issue(
        cls,
        flight_number: str,
        flight_datetime: datetime,
        seat: str,
        price: float,
        passport_number: str,
    ) -> Ticket:
        """
        Фабричный метод для создания билета.

        Returns:
            Новый экземпляр Ticket.
        """
        return cls(
            flight_number, flight_datetime, seat, price, passport_number
        )

    @property
    def flight_number(self) -> str:
        """Получить номер рейса."""
        return self._flight_number

    @property
    def flight_datetime(self) -> datetime:
        """Получить дату/время вылета."""
        return self._flight_datetime

    @property
    def seat(self) -> str:
        """Получить место."""
        return self._seat

    @property
    def price(self) -> float:
        """Получить цену."""
        return self._price

    @property
    def status(self) -> TicketStatus:
        """Получить статус."""
        return self._status

    @property
    def passport_number(self) -> str:
        """Получить номер паспорта."""
        return self._passport_number

    def validate(self) -> bool:
        """
        Валидировать билет.

        Returns:
            True если билет валиден для использования.

        Raises:
            FlightError: Если билет недействителен.
        """
        if self._status == TicketStatus.CANCELLED:
            raise FlightError("Ticket has been cancelled")

        if self._status == TicketStatus.REFUNDED:
            raise FlightError("Ticket has been refunded")

        if self._status == TicketStatus.USED:
            raise FlightError("Ticket has already been used")

        # Проверяем, что вылет не раньше чем через 24 часа
        time_until_flight = self._flight_datetime - datetime.now()
        if time_until_flight < timedelta(hours=-2):
            raise FlightError("Flight has already departed")

        return True

    def confirm(self) -> bool:
        """
        Подтвердить билет.

        Returns:
            True если успешно.
        """
        if self._status != TicketStatus.BOOKED:
            return False
        self._status = TicketStatus.CONFIRMED
        return True

    def use(self) -> bool:
        """
        Пометить билет как использованный.

        Returns:
            True если успешно.

        Raises:
            FlightError: Если билет нельзя использовать.
        """
        if self._status not in (
            TicketStatus.BOOKED,
            TicketStatus.CONFIRMED,
        ):
            raise FlightError(
                f"Cannot use ticket with status: {self._status.name}"
            )
        self._status = TicketStatus.USED
        return True

    def cancel(self) -> bool:
        """
        Отменить билет.

        Returns:
            True если успешно.
        """
        if self._status in (TicketStatus.USED, TicketStatus.CANCELLED):
            return False
        self._status = TicketStatus.CANCELLED
        return True

    def refund(self) -> bool:
        """
        Возместить билет.

        Returns:
            True если успешно.
        """
        if self._status == TicketStatus.USED:
            return False
        self._status = TicketStatus.REFUNDED
        return True

    def is_valid(self) -> bool:
        """Проверить, валиден ли билет."""
        return self._status in (TicketStatus.BOOKED, TicketStatus.CONFIRMED)

    def __repr__(self) -> str:
        return (
            f"Ticket(flight={self._flight_number!r}, "
            f"seat={self._seat!r}, "
            f"status={self._status.name}, "
            f"passport={self._passport_number!r})"
        )

    def __str__(self) -> str:
        return (
            f"Ticket: {self._flight_number} | "
            f"Date: {self._flight_datetime.strftime('%Y-%m-%d %H:%M')} | "
            f"Seat: {self._seat} | "
            f"Price: ${self._price:.2f} | "
            f"Status: {self._status.name}"
        )
