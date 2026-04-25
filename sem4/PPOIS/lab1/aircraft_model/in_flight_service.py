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
        ServiceType.MEAL: 150,
        ServiceType.BEVERAGE: 150,
        ServiceType.ASSISTANCE: 150,
        ServiceType.WIFI: 150,
    }

    # Лимиты услуг на пассажира
    SERVICE_LIMITS: Dict[ServiceType, int] = {
        ServiceType.MEAL: 1,
        ServiceType.BEVERAGE: 5,
        ServiceType.ASSISTANCE: 5,
        ServiceType.WIFI: 1,
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
        self._passenger_usage: Dict[str, Dict[ServiceType, int]] = {}

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

    def _check_passenger_limit(self, passenger_id: str, service_type: ServiceType) -> None:
        """Проверить лимит услуги для пассажира."""
        if passenger_id not in self._passenger_usage:
            self._passenger_usage[passenger_id] = {st: 0 for st in ServiceType}

        current_usage = self._passenger_usage[passenger_id][service_type]
        limit = self.SERVICE_LIMITS[service_type]

        if current_usage >= limit:
            service_names = {
                ServiceType.MEAL: "Питание",
                ServiceType.BEVERAGE: "Напитки",
                ServiceType.ASSISTANCE: "Помощь",
                ServiceType.WIFI: "Wi-Fi",
            }
            raise ServiceError(
                f"Пассажир уже использовал лимит услуги \"{service_names[service_type]}\" ({current_usage}/{limit})"
            )

    def _use_supply(self, service_type: ServiceType, amount: int = 1) -> None:
        """Использовать запасы (внутренний метод)."""
        if self._inventory.get(service_type, 0) < amount:
            raise ServiceError(
                f"Insufficient supply for {service_type.name}: "
                f"requested {amount}, available {self._inventory.get(service_type, 0)}"
            )
        self._inventory[service_type] -= amount

    def provide_meal(self, meal_type: str, passenger_id: str) -> Dict[str, str]:
        """
        Предоставить питание.

        Args:
            meal_type: Тип питания.
            passenger_id: ID пассажира.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна или превышен лимит.
        """
        self._check_passenger_limit(passenger_id, ServiceType.MEAL)

        if not self.check_supplies(ServiceType.MEAL):
            raise ServiceError("Meals are out of stock")

        self._use_supply(ServiceType.MEAL)
        self._services_provided[ServiceType.MEAL] += 1
        self._passenger_usage[passenger_id][ServiceType.MEAL] += 1

        return {
            "service": "MEAL",
            "type": meal_type,
            "status": "provided",
        }

    def assist_passenger(self, request: str, passenger_id: str) -> Dict[str, str]:
        """
        Оказать помощь пассажиру.

        Args:
            request: Тип запроса.
            passenger_id: ID пассажира.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна или превышен лимит.
        """
        self._check_passenger_limit(passenger_id, ServiceType.ASSISTANCE)

        if not self.check_supplies(ServiceType.ASSISTANCE):
            raise ServiceError(f"Assistance service ({request}) is not available")

        self._use_supply(ServiceType.ASSISTANCE)
        self._services_provided[ServiceType.ASSISTANCE] += 1
        self._passenger_usage[passenger_id][ServiceType.ASSISTANCE] += 1

        return {
            "service": ServiceType.ASSISTANCE.name,
            "request": request,
            "status": "provided",
        }

    def provide_beverage(self, beverage_type: str, passenger_id: str) -> Dict[str, str]:
        """
        Предоставить напиток.

        Args:
            beverage_type: Тип напитка.
            passenger_id: ID пассажира.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна или превышен лимит.
        """
        self._check_passenger_limit(passenger_id, ServiceType.BEVERAGE)

        if not self.check_supplies(ServiceType.BEVERAGE):
            raise ServiceError("Beverages are out of stock")

        self._use_supply(ServiceType.BEVERAGE)
        self._services_provided[ServiceType.BEVERAGE] += 1
        self._passenger_usage[passenger_id][ServiceType.BEVERAGE] += 1

        return {
            "service": "BEVERAGE",
            "type": beverage_type,
            "status": "provided",
        }

    def provide_wifi(self, passenger_id: str) -> Dict[str, str]:
        """
        Предоставить Wi-Fi.

        Args:
            passenger_id: ID пассажира.

        Returns:
            Словарь с результатом.

        Raises:
            ServiceError: Если услуга недоступна или превышен лимит.
        """
        self._check_passenger_limit(passenger_id, ServiceType.WIFI)

        if not self.check_supplies(ServiceType.WIFI):
            raise ServiceError("Wi-Fi is not available")

        self._use_supply(ServiceType.WIFI)
        self._passenger_usage[passenger_id][ServiceType.WIFI] += 1

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
