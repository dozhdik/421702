"""
Класс InFlightService (Бортовой сервис).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .enums import ServiceType
from .exceptions import ServiceError, ValidationError


class InFlightService:
    """
    Управляет бортовыми услугами и инвентарём.

    Атрибуты:
        available_services: Список доступных услуг.
        inventory: Словарь остатков по типам услуг.
    """

    # Начальные значения инвентаря
    DEFAULT_INVENTORY: Dict[ServiceType, int] = {
        ServiceType.MEAL: 100,
        ServiceType.BEVERAGE: 200,
        ServiceType.ENTERTAINMENT: 50,
        ServiceType.ASSISTANCE: 100,
        ServiceType.DUTY_FREE: 50,
        ServiceType.WIFI: 150,
        ServiceType.SPECIAL_ASSISTANCE: 20,
    }

    def __init__(self) -> None:
        self._inventory: Dict[ServiceType, int] = (
            self.DEFAULT_INVENTORY.copy()
        )
        self._available_services: List[ServiceType] = list(
            ServiceType
        )
        self._services_provided: Dict[ServiceType, int] = {
            st: 0 for st in ServiceType
        }

    @property
    def available_services(self) -> List[str]:
        """Получить список доступных услуг."""
        return [st.name for st in self._available_services]

    @property
    def inventory(self) -> Dict[str, int]:
        """Получить копию инвентаря."""
        return {st.name: qty for st, qty in self._inventory.items()}

    def check_supplies(self, service_type: ServiceType) -> bool:
        """
        Проверить наличие услуги.

        Args:
            service_type: Тип услуги.

        Returns:
            True если услуга доступна.
        """
        return self._inventory.get(service_type, 0) > 0

    def get_quantity(self, service_type: ServiceType) -> int:
        """
        Получить остаток услуги.

        Args:
            service_type: Тип услуги.

        Returns:
            Количество в наличии.
        """
        return self._inventory.get(service_type, 0)

    def restock(self, service_type: ServiceType, quantity: int) -> None:
        """
        Пополнить запасы.

        Args:
            service_type: Тип услуги.
            quantity: Количество для добавления.

        Raises:
            ValidationError: Если количество <= 0.
            ServiceError: Если услуга не найдена.
        """
        if quantity <= 0:
            raise ValidationError(
                "quantity", "Restock quantity must be positive"
            )

        if service_type not in self._inventory:
            raise ServiceError(
                f"Service type {service_type.name} not found"
            )

        self._inventory[service_type] += quantity

    def _use_supply(self, service_type: ServiceType, amount: int = 1) -> None:
        """Использовать запасы (внутренний метод)."""
        if self._inventory.get(service_type, 0) < amount:
            raise ServiceError(
                f"Insufficient supply for {service_type.name}: "
                f"requested {amount}, available {self._inventory.get(service_type, 0)}"
            )
        self._inventory[service_type] -= amount

    def provide_meal(self, meal_type: str) -> Dict[str, str]:
        """
        Предоставить питание.

        Args:
            meal_type: Тип питания.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна.
        """
        if not self.check_supplies(ServiceType.MEAL):
            raise ServiceError("Meals are out of stock")

        self._use_supply(ServiceType.MEAL)
        self._services_provided[ServiceType.MEAL] += 1

        return {
            "service": "MEAL",
            "type": meal_type,
            "status": "provided",
        }

    def assist_passenger(self, request: str) -> Dict[str, str]:
        """
        Оказать помощь пассажиру.

        Args:
            request: Тип запроса.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна.
        """
        # Проверяем тип помощи
        if request.lower() in ("wheelchair", "special", "medical"):
            service_type = ServiceType.SPECIAL_ASSISTANCE
        else:
            service_type = ServiceType.ASSISTANCE

        if not self.check_supplies(service_type):
            raise ServiceError(
                f"Assistance service ({request}) is not available"
            )

        self._use_supply(service_type)
        self._services_provided[service_type] += 1

        return {
            "service": service_type.name,
            "request": request,
            "status": "provided",
        }

    def provide_beverage(self, beverage_type: str) -> Dict[str, str]:
        """
        Предоставить напиток.

        Args:
            beverage_type: Тип напитка.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна.
        """
        if not self.check_supplies(ServiceType.BEVERAGE):
            raise ServiceError("Beverages are out of stock")

        self._use_supply(ServiceType.BEVERAGE)
        self._services_provided[ServiceType.BEVERAGE] += 1

        return {
            "service": "BEVERAGE",
            "type": beverage_type,
            "status": "provided",
        }

    def provide_entertainment(self, passenger_id: str) -> Dict[str, str]:
        """
        Предоставить развлечения.

        Args:
            passenger_id: ID пассажира.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна.
        """
        if not self.check_supplies(ServiceType.ENTERTAINMENT):
            raise ServiceError("Entertainment system unavailable")

        self._use_supply(ServiceType.ENTERTAINMENT)

        return {
            "service": "ENTERTAINMENT",
            "passenger": passenger_id,
            "status": "activated",
        }

    def provide_wifi(self, passenger_id: str) -> Dict[str, str]:
        """
        Предоставить Wi-Fi.

        Args:
            passenger_id: ID пассажира.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна.
        """
        if not self.check_supplies(ServiceType.WIFI):
            raise ServiceError("Wi-Fi is not available")

        self._use_supply(ServiceType.WIFI)

        return {
            "service": "WIFI",
            "passenger": passenger_id,
            "status": "connected",
        }

    def get_stats(self) -> Dict[str, int]:
        """Получить статистику предоставленных услуг."""
        return self._services_provided.copy()

    def __repr__(self) -> str:
        return f"InFlightService(inventory={self._inventory})"

    def __str__(self) -> str:
        lines = ["In-Flight Services:", "  Inventory:"]
        for service, qty in self._inventory.items():
            lines.append(f"    {service.name}: {qty}")

        lines.append("  Statistics:")
        for service, count in self._services_provided.items():
            if count > 0:
                lines.append(f"    {service.name}: {count} provided")

        return "\n".join(lines)
