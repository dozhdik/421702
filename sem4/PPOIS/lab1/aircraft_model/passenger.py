"""
Класс Passenger (Пассажир).
"""

from __future__ import annotations

import re
from typing import Optional

from .exceptions import RegistrationError, ValidationError


class Passenger:
    """
    Представляет пассажира авиарейса.

    Атрибуты:
        full_name: Полное имя пассажира.
        passport_number: Номер паспорта (уникальный идентификатор).
        ticket_number: Номер билета.
        seat_number: Номер места в салоне.
        is_registered: Статус регистрации на рейс.
    """

    def __init__(
        self,
        full_name: str,
        passport_number: str,
        ticket_number: str,
        seat_number: Optional[str] = None,
    ) -> None:
        self._validate_name(full_name)
        self._validate_passport(passport_number)
        self._validate_ticket_number(ticket_number)

        self._full_name = full_name
        self._passport_number = passport_number
        self._ticket_number = ticket_number
        self._seat_number: Optional[str] = None
        self._is_registered = False

        if seat_number:
            self.assign_seat(seat_number)

    @staticmethod
    def _validate_name(name: str) -> None:
        """Валидация имени пассажира."""
        if not name or not name.strip():
            raise ValidationError("full_name", "Name cannot be empty")
        if len(name.strip()) < 3:
            raise ValidationError(
                "full_name", "Name must be at least 3 characters"
            )

    @staticmethod
    def _validate_passport(passport: str) -> None:
        """Валидация номера паспорта."""
        if not passport or not passport.strip():
            raise ValidationError(
                "passport_number", "Passport number cannot be empty"
            )
        if len(passport) < 6 or len(passport) > 12:
            raise ValidationError(
                "passport_number",
                "Passport must be between 6 and 12 characters",
            )
        if not re.match(r"^[A-Z0-9]+$", passport.upper()):
            raise ValidationError(
                "passport_number", "Passport must be alphanumeric"
            )

    @staticmethod
    def _validate_ticket_number(ticket: str) -> None:
        """Валидация номера билета."""
        if not ticket or not ticket.strip():
            raise ValidationError(
                "ticket_number", "Ticket number cannot be empty"
            )

    @staticmethod
    def _validate_seat(seat: str) -> None:
        """Валидация номера места."""
        if not seat:
            raise ValidationError("seat_number", "Seat cannot be empty")
        # Формат: ряд (число) + буква (A-K, кроме I)
        pattern = r"^\d{1,2}[A-HJK]$"
        if not re.match(pattern, seat.upper()):
            raise ValidationError(
                "seat_number",
                "Seat must be in format: row number + letter (e.g., 12A)",
            )

    @property
    def full_name(self) -> str:
        """Получить полное имя."""
        return self._full_name

    @property
    def passport_number(self) -> str:
        """Получить номер паспорта."""
        return self._passport_number

    @property
    def ticket_number(self) -> str:
        """Получить номер билета."""
        return self._ticket_number

    @property
    def seat_number(self) -> Optional[str]:
        """Получить номер места."""
        return self._seat_number

    @property
    def is_registered(self) -> bool:
        """Проверить статус регистрации."""
        return self._is_registered

    def assign_seat(self, seat: str) -> None:
        """
        Назначить место пассажиру.

        Args:
            seat: Номер места для назначения.
        """
        self._validate_seat(seat)
        self._seat_number = seat.upper()

    def register_for_flight(self, seat: Optional[str] = None) -> bool:
        """
        Зарегистрировать пассажира на рейс.

        Args:
            seat: Необязательный номер места.

        Returns:
            True если регистрация успешна.

        Raises:
            RegistrationError: Если пассажир уже зарегистрирован
                                или место не назначено.
        """
        if self._is_registered:
            raise RegistrationError(
                f"Passenger {self._full_name} is already registered"
            )

        if seat:
            self.assign_seat(seat)
        elif not self._seat_number:
            raise RegistrationError(
                "Cannot register: seat not assigned. "
                "Use register_for_flight(seat='12A')"
            )

        self._is_registered = True
        return True

    def get_seat_number(self) -> Optional[str]:
        """Получить номер места пассажира."""
        return self._seat_number

    def is_registered_method(self) -> bool:
        """Проверить регистрацию (метод-версия)."""
        return self._is_registered

    def cancel_registration(self) -> bool:
        """
        Отменить регистрацию пассажира.

        Returns:
            True если отмена успешна.
        """
        if not self._is_registered:
            return False
        self._is_registered = False
        return True

    def __repr__(self) -> str:
        return (
            f"Passenger(name={self._full_name!r}, "
            f"passport={self._passport_number}, "
            f"seat={self._seat_number}, "
            f"registered={self._is_registered})"
        )

    def __str__(self) -> str:
        status = "registered" if self._is_registered else "not registered"
        seat = self._seat_number or "not assigned"
        return (
            f"Passenger: {self._full_name} | "
            f"Passport: {self._passport_number} | "
            f"Seat: {seat} | {status}"
        )
