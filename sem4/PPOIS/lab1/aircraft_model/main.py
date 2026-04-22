#!/usr/bin/env python3
"""
Интерактивный CLI для модели самолёта.
Демонстрация работы ООП-модели через командную строку.
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import uuid
from datetime import datetime, timedelta
from typing import Optional

# ============================================================================
# ИМПОРТЫ ИЗ МОДЕЛИ
# ============================================================================
from aircraft_model import (
    Aircraft,
    AircraftStatus,
    CrewMember,
    CrewRole,
    FlightRoute,
    InFlightService,
    Passenger,
    # Runway удалён
    # Исключения
    CapacityError,
    CrewError,
    FlightError,
    LandingError,
    RegistrationError,
    RunwayError,
    ServiceError,
    TakeoffError,
    ValidationError,
)
from aircraft_model.enums import ServiceType


# ============================================================================
# ФИКСИРОВАННЫЙ СПИСОК АЭРОПОРТОВ (Требование 4)
# ============================================================================
class Airport:
    """Фиксированный аэропорт."""
    SVO = "SVO"   # Шереметьево
    LED = "LED"   # Пулково
    DME = "DME"   # Домодедово
    VKO = "VKO"   # Внуково
    KZN = "KZN"   # Казань
    AER = "AER"   # Сочи

    @classmethod
    def all(cls) -> list[str]:
        """Все аэропорты."""
        return [cls.SVO, cls.LED, cls.DME, cls.VKO, cls.KZN, cls.AER]

    @classmethod
    def display_all(cls) -> str:
        """Строка для отображения."""
        return ", ".join(cls.all())

    AIRPORT_NAMES = {
        SVO: "Шереметьево (Москва)",
        LED: "Пулково (Санкт-Петербург)",
        DME: "Домодедово (Москва)",
        VKO: "Внуково (Москва)",
        KZN: "Казань",
        AER: "Сочи",
    }

    @classmethod
    def get_name(cls, code: str) -> str:
        """Получить название по коду."""
        return cls.AIRPORT_NAMES.get(code, code)


# ============================================================================
# РАССТОЯНИЯ МЕЖДУ АЭРОПОРТАМИ (для автоматического расчёта)
# ============================================================================
AIRPORT_DISTANCES: dict[tuple[str, str], float] = {
    # Москва - Санкт-Петербург
    (Airport.SVO, Airport.LED): 634.0,
    (Airport.DME, Airport.LED): 634.0,
    (Airport.VKO, Airport.LED): 634.0,
    # Москва - Казань
    (Airport.SVO, Airport.KZN): 720.0,
    (Airport.DME, Airport.KZN): 720.0,
    (Airport.VKO, Airport.KZN): 720.0,
    # Москва - Сочи
    (Airport.SVO, Airport.AER): 1362.0,
    (Airport.DME, Airport.AER): 1362.0,
    (Airport.VKO, Airport.AER): 1362.0,
    # СПб - Казань
    (Airport.LED, Airport.KZN): 1107.0,
    # СПб - Сочи
    (Airport.LED, Airport.AER): 1740.0,
    # Казань - Сочи
    (Airport.KZN, Airport.AER): 1200.0,
}


def get_distance(from_code: str, to_code: str) -> float:
    """Получить расстояние между аэропортами."""
    # Пробуем прямое направление
    if (from_code, to_code) in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[(from_code, to_code)]
    # Пробуем обратное
    if (to_code, from_code) in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[(to_code, from_code)]
    # По умолчанию
    return 800.0


# ============================================================================
# ПРОСТЫЕ ФУНКЦИИ ВЫВОДА (БЕЗ ЦВЕТОВ)
# ============================================================================

def header(text: str) -> None:
    print(f"\n--- {text} ---")


def info(text: str) -> None:
    print(f"[INFO] {text}")


def success(text: str) -> None:
    print(f"[OK] {text}")


def warning(text: str) -> None:
    print(f"[WARN] {text}")


def error(text: str) -> None:
    print(f"[ERROR] {text}")


def step(step_num: int, description: str) -> None:
    print(f"[STEP {step_num}] {description}")


# ============================================================================
# КЛАСС РЕЙСА (Flight)
# ============================================================================
class Flight:
    """Рейс, привязанный к конкретному самолёту."""

    def __init__(
        self,
        flight_number: str,
        aircraft: Aircraft,
        departure: str,
        destination: str,
        departure_time: datetime,
        distance_km: float = 0.0,
    ) -> None:
        self.flight_number = flight_number.upper()
        self.aircraft = aircraft
        self.departure = departure.upper()
        self.destination = destination.upper()
        self.departure_time = departure_time
        self.arrival_time: Optional[datetime] = None
        self.passengers: list[Passenger] = []
        self._seats_taken: set[str] = set()
        # Данные маршрута
        self.distance_km = distance_km
        self.fuel_needed: float = 0.0
        self.duration_hours: float = 0.0
        self._calculate_route()

    def _calculate_route(self) -> None:
        """Автоматический расчёт маршрута (Требование 7)."""
        self.distance_km = get_distance(self.departure, self.destination)
        # Топливо: ~3.5 л/км + 10% резерв
        self.fuel_needed = self.distance_km * 3.5 * 1.1
        # Время: ~800 км/ч
        self.duration_hours = self.distance_km / 800.0

    def add_passenger(self, passenger: Passenger) -> None:
        """Добавить пассажира на рейс."""
        self.passengers.append(passenger)
        self._seats_taken.add(passenger.seat_number.upper())

    def is_seat_taken(self, seat: str) -> bool:
        """Проверить, занято ли место."""
        return seat.upper() in self._seats_taken

    def is_passenger_on_flight(self, passport: str) -> bool:
        """Проверить, есть ли пассажир на рейсе."""
        passport = passport.upper()
        return any(p.passport_number.upper() == passport for p in self.passengers)

    def get_passenger_count(self) -> int:
        return len(self.passengers)

    def __repr__(self) -> str:
        return (
            f"Flight({self.flight_number}: {self.departure}->{self.destination}, "
            f"aircraft={self.aircraft.tail_number}, passengers={self.get_passenger_count()})"
        )

    def __str__(self) -> str:
        time_str = self.departure_time.strftime("%Y-%m-%d %H:%M")
        hours = int(self.duration_hours)
        minutes = int((self.duration_hours % 1) * 60)
        return (
            f"Рейс: {self.flight_number} | {self.departure} -> {self.destination} | "
            f"Вылет: {time_str} | Борт: {self.aircraft.tail_number} | "
            f"{self.distance_km:.0f}км | ~{hours}h {minutes}m"
        )


# ============================================================================
# КЛАСС УПРАВЛЕНИЯ СОСТОЯНИЕМ СИСТЕМЫ
# ============================================================================
class SystemState:
    """
    Хранит состояние всех созданных объектов сессии.
    Singleton для доступа из любого места программы.
    """

    _instance: Optional["SystemState"] = None

    def __new__(cls) -> "SystemState":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.aircraft: dict[str, Aircraft] = {}
        self.passengers: dict[str, Passenger] = {}
        self.tickets: dict[str, Passenger] = {}
        self.crew_members: dict[str, CrewMember] = {}
        self.flights: dict[str, Flight] = {}
        self.in_flight_services: dict[str, InFlightService] = {}

    def reset(self) -> None:
        self._init()
        info("Состояние системы сброшено")

    # =========================================================================
    # ВАЛИДАЦИЯ УНИКАЛЬНОСТИ
    # =========================================================================
    def is_tail_number_exists(self, tail_number: str) -> bool:
        return tail_number.upper() in self.aircraft

    def is_flight_number_exists(self, flight_number: str) -> bool:
        return flight_number.upper() in self.flights

    def is_passport_exists(self, passport: str) -> bool:
        return passport.upper() in self.passengers

    def is_license_exists(self, license_num: str) -> bool:
        return license_num.upper() in self.crew_members

    # =========================================================================
    # ГЕТТЕРЫ
    # =========================================================================
    def get_aircraft(self, identifier: str = None) -> Optional[Aircraft]:
        if not identifier:
            return None
        identifier = identifier.upper()
        if identifier in self.aircraft:
            return self.aircraft[identifier]
        for aircraft in self.aircraft.values():
            if aircraft.tail_number == identifier:
                return aircraft
        return None

    def get_flight(self, flight_number: str = None) -> Optional[Flight]:
        if not flight_number:
            return None
        return self.flights.get(flight_number.upper())

    def get_flight_by_aircraft(self, aircraft: Aircraft) -> Optional[Flight]:
        """Найти рейс по самолёту (Требование 6)."""
        for flight in self.flights.values():
            if flight.aircraft.tail_number == aircraft.tail_number:
                return flight
        return None

    def get_passenger(self, passport: str = None) -> Optional[Passenger]:
        if not passport:
            return None
        return self.passengers.get(passport.upper())

    # =========================================================================
    # СВОДКА (Требование 2 - привязка к самолёту)
    # =========================================================================
    def summary(self) -> None:
        header("СОСТОЯНИЕ СИСТЕМЫ")

        if self.aircraft:
            print("\nСамолёты:")
            for aid, aircraft in self.aircraft.items():
                print(f"  [{aid}] {aircraft}")
        else:
            print("\nСамолёты: нет")

        if self.flights:
            print("\nРейсы:")
            for fid, flight in self.flights.items():
                print(f"  [{fid}] {flight}")
        else:
            print("\nРейсы: нет")

        if self.passengers:
            print("\nПассажиры:")
            for pid, passenger in self.passengers.items():
                # Требование 2: добавляем привязку к самолёту
                aircraft_code = ""
                for flight in self.flights.values():
                    if flight.is_passenger_on_flight(pid):
                        aircraft_code = flight.aircraft.tail_number
                        break
                print(f"  [{pid}] Passenger: {passenger.full_name} | Passport: {pid} | "
                      f"Aircraft: {aircraft_code} | Seat: {passenger.seat_number or '-'} | "
                      f"Status: {'registered' if passenger.is_registered else 'not registered'}")
        else:
            print("\nПассажиры: нет")

        if self.crew_members:
            print("\nЭкипаж:")
            for cid, crew in self.crew_members.items():
                # Требование 2: добавляем привязку к самолёту
                aircraft_code = ""
                for aircraft in self.aircraft.values():
                    for cm in aircraft.crew:
                        if cm.license_number == cid:
                            aircraft_code = aircraft.tail_number
                            break
                duty_status = "on duty" if crew.is_on_duty else "off duty"
                print(f"  [{cid}] Crew: {crew.full_name} | Role: {crew.role.name} | "
                      f"License: {cid} | Aircraft: {aircraft_code} | {duty_status}")
        else:
            print("\nЭкипаж: нет")


# Глобальный экземпляр состояния
state = SystemState()


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВВОДА С ВАЛИДАЦИЕЙ
# ============================================================================
def safe_input(prompt: str) -> Optional[str]:
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print()
        return None


def get_choice(menu_items: int = 10) -> Optional[int]:
    try:
        choice = input("> ").strip()
        if choice == "":
            return None
        return int(choice)
    except ValueError:
        return None
    except KeyboardInterrupt:
        return None


def input_while_empty(prompt: str) -> Optional[str]:
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        if value.strip():
            return value.strip()
        warning("Поле не может быть пустым.")


def input_while_not_number(prompt: str, is_float: bool = False) -> Optional[float]:
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        try:
            if is_float:
                return float(value)
            else:
                return int(value)
        except ValueError:
            warning("Введите число.")


def input_until_valid_seat(
    prompt: str,
    existing_seats: set[str],
    capacity: int
) -> Optional[str]:
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        value = value.strip().upper()
        if not value:
            warning("Место не может быть пустым.")
            continue
        if len(value) < 2 or len(value) > 3:
            warning("Неверный формат места. Пример: 12A")
            continue
        if not value[-1].isalpha():
            warning("Место должно заканчиваться буквой.")
            continue
        row_part = value[:-1]
        if not row_part.isdigit():
            warning("Ряд должен быть числом.")
            continue
        if value in existing_seats:
            warning(f"Место {value} уже занято.")
            continue
        return value


def input_airport(prompt: str) -> Optional[str]:
    """Выбор аэропорта из списка (Требование 5)."""
    while True:
        print(f"\n{prompt}")
        print("Доступные аэропорты:")
        for i, code in enumerate(Airport.all(), 1):
            print(f"  {i} - {code} ({Airport.get_name(code)})")

        choice = safe_input("Выберите номер: ")
        if choice is None:
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(Airport.all()):
                return Airport.all()[idx]
            warning("Неверный номер.")
        except ValueError:
            warning("Введите номер.")


# ============================================================================
# ПУНКТЫ МЕНЮ
# ============================================================================

def menu_create_aircraft() -> None:
    """Пункт 1: Создать самолёт (с авто-экипажем)."""
    header("СОЗДАТЬ САМОЛЁТ")

    try:
        step(1, "Ввод данных самолёта")
        model = input_while_empty("Модель (например, Boeing 737-800): ")
        if model is None:
            return

        while True:
            tail = safe_input("Бортовой номер (например, RA-12345): ")
            if tail is None:
                return
            tail = tail.strip().upper()
            if not tail:
                warning("Бортовой номер не может быть пустым.")
                continue
            if state.is_tail_number_exists(tail):
                warning(f"Самолёт с бортовым номером {tail} уже существует!")
                continue
            break

        capacity = input_while_not_number("Вместимость (пассажиров): ")
        if capacity is None:
            return
        if capacity <= 0:
            error("Вместимость должна быть положительным числом")
            return

        step(2, "Создание самолёта")
        aircraft = Aircraft(model=model, tail_number=tail, capacity=int(capacity))
        state.aircraft[tail] = aircraft
        state.in_flight_services[tail] = aircraft.get_service()
        success(f"Самолёт создан: {aircraft.model} ({aircraft.tail_number})")

        step(3, "Автоматическое создание экипажа")
        _create_minimum_crew(aircraft)

        print(f"\n{aircraft}")

    except ValidationError as e:
        error(f"Ошибка валидации: {e.message}")
    except KeyboardInterrupt:
        pass


def _create_minimum_crew(aircraft: Aircraft) -> None:
    """Создать минимальный экипаж из 4 человек."""
    crew_data = [
        ("Первый пилот", CrewRole.PILOT, f"PLT-{uuid.uuid4().hex[:6].upper()}"),
        ("Второй пилот", CrewRole.CO_PILOT, f"CPT-{uuid.uuid4().hex[:6].upper()}"),
        ("Бортпроводник 1", CrewRole.FLIGHT_ATTENDANT, f"FA-{uuid.uuid4().hex[:6].upper()}"),
        ("Бортпроводник 2", CrewRole.FLIGHT_ATTENDANT, f"FA-{uuid.uuid4().hex[:6].upper()}"),
    ]

    for name, role, license_num in crew_data:
        crew = CrewMember(name, role, license_num)
        crew.start_duty()
        aircraft.add_crew_member(crew)
        state.crew_members[license_num] = crew
        print(f"[{license_num}] Crew: {name} | Role: {role.name} | "
              f"License: {license_num} | Aircraft: {aircraft.tail_number} | on duty")


def menu_add_crew_member() -> None:
    """Пункт 2: Добавить члена экипажа."""
    header("ДОБАВИТЬ ЧЛЕНА ЭКИПАЖА")

    try:
        if not state.aircraft:
            warning("Нет доступных самолётов. Сначала создайте самолёт.")
            return

        step(1, "Выбор самолёта")
        print("Доступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model} ({len(aircraft.crew)} чл. экипажа)")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер самолёта: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                warning(f"Самолёт {tail} не найден.")

        success(f"Выбран: {aircraft.model} ({aircraft.tail_number})")

        step(2, "Выбор должности")
        print("\n  1 - Пилот")
        print("  2 - Второй пилот")
        print("  3 - Штурман")
        print("  4 - Бортпроводник")
        print("  5 - Старший бортпроводник")
        print("  6 - Бортинженер")

        role_map = {
            "1": CrewRole.PILOT,
            "2": CrewRole.CO_PILOT,
            "3": CrewRole.NAVIGATOR,
            "4": CrewRole.FLIGHT_ATTENDANT,
            "5": CrewRole.LEAD_ATTENDANT,
            "6": CrewRole.ENGINEER,
        }

        role = None
        while role is None:
            role_choice = safe_input("\nВыберите должность (1-6): ")
            if role_choice is None:
                return
            role = role_map.get(role_choice)
            if not role:
                warning("Неизвестная должность. Введите 1-6.")

        step(3, "Ввод данных")
        name = input_while_empty("ФИО: ")
        if name is None:
            return

        license_num = None
        while license_num is None:
            lic = safe_input("Номер лицензии: ")
            if lic is None:
                return
            lic = lic.strip().upper()
            if not lic:
                warning("Номер лицензии не может быть пустым.")
                continue
            if state.is_license_exists(lic):
                warning(f"Лицензия {lic} уже существует!")
                continue
            license_num = lic

        step(4, "Создание")
        crew = CrewMember(full_name=name, role=role, license_number=license_num)
        success(f"Создан: {crew.full_name} ({crew.role.name})")

        if aircraft.add_crew_member(crew):
            state.crew_members[license_num] = crew
            success(f"Добавлен в экипаж {aircraft.tail_number}")
        else:
            warning("Ошибка добавления.")

        start = safe_input("\nВыйти на дежурство? (y/n): ")
        if start and start.lower() == 'y':
            crew.start_duty()
            success("На дежурстве")

        print(f"\n{aircraft}")

    except ValidationError as e:
        error(f"Ошибка валидации: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_create_flight() -> None:
    """Пункт 3: Выпустить рейс (с автоматическим расчётом маршрута)."""
    header("ВЫПУСТИТЬ РЕЙС")

    try:
        if not state.aircraft:
            warning("Нет доступных самолётов. Сначала создайте самолёт.")
            return

        step(1, "Выбор самолёта")
        print("Доступные самолёты:")
        for key, aircraft in state.aircraft.items():
            # Проверяем, есть ли уже рейс
            has_flight = state.get_flight_by_aircraft(aircraft)
            status = "(рейс есть)" if has_flight else ""
            print(f"  [{key}] {aircraft.model} {status}")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер самолёта: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                warning(f"Самолёт {tail} не найден.")

        # Проверяем, что нет рейса
        existing = state.get_flight_by_aircraft(aircraft)
        if existing:
            error(f"У самолёта {aircraft.tail_number} уже есть рейс {existing.flight_number}!")
            return

        success(f"Выбран: {aircraft.model} ({aircraft.tail_number})")

        # Номер рейса
        step(2, "Номер рейса")
        flight_number = None
        while flight_number is None:
            num = safe_input("Номер рейса (например, SU123): ")
            if num is None:
                return
            num = num.strip().upper()
            if not num:
                warning("Номер рейса не может быть пустым.")
                continue
            if state.is_flight_number_exists(num):
                warning(f"Рейс {num} уже существует!")
                continue
            flight_number = num

        # Выбор аэропортов (Требование 5)
        step(3, "Аэропорт вылета")
        departure = input_airport("Аэропорт вылета:")
        if departure is None:
            return

        step(4, "Аэропорт прилёта")
        destination = input_airport("Аэропорт прилёта:")
        if destination is None:
            return

        if departure == destination:
            error("Аэропорты вылета и прилёта совпадают!")
            return

        # Время вылета
        step(5, "Время вылета")
        print("Время вылета: сейчас + 24 часа (по умолчанию)")
        departure_time = datetime.now() + timedelta(hours=24)

        # Автоматический расчёт маршрута (Требование 7)
        step(6, "Расчёт маршрута")
        distance = get_distance(departure, destination)
        fuel = distance * 3.5 * 1.1
        duration_hours = distance / 800.0
        hours = int(duration_hours)
        minutes = int((duration_hours % 1) * 60)

        info(f"Расстояние: {distance:.0f} км")
        info(f"Топливо: {fuel:.0f} л (с резервом)")
        info(f"Время полёта: ~{hours}h {minutes}m")

        # Создание рейса
        step(7, "Создание рейса")
        flight = Flight(
            flight_number=flight_number,
            aircraft=aircraft,
            departure=departure,
            destination=destination,
            departure_time=departure_time,
            distance_km=distance,
        )
        # Привязываем маршрут к самолёту (для preflight_check)
        from aircraft_model import FlightRoute
        route = FlightRoute(departure, destination, distance)
        aircraft.set_route(route)

        state.flights[flight_number] = flight

        success(f"Рейс создан: {flight}")

    except ValidationError as e:
        error(f"Ошибка: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_register_passenger() -> None:
    """Пункт 4: Зарегистрировать пассажира на рейс."""
    header("ЗАРЕГИСТРИРОВАТЬ ПАССАЖИРА НА РЕЙС")

    try:
        if not state.flights:
            warning("Нет доступных рейсов. Сначала создайте рейс.")
            return

        step(1, "Выбор рейса")
        print("Доступные рейсы:")
        for fid, flight in state.flights.items():
            available = flight.aircraft.capacity - flight.get_passenger_count()
            print(f"  [{fid}] {flight.departure} -> {flight.destination} "
                  f"(свободно: {available})")

        flight = None
        while flight is None:
            flight_num = safe_input("\nНомер рейса: ")
            if flight_num is None:
                return
            flight = state.get_flight(flight_num)
            if not flight:
                warning(f"Рейс {flight_num} не найден.")

        success(f"Выбран: {flight.flight_number}")

        if flight.get_passenger_count() >= flight.aircraft.capacity:
            error("Самолёт полностью загружен!")
            return

        step(2, "Данные пассажира")
        name = input_while_empty("ФИО: ")
        if name is None:
            return

        passport = None
        while passport is None:
            pas = safe_input("Номер паспорта: ")
            if pas is None:
                return
            pas = pas.strip().upper()
            if not pas:
                warning("Номер паспорта не может быть пустым.")
                continue
            if state.is_passport_exists(pas):
                warning(f"Пассажир с паспортом {pas} уже зарегистрирован!")
                continue
            passport = pas

        if flight.is_passenger_on_flight(passport):
            error(f"Пассажир с паспортом {passport} уже на рейсе {flight.flight_number}!")
            return

        step(3, "Выбор места")
        occupied_seats = flight._seats_taken.copy()
        available = flight.aircraft.capacity - flight.get_passenger_count()
        print(f"Свободных мест: {available}")

        seat = input_until_valid_seat(
            "Место (например, 12A): ",
            occupied_seats,
            flight.aircraft.capacity
        )
        if seat is None:
            return

        success(f"Выбрано место: {seat}")

        step(4, "Регистрация")
        passenger = Passenger(
            full_name=name,
            passport_number=passport,
            ticket_number=f"TKT-{uuid.uuid4().hex[:8].upper()}",
            seat_number=seat,
        )
        passenger.register_for_flight()
        state.passengers[passport] = passenger

        # Добавляем пассажира в самолёт (для внутреннего счётчика Aircraft)
        flight.aircraft.add_passenger(passenger)
        flight.add_passenger(passenger)
        success(f"Пассажир {passenger.full_name} зарегистрирован!")

        # Требование 1: отображение количества пассажиров
        print(f"\n[INFO] На борту самолёта {flight.aircraft.tail_number} "
              f"теперь {flight.get_passenger_count()} пассажиров")

        print(f"\n{passenger}")

    except ValidationError as e:
        error(f"Ошибка: {e.message}")
    except RegistrationError as e:
        error(f"Ошибка: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_takeoff_landing() -> None:
    """Пункт 5: Запросить взлёт или посадку (БЕЗ ВПП - Требование 3)."""
    header("ВЗЛЁТ ИЛИ ПОСАДКА")

    try:
        print("1 - Запросить взлёт")
        print("2 - Запросить посадку")
        op = safe_input("\nВыберите (1/2): ")
        if op is None:
            return

        if not state.aircraft:
            warning("Нет доступных самолётов")
            return

        print("Доступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model} ({aircraft.status.name})")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                warning(f"Самолёт {tail} не найден.")

        info(f"Текущий статус: {aircraft.status.name}")

        if op == "1":
            _do_takeoff(aircraft)
        elif op == "2":
            _do_landing(aircraft)

    except (TakeoffError, LandingError) as e:
        error(f"Операция невозможна: {e.message}")
    except KeyboardInterrupt:
        pass


def _do_takeoff(aircraft: Aircraft) -> None:
    """Выполнить взлёт (Требование 6 - проверка рейса)."""
    if not aircraft.crew:
        warning("Нет экипажа!")
        return

    if aircraft.status != AircraftStatus.ON_GROUND:
        error(f"Самолёт не на земле (статус: {aircraft.status.name})")
        return

    # Требование 6: проверка рейса
    flight = state.get_flight_by_aircraft(aircraft)
    if not flight:
        error("Нет зарегистрированного рейса для этого самолёта!")
        return

    success("Рейс подтверждён")

    checks = aircraft.preflight_check()
    for check_name, result in checks.items():
        status = "OK" if result else "FAIL"
        print(f"  [{status}] {check_name}")

    if not all(checks.values()):
        error("Предполётная проверка не пройдена!")
        return

    aircraft.take_off()
    success(f"Взлёт выполнен! Статус: {aircraft.status.name}")
    print(aircraft)


def _do_landing(aircraft: Aircraft) -> None:
    """Выполнить посадку с очисткой рейса."""
    if aircraft.status != AircraftStatus.IN_FLIGHT:
        error(f"Самолёт не в воздухе (статус: {aircraft.status.name})")
        return

    aircraft.land()
    success(f"Посадка выполнена! Статус: {aircraft.status.name}")

    # Очищаем пассажиров и маршрут
    aircraft._passengers.clear()
    aircraft._flight_route = None

    # Удаляем рейс из state для этого самолёта
    for flight_num, flight in list(state.flights.items()):
        if flight.aircraft.tail_number == aircraft.tail_number:
            del state.flights[flight_num]
            break

    success("Рейс завершён. Пассажиры и маршрут очищены.")
    info("Самолёт и экипаж готовы к повторному использованию.")

    print(aircraft)


def menu_inflight_service() -> None:
    """Пункт 6: Бортовое обслуживание."""
    header("БОРТОВОЕ ОБСЛУЖИВАНИЕ")

    try:
        if not state.aircraft:
            warning("Нет доступных самолётов")
            return

        print("Доступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model}")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                warning(f"Самолёт {tail} не найден.")

        service = aircraft.get_service()

        print("\nУслуги:")
        print("  1 - Питание")
        print("  2 - Напитки")
        print("  3 - Помощь")
        print("  4 - Wi-Fi")
        print("  5 - Показать инвентарь")

        svc_choice = safe_input("\nВыберите (1-5): ")
        if svc_choice is None:
            return

        passenger_id = safe_input("ID пассажира (Enter - демо): ") or "DEMO-PASS"

        print("\nИнвентарь:")
        for st in ServiceType:
            qty = service.get_quantity(st)
            print(f"  {st.name}: {qty}")

        if svc_choice == "1":
            result = service.provide_meal("горячее питание")
        elif svc_choice == "2":
            result = service.provide_beverage("кофе")
        elif svc_choice == "3":
            result = service.assist_passenger("general")
        elif svc_choice == "4":
            result = service.provide_wifi(passenger_id)
        elif svc_choice == "5":
            print(service)
            return
        else:
            error("Неизвестная услуга")
            return

        success(f"Услуга предоставлена: {result}")

        stats = service.get_stats()
        for svc_type, count in stats.items():
            if count > 0:
                print(f"  {svc_type.name}: {count}")

    except ServiceError as e:
        error(f"Услуга недоступна: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_safety_check() -> None:
    """Пункт 7: Проверка безопасности."""
    header("ПРОВЕРКА БЕЗОПАСНОСТИ")

    try:
        if not state.aircraft:
            warning("Нет доступных самолётов")
            return

        print("Самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model}")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                warning(f"Самолёт {tail} не найден.")

        checks = aircraft.preflight_check()
        all_passed = True

        for check_name, result in checks.items():
            status = "OK" if result else "FAIL"
            print(f"  [{status}] {check_name}")
            if not result:
                all_passed = False

        # Проверка рейса
        flight = state.get_flight_by_aircraft(aircraft)
        if flight:
            print(f"  [OK] flight_assigned: рейс {flight.flight_number}")
        else:
            print(f"  [FAIL] flight_assigned: нет рейса")
            all_passed = False

        if all_passed:
            success("Все проверки пройдены!")
        else:
            warning("Не все проверки пройдены.")

        print(f"\n{aircraft.model} | пассажиров: {aircraft.get_passenger_count()} | "
              f"экипажа: {len(aircraft.crew)} | статус: {aircraft.status.name}")

    except KeyboardInterrupt:
        pass


def menu_show_state() -> None:
    """Пункт 8: Состояние системы."""
    state.summary()


def menu_load_demo() -> None:
    """Пункт 9: Загрузить демо-данные."""
    header("ЗАГРУЗКА ДЕМО-ДАННЫХ")

    try:
        info("Очистка предыдущего состояния...")
        state.reset()

        # Самолёт
        aircraft = Aircraft(
            model="Boeing 737-800",
            tail_number="RA-737MM",
            capacity=150,
        )
        aircraft.set_airport("SVO")
        state.aircraft["RA-737MM"] = aircraft
        state.in_flight_services["RA-737MM"] = aircraft.get_service()
        success(f"Самолёт: {aircraft.tail_number}")

        # Авто-экипаж
        print("\nЭкипаж:")
        _create_minimum_crew(aircraft)

        # Рейс с автоматическим расчётом
        distance = get_distance("SVO", "LED")
        flight = Flight(
            flight_number="SU737",
            aircraft=aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=2),
            distance_km=distance,
        )
        # Привязываем маршрут к самолёту
        from aircraft_model import FlightRoute
        route = FlightRoute("SVO", "LED", distance)
        aircraft.set_route(route)

        state.flights["SU737"] = flight
        print(f"\nМаршрут: {distance:.0f} км, "
              f"топливо: {distance * 3.5 * 1.1:.0f} л, "
              f"время: ~{distance/800:.1f}ч")
        success(f"Рейс: {flight}")

        # Пассажиры
        print("\nПассажиры:")
        passengers_data = [
            ("Михаил Петров", "MP1234567", "15A"),
            ("Ольга Иванова", "OI2345678", "15B"),
            ("Сергей Козлов", "SK3456789", "15C"),
        ]
        for name, passport, seat in passengers_data:
            p = Passenger(name, passport, f"TKT-{uuid.uuid4().hex[:6].upper()}", seat)
            p.register_for_flight()
            aircraft.add_passenger(p)
            flight.add_passenger(p)
            state.passengers[passport] = p
            success(f"  {name}, место {seat}")

        success("\nДемо-данные загружены!")

    except Exception as e:
        error(f"Ошибка: {e}")


def print_menu() -> None:
    """Вывести меню (без пункта планирования маршрута - Требование 7)."""
    print("\n=== МЕНЮ ===")
    print("1. Создать самолёт")
    print("2. Добавить члена экипажа")
    print("3. Выпустить рейс")
    print("4. Зарегистрировать пассажира на рейс")
    print("5. Запросить взлёт или посадку")
    print("6. Бортовое обслуживание")
    print("7. Проверка безопасности")
    print("8. Состояние системы")
    print("9. Загрузить демо-данные")
    print("0. Выход")
    print("=============")


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================
def main() -> None:
    """Главная функция CLI."""
    print("\n=== АВИАЦИОННАЯ МОДЕЛЬ ===")
    info("Введите номер пункта меню (0-9)")
    info("Ctrl+C или 0 для выхода")

    while True:
        try:
            print_menu()
            choice = get_choice()

            if choice is None:
                warning("Введите номер пункта")
                continue

            if choice == 0:
                header("ВЫХОД")
                success("До свидания!")
                break
            elif choice == 1:
                menu_create_aircraft()
            elif choice == 2:
                menu_add_crew_member()
            elif choice == 3:
                menu_create_flight()
            elif choice == 4:
                menu_register_passenger()
            elif choice == 5:
                menu_takeoff_landing()
            elif choice == 6:
                menu_inflight_service()
            elif choice == 7:
                menu_safety_check()
            elif choice == 8:
                menu_show_state()
            elif choice == 9:
                menu_load_demo()
            else:
                warning(f"Неизвестный пункт: {choice}")

        except KeyboardInterrupt:
            print("\n[Ctrl+C] Нажмите 0 для выхода")
            continue

    print("Сеанс завершён.\n")


if __name__ == "__main__":
    main()
