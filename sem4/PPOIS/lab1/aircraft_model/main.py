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
    Runway,
    RunwayStatus,
    Ticket,
    TicketStatus,
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
        self.runways: dict[str, Runway] = {}
        self.passengers: dict[str, Passenger] = {}
        self.tickets: dict[str, Ticket] = {}
        self.crew_members: dict[str, CrewMember] = {}
        self.routes: dict[str, FlightRoute] = {}
        self.in_flight_services: dict[str, InFlightService] = {}

    def reset(self) -> None:
        self._init()
        info("Состояние системы сброшено")

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

    def get_runway(self, runway_id: str = None) -> Optional[Runway]:
        if not runway_id:
            return None
        runway_id = runway_id.upper()
        if runway_id in self.runways:
            return self.runways[runway_id]
        return None

    def get_passenger(self, passport: str = None) -> Optional[Passenger]:
        if not passport:
            return None
        passport = passport.upper()
        if passport in self.passengers:
            return self.passengers[passport]
        return None

    def summary(self) -> None:
        header("СОСТОЯНИЕ СИСТЕМЫ")

        if self.aircraft:
            print("\nСамолёты:")
            for aid, aircraft in self.aircraft.items():
                print(f"  [{aid}] {aircraft}")
        else:
            print("\nСамолёты: нет")

        if self.runways:
            print("\nВПП:")
            for rid, runway in self.runways.items():
                print(f"  [{rid}] {runway}")
        else:
            print("\nВПП: нет")

        if self.passengers:
            print("\nПассажиры:")
            for pid, passenger in self.passengers.items():
                print(f"  [{pid}] {passenger}")
        else:
            print("\nПассажиры: нет")

        if self.crew_members:
            print("\nЭкипаж:")
            for cid, crew in self.crew_members.items():
                print(f"  [{cid}] {crew}")
        else:
            print("\nЭкипаж: нет")

        if self.routes:
            print("\nМаршруты:")
            for rid, route in self.routes.items():
                print(f"  [{rid}] {route}")
        else:
            print("\nМаршруты: нет")


# Глобальный экземпляр состояния
state = SystemState()


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВВОДА
# ============================================================================
def safe_input(prompt: str) -> Optional[str]:
    """Безопасный ввод с обработкой Ctrl+C."""
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print()
        return None


def get_choice(menu_items: int = 8) -> Optional[int]:
    """Получить выбор пункта меню."""
    try:
        choice = input("> ").strip()
        if choice == "":
            return None
        return int(choice)
    except ValueError:
        return None
    except KeyboardInterrupt:
        return None


# ============================================================================
# ПУНКТЫ МЕНЮ
# ============================================================================

def menu_create_aircraft() -> None:
    """Пункт 1: Создать самолёт."""
    header("СОЗДАТЬ САМОЛЁТ")

    try:
        model = safe_input("Модель (например, Boeing 737-800): ")
        if model is None:
            return

        tail = safe_input("Бортовой номер (например, RA-12345): ")
        if tail is None:
            return

        cap_str = safe_input("Вместимость (пассажиров): ")
        if cap_str is None:
            return
        capacity = int(cap_str)

        aircraft = Aircraft(model=model, tail_number=tail, capacity=capacity)
        success(f"Самолёт создан: {aircraft.model} ({aircraft.tail_number})")

        state.aircraft[tail.upper()] = aircraft
        state.in_flight_services[tail.upper()] = aircraft.get_service()
        success(f"Сохранён как [{tail.upper()}]")

        add_crew = safe_input("Добавить минимальный экипаж? (y/n): ")
        if add_crew and add_crew.lower() == 'y':
            _add_minimum_crew(aircraft)

        print(f"\nСамолёт готов!")
        print(aircraft)

    except ValidationError as e:
        error(f"Ошибка валидации: {e.message}")
    except ValueError:
        error("Некорректное число для вместимости")
    except KeyboardInterrupt:
        pass


