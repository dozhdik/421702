"""
Кастомные исключения для модели самолёта.
Иерархия исключений для разных типов ошибок.
"""


class FlightError(Exception):
    """Базовый класс для всех ошибок, связанных с полётами."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ValidationError(FlightError):
    """Ошибка валидации данных."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation error in '{field}': {message}")


class RegistrationError(FlightError):
    """Ошибка регистрации пассажира."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Registration error: {message}")


class TakeoffError(FlightError):
    """Ошибка при взлёте."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Takeoff error: {message}")


class LandingError(FlightError):
    """Ошибка при посадке."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Landing error: {message}")


class ServiceError(FlightError):
    """Ошибка бортового сервиса."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Service error: {message}")


class CrewError(FlightError):
    """Ошибка, связанная с экипажем."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Crew error: {message}")


class CapacityError(FlightError):
    """Ошибка превышения вместимости."""

    def __init__(self, capacity: int, requested: int) -> None:
        super().__init__(
            f"Capacity exceeded: requested {requested}, available {capacity}"
        )
