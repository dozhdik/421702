#!/usr/bin/env python3
"""
Интерактивный CLI для модели самолёта.
Демонстрация работы ООП-модели через командную строку.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import uuid
import re
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
    CapacityError,
    CrewError,
    FlightError,
    LandingError,
    RegistrationError,
    ServiceError,
    TakeoffError,
    ValidationError,
)
from aircraft_model.enums import ServiceType


# ============================================================================
# КОНСТАНТЫ: МОДЕЛИ САМОЛЁТОВ И АЭРОПОРТЫ
# ============================================================================

AVAILABLE_AIRCRAFT_MODELS = [
    "Boeing 737-800",
    "Airbus A320neo",
    "Sukhoi Superjet 100",
    "Boeing 777-300ER",
    "Airbus A380",
    "Ilyushin Il-96",
    "Tupolev Tu-204",
    "Embraer E190",
    "Bombardier CRJ900",
    "Airbus A220",
]

MODEL_CAPACITIES = {
    "Boeing 737-800": 150,
    "Airbus A320neo": 180,
    "Sukhoi Superjet 100": 98,
    "Boeing 777-300ER": 350,
    "Airbus A380": 525,
    "Ilyushin Il-96": 300,
    "Tupolev Tu-204": 210,
    "Embraer E190": 100,
    "Bombardier CRJ900": 90,
    "Airbus A220": 135,
}

AIRPORTS = {
    "SVO": "Шереметьево (Москва)",
    "DME": "Домодедово (Москва)",
    "VKO": "Внуково (Москва)",
    "LED": "Пулково (Санкт-Петербург)",
    "KZN": "Казань",
    "AER": "Сочи",
    "ROV": "Ростов-на-Дону",
    "KGD": "Калининград",
    "UFA": "Уфа",
    "OMS": "Омск",
}

AIRPORT_DISTANCES: dict[tuple[str, str], float] = {
    ("SVO", "LED"): 634.0, ("DME", "LED"): 634.0, ("VKO", "LED"): 634.0,
    ("SVO", "KZN"): 720.0, ("DME", "KZN"): 720.0, ("VKO", "KZN"): 720.0,
    ("SVO", "AER"): 1362.0, ("DME", "AER"): 1362.0, ("VKO", "AER"): 1362.0,
    ("SVO", "ROV"): 1200.0, ("DME", "ROV"): 1200.0, ("VKO", "ROV"): 1200.0,
    ("SVO", "UFA"): 1200.0, ("DME", "UFA"): 1200.0, ("VKO", "UFA"): 1200.0,
    ("LED", "KZN"): 1107.0,
    ("LED", "AER"): 1740.0,
    ("KZN", "AER"): 1200.0,
}


def get_airport_distance(from_code: str, to_code: str) -> float:
    if (from_code, to_code) in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[(from_code, to_code)]
    if (to_code, from_code) in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[(to_code, from_code)]
    return 800.0


def get_airport_list() -> list[str]:
    return list(AIRPORTS.keys())


# ============================================================================
# КЛАСС РЕЙСА (Flight)
# ============================================================================
class Flight:
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
        self.distance_km = distance_km
        self.fuel_needed: float = 0.0
        self.duration_hours: float = 0.0
        self._calculate_route()

    def _calculate_route(self) -> None:
        self.distance_km = get_airport_distance(self.departure, self.destination)
        self.fuel_needed = self.distance_km * 3.5 * 1.1
        self.duration_hours = self.distance_km / 800.0

    def add_passenger(self, passenger: Passenger) -> None:
        self.passengers.append(passenger)
        self._seats_taken.add(passenger.seat_number.upper())

    def is_seat_taken(self, seat: str) -> bool:
        return seat.upper() in self._seats_taken

    def is_passenger_on_flight(self, passport: str) -> bool:
        passport = passport.upper()
        return any(p.passport_number.upper() == passport for p in self.passengers)

    def get_passenger_count(self) -> int:
        return len(self.passengers)

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
    """Хранит состояние всех созданных объектов сессии."""
    
    _instance: Optional["SystemState"] = None 

    def __new__(cls) -> "SystemState":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.aircraft: dict[str, Aircraft] = {}
        self.passengers: dict[str, Passenger] = {}
        self.crew_members: dict[str, CrewMember] = {}
        self.flights: dict[str, Flight] = {}
        self.in_flight_services: dict[str, InFlightService] = {}

    def reset(self) -> None:
        self._init()

    def is_tail_number_exists(self, tail_number: str) -> bool:
        return tail_number.upper() in self.aircraft

    def is_flight_number_exists(self, flight_number: str) -> bool:
        return flight_number.upper() in self.flights

    def is_passport_exists(self, passport: str) -> bool:
        return passport.upper() in self.passengers

    def is_license_exists(self, license_num: str) -> bool:
        return license_num.upper() in self.crew_members

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
        for flight in self.flights.values():
            if flight.aircraft.tail_number == aircraft.tail_number:
                return flight
        return None

    def summary(self) -> None:
        print("\n--- Состояние системы ---")

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
                aircraft_code = ""
                for flight in self.flights.values():
                    if flight.is_passenger_on_flight(pid):
                        aircraft_code = flight.aircraft.tail_number
                        break
                print(f"  [{pid}] {passenger.full_name} | Паспорт: {pid} | "
                      f"Борт: {aircraft_code} | Место: {passenger.seat_number or '-'} | "
                      f"Статус: {'registered' if passenger.is_registered else 'not registered'}")
        else:
            print("\nПассажиры: нет")

        if self.crew_members:
            print("\nЭкипаж:")
            for cid, crew in self.crew_members.items():
                aircraft_code = ""
                for aircraft in self.aircraft.values():
                    for cm in aircraft.crew:
                        if cm.license_number == cid:
                            aircraft_code = aircraft.tail_number
                            break
                duty_status = "on duty" if crew.is_on_duty else "off duty"
                print(f"  [{cid}] {crew.full_name} | Должность: {crew.role.name} | "
                      f"Лицензия: {cid} | Борт: {aircraft_code} | {duty_status}")
        else:
            print("\nЭкипаж: нет")

state = SystemState()
state._instance = None  # Сброс синглтона при перезапуске в интерактивной сессии (если нужно)


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВВОДА
# ============================================================================

def safe_input(prompt: str) -> Optional[str]:
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print()
        return None


def get_choice() -> Optional[int]:
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
        print("Ошибка: поле не может быть пустым. Попробуйте ещё раз.")


def input_number(prompt: str) -> Optional[int]:
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            print("Ошибка: введите число.")


def input_menu_choice(options_count: int) -> Optional[int]:
    while True:
        value = safe_input("Выберите номер: ")
        if value is None:
            return None
        try:
            num = int(value)
            if 1 <= num <= options_count:
                return num
            print(f"Ошибка: введите число от 1 до {options_count}.")
        except ValueError:
            print("Ошибка: введите число.")


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
            print("Ошибка: место не может быть пустым.")
            continue
        if len(value) < 2 or len(value) > 3:
            print("Ошибка: неверный формат места. Пример: 12A")
            continue
        if not value[-1].isalpha():
            print("Ошибка: место должно заканчиваться буквой.")
            continue
        row_part = value[:-1]
        if not row_part.isdigit():
            print("Ошибка: ряд должен быть числом.")
            continue
        if value in existing_seats:
            print(f"Ошибка: место {value} уже занято.")
            continue
        return value


def is_valid_fio(text: str) -> bool:
    if not text or not (5 <= len(text) <= 50):
        return False
    return bool(re.match(r"^[а-яА-Яa-zA-Z\s\-]+$", text))


def is_valid_passport(text: str) -> bool:
    if not text or not (5 <= len(text) <= 15):
        return False
    return bool(re.match(r"^[а-яА-Яa-zA-Z0-9]+$", text))


def input_valid_fio(prompt: str) -> Optional[str]:
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        value = value.strip()
        if not value:
            print("Ошибка: поле не может быть пустым. Попробуйте ещё раз.")
            continue
        if is_valid_fio(value):
            return value
        print("Ошибка: некорректный формат. Попробуйте снова.")


def input_valid_passport(prompt: str) -> Optional[str]:
    while True:
        value = safe_input(prompt)
        if value is None:
            return None
        value = value.strip().upper()
        if not value:
            print("Ошибка: поле не может быть пустым. Попробуйте ещё раз.")
            continue
        if is_valid_passport(value):
            return value
        print("Ошибка: некорректный формат. Попробуйте снова.")


# ============================================================================
# ПУНКТЫ МЕНЮ
# ============================================================================

def menu_create_aircraft() -> None:
    print("\n--- Создать самолёт ---")
    try:
        print("\nВыберите модель самолёта:")
        for i, model in enumerate(AVAILABLE_AIRCRAFT_MODELS, 1):
            capacity = MODEL_CAPACITIES.get(model, 150)
            print(f"  {i}. {model} (вместимость: {capacity})")

        model_num = input_menu_choice(len(AVAILABLE_AIRCRAFT_MODELS))
        if model_num is None:
            return
        model = AVAILABLE_AIRCRAFT_MODELS[model_num - 1]
        capacity = MODEL_CAPACITIES.get(model, 150)

        while True:
            tail = safe_input("\nБортовой номер (например, RA-12345): ")
            if tail is None:
                return
            tail = tail.strip().upper()
            if not tail:
                print("Ошибка: бортовой номер не может быть пустым.")
                continue
            if state.is_tail_number_exists(tail):
                print(f"Ошибка: самолёт с бортовым номером {tail} уже существует!")
                continue
            break

        aircraft = Aircraft(model=model, tail_number=tail, capacity=capacity)
        state.aircraft[tail] = aircraft
        state.in_flight_services[tail] = aircraft.get_service()
        print(f"\nСамолёт создан: {aircraft.model} ({aircraft.tail_number}), вместимость: {capacity}")

        print("\nСоздание экипажа:")
        _create_minimum_crew(aircraft)
        print(f"\n{aircraft}")

    except ValidationError as e:
        print(f"Ошибка валидации: {e.message}")
    except KeyboardInterrupt:
        pass


def _create_minimum_crew(aircraft: Aircraft) -> None:
    crew_data = [
        ("Первый пилот", CrewRole.PILOT, f"PLT{uuid.uuid4().hex[:7].upper()}"),
        ("Второй пилот", CrewRole.CO_PILOT, f"CPT{uuid.uuid4().hex[:7].upper()}"),
        ("Бортпроводник 1", CrewRole.FLIGHT_ATTENDANT, f"FA{uuid.uuid4().hex[:8].upper()}"),
        ("Бортпроводник 2", CrewRole.FLIGHT_ATTENDANT, f"FA{uuid.uuid4().hex[:8].upper()}"),
    ]

    for name, role, license_num in crew_data:
        crew = CrewMember(name, role, license_num)
        crew.start_duty()
        aircraft.add_crew_member(crew)
        state.crew_members[license_num] = crew
        print(f"  [{license_num}] {name} | {role.name} | {aircraft.tail_number} | on duty")


def menu_add_crew_member() -> None:
    print("\n--- Добавить члена экипажа ---")
    try:
        if not state.aircraft:
            print("Нет доступных самолётов. Сначала создайте самолёт.")
            return

        print("\nДоступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model} ({len(aircraft.crew)} чл. экипажа)")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                print(f"Ошибка: самолёт {tail} не найден.")

        print(f"Выбран: {aircraft.model} ({aircraft.tail_number})")

        print("\nДолжности:")
        roles = [
            (CrewRole.PILOT, "Пилот"),
            (CrewRole.CO_PILOT, "Второй пилот"),
            (CrewRole.NAVIGATOR, "Штурман"),
            (CrewRole.FLIGHT_ATTENDANT, "Бортпроводник"),
            (CrewRole.LEAD_ATTENDANT, "Старший бортпроводник"),
            (CrewRole.ENGINEER, "Бортинженер"),
        ]
        for i, (role, name) in enumerate(roles, 1):
            print(f"  {i}. {name}")

        role_num = input_menu_choice(len(roles))
        if role_num is None:
            return
        role = roles[role_num - 1][0]

        # Проверка лимита пилотов
        pilot_count = sum(1 for m in aircraft.crew if m.role == CrewRole.PILOT)
        copilot_count = sum(1 for m in aircraft.crew if m.role == CrewRole.CO_PILOT)

        if role == CrewRole.PILOT and pilot_count >= 1:
            print("Ошибка: на борту уже есть пилот! Можно добавить только одного пилота.")
            return

        if role == CrewRole.CO_PILOT and copilot_count >= 1:
            print("Ошибка: на борту уже есть второй пилот! Можно добавить только одного второго пилота.")
            return

        name = input_valid_fio("\nФИО: ")
        if name is None:
            return

        while True:
            lic = safe_input("\nНомер лицензии: ")
            if lic is None:
                return
            lic = lic.strip().upper()
            if not lic:
                print("Ошибка: номер лицензии не может быть пустым.")
                continue
            if state.is_license_exists(lic):
                print(f"Ошибка: лицензия {lic} уже существует!")
                continue
            if state.is_passport_exists(lic):
                print(f"Ошибка: номер {lic} уже используется пассажиром!")
                continue
            if not is_valid_passport(lic):
                print("Ошибка: некорректный формат. Попробуйте снова.")
                continue
            break

        crew = CrewMember(full_name=name, role=role, license_number=lic)
        if aircraft.add_crew_member(crew):
            state.crew_members[lic] = crew
            print(f"Создан: {crew.full_name} ({crew.role.name})")
        else:
            print("Ошибка добавления в экипаж.")

        start = safe_input("\nВыйти на дежурство? (y/n): ")
        if start and start.lower() == 'y':
            crew.start_duty()
            print("На дежурстве.")

        print(f"\n{aircraft}")

    except ValidationError as e:
        print(f"Ошибка валидации: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_create_flight() -> None:
    print("\n--- Выпустить рейс ---")
    try:
        if not state.aircraft:
            print("Нет доступных самолётов. Сначала создайте самолёт.")
            return

        print("\nДоступные самолёты:")
        for key, aircraft in state.aircraft.items():
            has_flight = state.get_flight_by_aircraft(aircraft)
            status = "(рейс есть)" if has_flight else ""
            print(f"  [{key}] {aircraft.model} {status}")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                print(f"Ошибка: самолёт {tail} не найден.")

        existing = state.get_flight_by_aircraft(aircraft)
        if existing:
            print(f"Ошибка: у самолёта {aircraft.tail_number} уже есть рейс {existing.flight_number}!")
            return

        print(f"Выбран: {aircraft.model} ({aircraft.tail_number})")

        while True:
            num = safe_input("\nНомер рейса (например, SU123): ")
            if num is None:
                return
            num = num.strip().upper()
            if not num:
                print("Ошибка: номер рейса не может быть пустым.")
                continue
            if state.is_flight_number_exists(num):
                print(f"Ошибка: рейс {num} уже существует!")
                continue
            break
        flight_number = num

        print("\nАэропорт вылета:")
        airport_codes = get_airport_list()
        for i, code in enumerate(airport_codes, 1):
            name = AIRPORTS.get(code, code)
            print(f"  {i}. {code} - {name}")

        dep_num = input_menu_choice(len(airport_codes))
        if dep_num is None:
            return
        departure = airport_codes[dep_num - 1]

        print("\nАэропорт прилёта:")
        for i, code in enumerate(airport_codes, 1):
            name = AIRPORTS.get(code, code)
            print(f"  {i}. {code} - {name}")

        dest_num = input_menu_choice(len(airport_codes))
        if dest_num is None:
            return
        destination = airport_codes[dest_num - 1]

        while destination == departure:
            print("Ошибка: аэропорт вылета и прилёта совпадают! Выберите другой аэропорт прилёта.")
            print("\nАэропорт прилёта:")
            for i, code in enumerate(airport_codes, 1):
                name = AIRPORTS.get(code, code)
                print(f"  {i}. {code} - {name}")
            dest_num = input_menu_choice(len(airport_codes))
            if dest_num is None:
                return
            destination = airport_codes[dest_num - 1]

        print("\nВремя вылета: сейчас + 24 часа (по умолчанию)")
        departure_time = datetime.now() + timedelta(hours=24)

        distance = get_airport_distance(departure, destination)
        fuel = distance * 3.5 * 1.1
        duration_hours = distance / 800.0
        hours = int(duration_hours)
        minutes = int((duration_hours % 1) * 60)

        print(f"\nРасстояние: {distance:.0f} км")
        print(f"Топливо: {fuel:.0f} л (с резервом)")
        print(f"Время полёта: ~{hours}h {minutes}m")

        flight = Flight(
            flight_number=flight_number,
            aircraft=aircraft,
            departure=departure,
            destination=destination,
            departure_time=departure_time,
            distance_km=distance,
        )
        state.flights[flight_number] = flight
        aircraft.set_route(flight)
        print(f"\nРейс создан: {flight}")

    except ValidationError as e:
        print(f"Ошибка: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_register_passenger() -> None:
    print("\n--- Зарегистрировать пассажира на рейс ---")
    try:
        if not state.flights:
            print("Нет доступных рейсов. Сначала создайте рейс.")
            return

        print("\nДоступные рейсы:")
        for fid, flight in state.flights.items():
            available = flight.aircraft.capacity - flight.get_passenger_count()
            print(f"  [{fid}] {flight.departure} -> {flight.destination} (свободно: {available})")

        flight = None
        while flight is None:
            flight_num = safe_input("\nНомер рейса: ")
            if flight_num is None:
                return
            flight = state.get_flight(flight_num)
            if not flight:
                print(f"Ошибка: рейс {flight_num} не найден.")

        print(f"Выбран: {flight.flight_number}")

        if flight.get_passenger_count() >= flight.aircraft.capacity:
            print("Ошибка: самолёт полностью загружен!")
            return

        name = input_valid_fio("\nФИО: ")
        if name is None:
            return

        passport = input_valid_passport("\nНомер паспорта: ")
        if passport is None:
            return

        if state.is_passport_exists(passport):
            print(f"Ошибка: пассажир с паспортом {passport} уже зарегистрирован!")
            return

        if state.is_license_exists(passport):
            print(f"Ошибка: номер {passport} уже используется членом экипажа!")
            return

        if flight.is_passenger_on_flight(passport):
            print(f"Ошибка: пассажир с паспортом {passport} уже на рейсе {flight.flight_number}!")
            return

        occupied_seats = flight._seats_taken.copy()
        available = flight.aircraft.capacity - flight.get_passenger_count()
        print(f"\nСвободных мест: {available}")

        seat = input_until_valid_seat(
            "Место (например, 12A): ",
            occupied_seats,
            flight.aircraft.capacity
        )
        if seat is None:
            return

        print(f"Выбрано место: {seat}")

        passenger = Passenger(
            full_name=name,
            passport_number=passport,
            seat_number=seat,
        )
        passenger.register_for_flight()
        state.passengers[passport] = passenger
        flight.add_passenger(passenger)
        flight.aircraft.add_passenger(passenger)

        count = flight.aircraft.get_passenger_count()
        print(f"\nПассажир успешно зарегистрирован. На борту самолёта {flight.aircraft.tail_number} теперь {count} пассажиров.")
        print(f"\n{passenger}")

    except ValidationError as e:
        print(f"Ошибка: {e.message}")
    except RegistrationError as e:
        print(f"Ошибка регистрации: {e.message}")
    except KeyboardInterrupt:
        pass


def menu_takeoff_landing() -> None:
    print("\n--- Взлёт или посадка ---")
    try:
        print("1. Запросить взлёт")
        print("2. Запросить посадку")
        op = safe_input("\nВыберите (1/2): ")
        if op is None:
            return

        if not state.aircraft:
            print("Нет доступных самолётов")
            return

        print("\nДоступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model} ({aircraft.status.name})")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                print(f"Ошибка: самолёт {tail} не найден.")

        print(f"Текущий статус: {aircraft.status.name}")

        if op == "1":
            _do_takeoff(aircraft)
        elif op == "2":
            _do_landing(aircraft)

    except (TakeoffError, LandingError) as e:
        print(f"Ошибка: {e.message}")
    except KeyboardInterrupt:
        pass


def _do_takeoff(aircraft: Aircraft) -> None:
    if not aircraft.crew:
        print("Ошибка: нет экипажа!")
        return

    if aircraft.status != AircraftStatus.ON_GROUND:
        print(f"Ошибка: самолёт не на земле (статус: {aircraft.status.name})")
        return

    flight = state.get_flight_by_aircraft(aircraft)
    if not flight:
        print("Ошибка: нет зарегистрированного рейса для этого самолёта!")
        return

    print("Рейс подтверждён")

    checks = aircraft.preflight_check()
    check_names_ru = {
        "crew_minimum": "Проверка минимального экипажа",
        "crew_on_duty": "Проверка дежурства экипажа",
        "passengers_registered": "Проверка регистрации пассажиров",
        "route_set": "Проверка установки маршрута",
        "status_ok": "Проверка статуса самолёта",
    }
    print("\nРезультаты предполётной проверки:")
    for check_name, result in checks.items():
        status = "пройдена" if result else "не пройдена"
        ru_name = check_names_ru.get(check_name, check_name)
        print(f"  {ru_name}: {status}")

    if not all(checks.values()):
        print("\nОшибка: предполётная проверка не пройдена!")
        return

    aircraft.take_off()
    print(f"Взлёт выполнен! Статус: {aircraft.status.name}")
    print(aircraft)


def _do_landing(aircraft: Aircraft) -> None:
    if aircraft.status != AircraftStatus.IN_FLIGHT:
        print(f"Ошибка: самолёт не в воздухе (статус: {aircraft.status.name})")
        return

    aircraft.land()
    print(f"Посадка выполнена! Статус: {aircraft.status.name}")

    # Находим рейс ДО удаления из state
    flight = state.get_flight_by_aircraft(aircraft)
    if flight:
        # Высаживаем пассажиров: удаляем их из глобальной базы state.passengers
        for p in flight.passengers:
            state.passengers.pop(p.passport_number.upper(), None)
        
        # Удаляем рейс из системы
        del state.flights[flight.flight_number]

    # Сбрасываем состояние самолёта
    aircraft._passengers.clear()
    aircraft._flight_route = None

    print("Рейс завершён. Пассажиры и маршрут очищены.")
    print("Самолёт и экипаж готовы к повторному использованию.")
    print(aircraft)


def menu_inflight_service() -> None:
    """Пункт 6: Бортовое обслуживание."""
    print("\n--- Бортовое обслуживание ---")

    # Словарь для перевода названий услуг
    SERVICE_NAMES_RU = {
        ServiceType.MEAL: "Питание",
        ServiceType.BEVERAGE: "Напитки",
        ServiceType.ASSISTANCE: "Помощь",
        ServiceType.WIFI: "Wi-Fi",
    }

    try:
        if not state.aircraft:
            print("Нет доступных самолётов")
            return

        print("\nДоступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model}")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                print(f"Ошибка: самолёт {tail} не найден.")

        service = aircraft.get_service()

        print("\nУслуги:")
        print("  1. Питание")
        print("  2. Напитки")
        print("  3. Помощь")
        print("  4. Wi-Fi")

        svc_choice = safe_input("\nВыберите (1-4 или Enter для инвентаря): ")
        if svc_choice is None:
            return

        # Показать инвентарь при пустом вводе
        if not svc_choice or svc_choice.strip() == "":
            print("\nИнвентарь на борту:")
            for st in ServiceType:
                qty = service.get_quantity(st)
                ru_name = SERVICE_NAMES_RU.get(st, st.name)
                print(f"  {ru_name}: {qty}")
            return

        # Запросить ID пассажира
        passenger_id = None
        while passenger_id is None:
            pid = safe_input("\nНомер паспорта пассажира: ")
            if pid is None:
                return
            pid = pid.strip().upper()
            if not pid:
                print("Ошибка: номер паспорта не может быть пустым.")
                continue
            if not state.is_passport_exists(pid):
                print(f"Ошибка: пассажир с паспортом {pid} не найден!")
                continue
            passenger_id = pid

        # Инвентарь
        print("\nИнвентарь на борту:")
        for st in ServiceType:
            qty = service.get_quantity(st)
            ru_name = SERVICE_NAMES_RU.get(st, st.name)
            print(f"  {ru_name}: {qty}")

        # Предоставить услугу
        if svc_choice == "1":
            result = service.provide_meal("горячее питание", passenger_id)
        elif svc_choice == "2":
            result = service.provide_beverage("кофе", passenger_id)
        elif svc_choice == "3":
            result = service.assist_passenger("general", passenger_id)
        elif svc_choice == "4":
            result = service.provide_wifi(passenger_id)
        else:
            print("Ошибка: неизвестная услуга")
            return

        # Чистый вывод результата
        if isinstance(result, dict):
            svc_name = result.get('service', 'Услуга')
            # Переводим название услуги
            for st, ru_name in SERVICE_NAMES_RU.items():
                if st.name == svc_name:
                    svc_name = ru_name
                    break
            status = result.get('status', '')
            if status in ('provided', 'connected'):
                print(f"\nУслуга успешно предоставлена: {svc_name}")
            else:
                print(f"\nРезультат: {svc_name} — {status}")
        else:
            print(f"\nРезультат: {result}")

        # Статистика
        stats = service.get_stats()
        if any(count > 0 for count in stats.values()):
            print("\nСтатистика оказанных услуг:")
            for svc_type, count in stats.items():
                if count > 0:
                    ru_name = SERVICE_NAMES_RU.get(svc_type, svc_type.name)
                    print(f"  {ru_name}: {count}")

    except ServiceError as e:
        print(f"Ошибка: {e.message}")
    except KeyboardInterrupt:
        pass

def menu_safety_check() -> None:
    print("\n--- Проверка безопасности ---")
    try:
        if not state.aircraft:
            print("Нет доступных самолётов")
            return

        print("\nСамолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model}")

        aircraft = None
        while aircraft is None:
            tail = safe_input("\nБортовой номер: ")
            if tail is None:
                return
            aircraft = state.get_aircraft(tail)
            if not aircraft:
                print(f"Ошибка: самолёт {tail} не найден.")

        checks = aircraft.preflight_check()
        all_passed = True

        print("\nРезультаты проверок:")
        for check_name, result in checks.items():
            status = "пройдена" if result else "не пройдена"
            print(f"  {check_name}: {status}")
            if not result:
                all_passed = False

        flight = state.get_flight_by_aircraft(aircraft)
        if flight:
            print(f"  Рейс: {flight.flight_number} назначен")
        else:
            print("  Рейс: не назначен")
            all_passed = False

        if all_passed:
            print("\nВсе проверки безопасности пройдены!")
        else:
            print("\nОшибка: не все проверки безопасности пройдены.")

        print(f"\n{aircraft.model} | пассажиров: {aircraft.get_passenger_count()} | "
              f"экипажа: {len(aircraft.crew)} | статус: {aircraft.status.name}")

    except KeyboardInterrupt:
        pass


def menu_show_state() -> None:
    state.summary()


def menu_load_demo() -> None:
    print("\n--- Загрузить демо-данные ---")
    print("Очистка предыдущего состояния...")
    state.reset()

    try:
        aircraft = Aircraft(
            model="Boeing 737-800",
            tail_number="RA-737MM",
            capacity=150,
        )
        aircraft.set_airport("SVO")
        state.aircraft["RA-737MM"] = aircraft
        state.in_flight_services["RA-737MM"] = aircraft.get_service()
        print(f"Самолёт: {aircraft.tail_number}")

        print("\nЭкипаж:")
        _create_minimum_crew(aircraft)

        distance = get_airport_distance("SVO", "LED")
        flight = Flight(
            flight_number="SU737",
            aircraft=aircraft,
            departure="SVO",
            destination="LED",
            departure_time=datetime.now() + timedelta(hours=2),
            distance_km=distance,
        )
        state.flights["SU737"] = flight
        print(f"\nМаршрут: {distance:.0f} км, топливо: {distance * 3.5 * 1.1:.0f} л")
        print(f"Рейс: {flight}")

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
            print(f"  {name}, место {seat}")

        print("\nДемо-данные загружены!")

    except Exception as e:
        print(f"Ошибка: {e}")


def print_menu() -> None:
    print("\n=== Меню ===")
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
    print("\n=== Авиационная модель ===")
    print("Введите номер пункта меню (0-9)")

    while True:
        try:
            print_menu()
            choice = get_choice()

            if choice is None:
                print("Введите номер пункта")
                continue

            if choice == 0:
                print("\nДо свидания!")
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
                print(f"Ошибка: неизвестный пункт {choice}")

        except KeyboardInterrupt:
            print("\nНажмите 0 для выхода")
            continue

    print("Сеанс завершён.\n")


if __name__ == "__main__":
    main()