def _add_minimum_crew(aircraft: Aircraft) -> None:
    """Добавить минимальный экипаж."""
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
        success(f"Добавлен: {name} ({role.name})")


def menu_issue_ticket() -> None:
    """Пункт 2: Выпустить билет и зарегистрировать пассажира."""
    header("ВЫПУСК БИЛЕТА И РЕГИСТРАЦИЯ")

    try:
        name = safe_input("ФИО пассажира: ")
        if name is None:
            return

        passport = safe_input("Номер паспорта: ")
        if passport is None:
            return

        flight_num = safe_input("Номер рейса (например, SU123): ")
        if flight_num is None:
            return

        seat = safe_input("Место (например, 12A): ")
        if seat is None:
            return

        price_str = safe_input("Цена билета: ")
        if price_str is None:
            return
        price = float(price_str)

        passenger = Passenger(
            full_name=name,
            passport_number=passport,
            ticket_number=f"TKT-{uuid.uuid4().hex[:8].upper()}",
            seat_number=seat,
        )
        success(f"Пассажир создан: {passenger.full_name}")

        flight_time = datetime.now() + timedelta(hours=24)
        ticket = Ticket.issue(
            flight_number=flight_num,
            flight_datetime=flight_time,
            seat=seat,
            price=price,
            passport_number=passport,
        )
        success(f"Билет выпущен: {ticket.flight_number}, место {ticket.seat}")

        ticket.validate()
        success("Билет валиден")

        passenger.register_for_flight()
        success(f"Пассажир {passenger.full_name} зарегистрирован")

        state.passengers[passport.upper()] = passenger
        state.tickets[ticket.passport_number] = ticket
        success("Данные сохранены")

        print(f"\nПассажир зарегистрирован!")
        print(passenger)
        print(ticket)

    except ValidationError as e:
        error(f"Ошибка валидации: {e.message}")
    except RegistrationError as e:
        error(f"Ошибка регистрации: {e.message}")
    except FlightError as e:
        error(f"Ошибка билета: {e.message}")
    except ValueError:
        error("Некорректная цена")
    except KeyboardInterrupt:
        pass


def menu_takeoff_landing() -> None:
    """Пункт 3: Запросить взлёт или посадку."""
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

        tail = safe_input("\nБортовой номер: ")
        if tail is None:
            return

        aircraft = state.get_aircraft(tail)
        if not aircraft:
            error(f"Самолёт {tail} не найден")
            return

        info(f"Текущий статус: {aircraft.status.name}")

        if not state.runways:
            warning("Нет доступных ВПП. Создаю новую...")
            runway = Runway("RWY-01", 3000)
            state.runways["RWY-01"] = runway
        else:
            print("Доступные ВПП:")
            for rid, runway in state.runways.items():
                print(f"  [{rid}] {runway.length}m ({runway.status.name})")

            rw_id = safe_input("\nID ВПП: ")
            if rw_id is None:
                return

            runway = state.get_runway(rw_id)
            if not runway:
                error(f"ВПП {rw_id} не найдена")
                return

        info(f"Статус ВПП: {runway.status.name}")

        if op == "1":
            _do_takeoff(aircraft, runway)
        elif op == "2":
            _do_landing(aircraft, runway)

    except (TakeoffError, LandingError, RunwayError) as e:
        error(f"Операция невозможна: {e.message}")
    except KeyboardInterrupt:
        pass


def _do_takeoff(aircraft: Aircraft, runway: Runway) -> None:
    """Выполнить взлёт."""
    if not aircraft.crew:
        warning("Нет экипажа!")
        return

    if aircraft.status != AircraftStatus.ON_GROUND:
        error(f"Самолёт не на земле (статус: {aircraft.status.name})")
        return

    can_takeoff = runway.request_takeoff(aircraft)
    if can_takeoff:
        success("ВПП предоставлена")
    else:
        warning(f"Самолёт добавлен в очередь (позиция: {runway.queue_size})")
        return

    checks = aircraft.preflight_check()
    for check_name, result in checks.items():
        status = "OK" if result else "FAIL"
        print(f"  [{status}] {check_name}")

    if not all(checks.values()):
        error("Предполётная проверка не пройдена!")
        runway.release()
        return

    aircraft.take_off()
    success(f"Взлёт выполнен! Статус: {aircraft.status.name}")
    print(aircraft)


