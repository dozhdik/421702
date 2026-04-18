"""
Класс CrewMember (Член экипажа).
"""

from __future__ import annotations

from typing import Dict, Optional

from .enums import CrewRole
from .exceptions import CrewError, ValidationError


class CrewMember:
    """
    Представляет члена экипажа самолёта.

    Атрибуты:
        full_name: Полное имя члена экипажа.
        role: Роль в экипаже (пилот, бортпроводник и т.д.).
        license_number: Номер лицензии/аттестата.
    """

    def __init__(
        self,
        full_name: str,
        role: CrewRole,
        license_number: str,
    ) -> None:
        self._validate_name(full_name)
        self._validate_license(license_number)

        self._full_name = full_name
        self._role = role
        self._license_number = license_number
        self._is_on_duty = False
        self._current_duties: list[str] = []

    @staticmethod
    def _validate_name(name: str) -> None:
        """Валидация имени."""
        if not name or not name.strip():
            raise ValidationError("full_name", "Name cannot be empty")
        if len(name.strip()) < 3:
            raise ValidationError(
                "full_name", "Name must be at least 3 characters"
            )

    @staticmethod
    def _validate_license(license_num: str) -> None:
        """Валидация номера лицензии."""
        if not license_num or not license_num.strip():
            raise ValidationError(
                "license_number", "License number cannot be empty"
            )
        if len(license_num) < 4:
            raise ValidationError(
                "license_number", "License number too short"
            )

    @property
    def full_name(self) -> str:
        """Получить полное имя."""
        return self._full_name

    @property
    def role(self) -> CrewRole:
        """Получить роль."""
        return self._role

    @property
    def license_number(self) -> str:
        """Получить номер лицензии."""
        return self._license_number

    @property
    def is_on_duty(self) -> bool:
        """Проверить, на дежурстве ли член экипажа."""
        return self._is_on_duty

    def get_role(self) -> CrewRole:
        """Получить роль (метод-версия)."""
        return self._role

    def start_duty(self) -> bool:
        """
        Начать дежурство.

        Returns:
            True если успешно.
        """
        if self._is_on_duty:
            return False
        self._is_on_duty = True
        self._current_duties = []
        return True

    def end_duty(self) -> bool:
        """
        Закончить дежурство.

        Returns:
            True если успешно.
        """
        if not self._is_on_duty:
            return False
        self._is_on_duty = False
        self._current_duties = []
        return True

    def perform_duty(self, duty_type: str) -> Dict[str, str]:
        """
        Выполнить обязанность.

        Args:
            duty_type: Тип выполняемой обязанности.

        Returns:
            Словарь с результатом выполнения.

        Raises:
            CrewError: Если член экипажа не на дежурстве.
        """
        if not self._is_on_duty:
            raise CrewError(
                f"{self._full_name} cannot perform duties: not on duty"
            )

        self._current_duties.append(duty_type)

        return {
            "member": self._full_name,
            "role": self._role.name,
            "duty": duty_type,
            "status": "completed",
        }

    def can_fly(self) -> bool:
        """
        Проверить, может ли член экипажа лететь.

        Returns:
            True если на дежурстве и роль позволяет.
        """
        if not self._is_on_duty:
            return False
        # Пилоты, штурманы и инженеры могут летать
        fly_roles = {
            CrewRole.PILOT,
            CrewRole.CO_PILOT,
            CrewRole.NAVIGATOR,
            CrewRole.ENGINEER,
        }
        return self._role in fly_roles

    def __repr__(self) -> str:
        return (
            f"CrewMember(name={self._full_name!r}, "
            f"role={self._role.name}, "
            f"license={self._license_number}, "
            f"on_duty={self._is_on_duty})"
        )

    def __str__(self) -> str:
        duty_status = "on duty" if self._is_on_duty else "off duty"
        return (
            f"Crew: {self._full_name} | "
            f"Role: {self._role.name} | "
            f"License: {self._license_number} | {duty_status}"
        )