def _do_landing(aircraft: Aircraft, runway: Runway) -> None:
    """Выполнить посадку."""
    if aircraft.status != AircraftStatus.IN_FLIGHT:
        error(f"Самолёт не в воздухе (статус: {aircraft.status.name})")
        return

    can_land = runway.request_landing(aircraft)
    if can_land:
        success("ВПП предоставлена")
    else:
        warning(f"Самолёт добавлен в очередь (позиция: {runway.queue_size})")
        return

    aircraft.land()
    success(f"Посадка выполнена! Статус: {aircraft.status.name}")
    print(aircraft)


def menu_inflight_service() -> None:
    """Пункт 4: Запустить бортовое обслуживание."""
    header("БОРТОВОЕ ОБСЛУЖИВАНИЕ")

    try:
        if not state.aircraft:
            warning("Нет доступных самолётов")
            return

        print("Доступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model}")

        tail = safe_input("\nБортовой номер: ")
        if tail is None:
            return

        aircraft = state.get_aircraft(tail)
        if not aircraft:
            error(f"Самолёт {tail} не найден")
            return

        service = aircraft.get_service()

        print("\nУслуги:")
        print("  1 - Питание")
        print("  2 - Напитки")
        print("  3 - Помощь")
        print("  4 - Wi-Fi")
        print("  5 - Развлечения")
        print("  6 - Показать инвентарь")

        svc_choice = safe_input("\nВыберите (1-6): ")
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
            req_type = safe_input("Тип (обычная/special): ") or "general"
            result = service.assist_passenger(req_type)
        elif svc_choice == "4":
            result = service.provide_wifi(passenger_id)
        elif svc_choice == "5":
            result = service.provide_entertainment(passenger_id)
        elif svc_choice == "6":
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


def menu_plan_route() -> None:
    """Пункт 5: Спланировать маршрут."""
    header("ПЛАНИРОВАНИЕ МАРШРУТА")

    try:
        departure = safe_input("Аэропорт вылета (IATA, например SVO): ")
        if departure is None:
            return

        destination = safe_input("Аэропорт прилёта (IATA, например LED): ")
        if destination is None:
            return

        dist_str = safe_input("Расстояние (км): ")
        if dist_str is None:
            return
        distance = float(dist_str)

        route = FlightRoute(
            departure=departure.upper(),
            destination=destination.upper(),
            distance=distance,
        )
        success(f"Маршрут: {route.departure} -> {route.destination}")

        fuel = route.calculate_fuel()
        info(f"Требуется топлива: {fuel:.1f} л (с резервом 10%)")

        duration = route.estimate_duration()
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        info(f"Расчётное время: ~{hours}h {minutes}m")

        alt = safe_input("\nАльтернативный аэропорт (Enter - нет): ")
        if alt:
            route.add_alternative(alt.upper())
            success(f"Добавлен: {alt.upper()}")

        route_id = f"{route.departure}-{route.destination}"
        state.routes[route_id] = route
        success(f"Маршрут сохранён как [{route_id}]")

        print(f"\nМаршрут запланирован!")
        print(route)

    except ValidationError as e:
        error(f"Ошибка валидации: {e.message}")
    except ValueError:
        error("Некорректное число для расстояния")
    except KeyboardInterrupt:
        pass


def menu_safety_check() -> None:
    """Пункт 6: Проверка безопасности."""
    header("ПРОВЕРКА БЕЗОПАСНОСТИ")

    try:
        if not state.aircraft:
            warning("Нет доступных самолётов")
            return

        print("Самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model}")

        tail = safe_input("\nБортовой номер: ")
        if tail is None:
            return

        aircraft = state.get_aircraft(tail)
        if not aircraft:
            error(f"Самолёт {tail} не найден")
            return

        checks = aircraft.preflight_check()
        all_passed = True

        for check_name, result in checks.items():
            status = "OK" if result else "FAIL"
            print(f"  [{status}] {check_name}")
            if not result:
                all_passed = False

        if all_passed:
            success("Все проверки пройдены! Самолёт готов к вылету.")
        else:
            warning("Не все проверки пройдены.")

        print(f"\nДетали: {aircraft.model}, пассажиров: {aircraft.get_passenger_count()}, "
              f"экипажа: {len(aircraft.crew)}, статус: {aircraft.status.name}")

    except KeyboardInterrupt:
        pass


def menu_show_state() -> None:
    """Пункт 7: Показать состояние системы."""
    state.summary()


def menu_load_demo() -> None:
    """Пункт 8: Загрузить демо-данные."""
    header("ЗАГРУЗКА ДЕМО-ДАННЫХ")

    try:
        info("Очистка предыдущего состояния...")
        state.reset()

        aircraft = Aircraft(
            model="Boeing 737-800",
            tail_number="RA-737MM",
            capacity=150,
        )
        aircraft.set_airport("SVO")
        state.aircraft["RA-737MM"] = aircraft
        state.in_flight_services["RA-737MM"] = aircraft.get_service()
        success(f"Создан: {aircraft}")

        crew_list = [
            ("Иван Сидоров", CrewRole.PILOT, "PLT-SID001"),
            ("Анна Козлова", CrewRole.CO_PILOT, "PLT-KOZ002"),
            ("Пётр Волков", CrewRole.FLIGHT_ATTENDANT, "FA-VOL003"),
            ("Елена Соколова", CrewRole.FLIGHT_ATTENDANT, "FA-SOK004"),
        ]
        for name, role, lic in crew_list:
            crew = CrewMember(name, role, lic)
            crew.start_duty()
            aircraft.add_crew_member(crew)
            state.crew_members[lic] = crew
            success(f"  {name} ({role.name})")

        passengers_data = [
            ("Михаил Петров", "MP1234567", "15A"),
            ("Ольга Иванова", "OI2345678", "15B"),
            ("Сергей Козлов", "SK3456789", "15C"),
        ]
        for name, passport, seat in passengers_data:
            p = Passenger(name, passport, f"TKT-{uuid.uuid4().hex[:6].upper()}", seat)
            p.register_for_flight()
            aircraft.add_passenger(p)
            state.passengers[passport] = p
            success(f"  {name}, место {seat}")

        route = FlightRoute("SVO", "LED", 650)
        aircraft.set_route(route)
        state.routes["SVO-LED"] = route
        success(f"  Маршрут: {route}")

        runway = Runway("RWY-SVO", 3000)
        state.runways["RWY-SVO"] = runway
        success(f"  ВПП: {runway}")

        ticket = Ticket.issue(
            flight_number="SU737",
            flight_datetime=datetime.now() + timedelta(hours=2),
            seat="1A",
            price=599.99,
            passport_number="MP1234567",
        )
        state.tickets["MP1234567"] = ticket
        success(f"  Билет: {ticket.flight_number}")

        success("\nДемо-данные загружены!")

    except Exception as e:
        error(f"Ошибка: {e}")


def menu_add_crew_member() -> None:
    """Пункт 9: Добавить члена экипажа к существующему самолёту."""
    header("ДОБАВИТЬ ЧЛЕНА ЭКИПАЖА")

    try:
        # Выбор самолёта
        if not state.aircraft:
            warning("Нет доступных самолётов. Сначала создайте самолёт.")
            return

        step(1, "Выбор самолёта")
        print("Доступные самолёты:")
        for key, aircraft in state.aircraft.items():
            print(f"  [{key}] {aircraft.model} ({len(aircraft.crew)} чл. экипажа)")

        tail = safe_input("\nБортовой номер самолёта: ")
        if tail is None:
            return

        aircraft = state.get_aircraft(tail)
        if not aircraft:
            error(f"Самолёт {tail} не найден")
            return

        success(f"Выбран: {aircraft.model} ({aircraft.tail_number})")

        # Выбор роли
        step(2, "Выбор должности")
        print("\nДоступные должности:")
        print("  1 - Пилот (PILOT)")
        print("  2 - Второй пилот (CO_PILOT)")
        print("  3 - Штурман (NAVIGATOR)")
        print("  4 - Бортпроводник (FLIGHT_ATTENDANT)")
        print("  5 - Старший бортпроводник (LEAD_ATTENDANT)")
        print("  6 - Бортинженер (ENGINEER)")

        role_choice = safe_input("\nВыберите должность (1-6): ")
        if role_choice is None:
            return

        role_map = {
            "1": CrewRole.PILOT,
            "2": CrewRole.CO_PILOT,
            "3": CrewRole.NAVIGATOR,
            "4": CrewRole.FLIGHT_ATTENDANT,
            "5": CrewRole.LEAD_ATTENDANT,
            "6": CrewRole.ENGINEER,
        }
        role = role_map.get(role_choice)
        if not role:
            error("Неизвестная должность")
            return

        # Ввод данных
        step(3, "Ввод данных члена экипажа")
        name = safe_input("ФИО: ")
        if name is None:
            return

        license_num = safe_input("Номер лицензии: ")
        if license_num is None:
            return

        # Создание члена экипажа
        step(4, "Создание члена экипажа")
        crew = CrewMember(
            full_name=name,
            role=role,
            license_number=license_num,
        )
        success(f"Создан: {crew.full_name} ({crew.role.name})")

        # Добавление в самолёт
        step(5, "Добавление в экипаж")
        if aircraft.add_crew_member(crew):
            state.crew_members[license_num] = crew
            success(f"Добавлен в экипаж {aircraft.tail_number}")
        else:
            warning("Член экипажа с таким номером лицензии уже есть")

        # Выход на дежурство
        step(6, "Выход на дежурство")
        start = safe_input("Выйти на дежурство? (y/n): ")
        if start and start.lower() == 'y':
            crew.start_duty()
            success("На дежурстве")

        print(f"\n{aircraft}")

    except ValidationError as e:
        error(f"Ошибка валидации: {e.message}")
    except CrewError as e:
        error(f"Ошибка экипажа: {e.message}")
    except KeyboardInterrupt:
        pass


def print_menu() -> None:
    """Вывести меню."""
    print("\n=== МЕНЮ ===")
    print("1. Создать самолёт")
    print("2. Выпустить билет и зарегистрировать пассажира")
    print("3. Запросить взлёт или посадку")
    print("4. Бортовое обслуживание")
    print("5. Спланировать маршрут")
    print("6. Проверка безопасности")
    print("7. Состояние системы")
    print("8. Загрузить демо-данные")
    print("9. Добавить члена экипажа")
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
                menu_issue_ticket()
            elif choice == 3:
                menu_takeoff_landing()
            elif choice == 4:
                menu_inflight_service()
            elif choice == 5:
                menu_plan_route()
            elif choice == 6:
                menu_safety_check()
            elif choice == 7:
                menu_show_state()
            elif choice == 8:
                menu_load_demo()
            elif choice == 9:
                menu_add_crew_member()
            else:
                warning(f"Неизвестный пункт: {choice}")

        except KeyboardInterrupt:
            print("\n[Ctrl+C] Нажмите 0 для выхода")
            continue

    print("Сеанс завершён.\n")


if __name__ == "__main__":
    main()