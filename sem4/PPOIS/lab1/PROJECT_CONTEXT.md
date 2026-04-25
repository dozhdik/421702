# Контекст проекта: Aircraft Model (Авиационная модель)

## Общее описание
Объектно-ориентированная система моделирования авиационных операций на Python. Проект реализует полный цикл управления самолётами, экипажем, пассажирами и рейсами с интерактивным CLI-интерфейсом.

## Архитектура

### Основные модули

#### 1. **aircraft.py** - Класс Aircraft (Самолёт)
Центральный класс системы, управляющий состоянием воздушного судна.

**Ключевые атрибуты:**
- `model`, `tail_number`, `capacity` - характеристики самолёта
- `status: AircraftStatus` - текущий статус (ON_GROUND, IN_FLIGHT, BOARDING, LANDING, MAINTENANCE)
- `current_airport` - текущий аэропорт
- `_passengers: list[Passenger]` - список пассажиров на борту
- `_crew: list[CrewMember]` - экипаж
- `_flight_route: FlightRoute` - маршрут полёта
- `_service: InFlightService` - бортовой сервис

**Основные методы:**
- `add_passenger()`, `remove_passenger()` - управление пассажирами
- `add_crew_member()`, `remove_crew_member()` - управление экипажем
- `preflight_check()` - предполётная проверка (экипаж, пассажиры, маршрут)
- `take_off()`, `land()` - операции взлёта/посадки
- `reset_after_landing()` - сброс состояния после рейса

**Валидация:**
- Модель: не пустая
- Бортовой номер: минимум 5 символов
- Вместимость: 1-850 мест

**Минимальные требования к экипажу:**
- 1 пилот (PILOT)
- 2 бортпроводника (FLIGHT_ATTENDANT)

#### 2. **passenger.py** - Класс Passenger (Пассажир)

**Атрибуты:**
- `full_name` - ФИО (минимум 3 символа)
- `passport_number` - паспорт (6-12 символов, алфавитно-цифровой)
- `ticket_number` - номер билета
- `seat_number` - место (формат: ряд + буква, например "12A")
- `is_registered` - статус регистрации

**Методы:**
- `assign_seat(seat)` - назначить место
- `register_for_flight(seat)` - регистрация на рейс
- `cancel_registration()` - отмена регистрации

#### 3. **crew_member.py** - Класс CrewMember (Член экипажа)

**Атрибуты:**
- `full_name` - ФИО
- `role: CrewRole` - роль (PILOT, CO_PILOT, NAVIGATOR, FLIGHT_ATTENDANT, LEAD_ATTENDANT, ENGINEER)
- `license_number` - номер лицензии (минимум 4 символа)
- `is_on_duty` - статус дежурства

**Методы:**
- `start_duty()`, `end_duty()` - начало/конец дежурства
- `perform_duty(duty_type)` - выполнение обязанностей
- `can_fly()` - проверка возможности полёта

#### 4. **flight_route.py** - Класс FlightRoute (Маршрут)

**Атрибуты:**
- `departure`, `destination` - IATA-коды аэропортов (3 буквы)
- `distance` - расстояние в км (1-20000)
- `estimated_duration: timedelta` - расчётное время
- `alternative_airports` - альтернативные аэропорты

**Константы:**
- `AVERAGE_SPEED_KMH = 800.0` - средняя скорость
- `AVERAGE_FUEL_CONSUMPTION = 3.5` л/км

**Методы:**
- `calculate_fuel()` - расчёт топлива (с 10% резервом)
- `estimate_duration()` - расчёт времени полёта
- `is_route_compatible(other)` - проверка совместимости маршрутов
- `__add__()` - объединение маршрутов

#### 5. **in_flight_service.py** - Класс InFlightService (Бортовой сервис)

**Типы услуг (ServiceType):**
- MEAL - питание
- BEVERAGE - напитки
- ENTERTAINMENT - развлечения
- ASSISTANCE - помощь
- DUTY_FREE - беспошлинная торговля
- WIFI - Wi-Fi
- SPECIAL_ASSISTANCE - специальная помощь

**Инвентарь по умолчанию:** 150 единиц каждого типа

**Методы:**
- `provide_meal(meal_type)` - предоставить питание
- `provide_beverage(beverage_type)` - предоставить напиток
- `assist_passenger(request)` - оказать помощь
- `provide_wifi(passenger_id)` - подключить Wi-Fi
- `check_supplies(service_type)` - проверить наличие
- `restock(service_type, quantity)` - пополнить запасы
- `get_stats()` - статистика предоставленных услуг

#### 6. **ticket.py** - Класс Ticket (Билет)

**Атрибуты:**
- `flight_number` - номер рейса (формат: 2 буквы + 1-4 цифры, например "SU123")
- `flight_datetime` - дата/время вылета
- `seat` - место
- `price` - цена
- `status: TicketStatus` - статус (BOOKED, CONFIRMED, USED, CANCELLED, REFUNDED)

**Методы:**
- `validate()` - валидация билета
- `confirm()` - подтверждение
- `use()` - использование
- `cancel()` - отмена
- `refund()` - возврат

#### 7. **runway.py** - Класс Runway (ВПП)

**Атрибуты:**
- `runway_id` - идентификатор
- `length` - длина (500-6000 м)
- `status: RunwayStatus` - статус (FREE, OCCUPIED, CLOSED, MAINTENANCE)
- `_current_aircraft` - текущий самолёт
- `_queue` - очередь самолётов

**Методы:**
- `request_takeoff(aircraft)` - запрос взлёта
- `request_landing(aircraft)` - запрос посадки
- `release()` - освобождение ВПП
- `close()`, `open()` - закрытие/открытие
- `set_maintenance()` - техобслуживание

#### 8. **enums.py** - Перечисления

```python
AircraftStatus: ON_GROUND, BOARDING, IN_FLIGHT, LANDING, MAINTENANCE
CrewRole: PILOT, CO_PILOT, NAVIGATOR, FLIGHT_ATTENDANT, LEAD_ATTENDANT, ENGINEER
TicketStatus: BOOKED, CONFIRMED, USED, CANCELLED, REFUNDED
RunwayStatus: FREE, OCCUPIED, CLOSED, MAINTENANCE
ServiceType: MEAL, BEVERAGE, ENTERTAINMENT, ASSISTANCE, DUTY_FREE, WIFI, SPECIAL_ASSISTANCE
```

#### 9. **exceptions.py** - Иерархия исключений

```python
FlightError (базовый)
├── ValidationError
├── RegistrationError
├── TakeoffError
├── LandingError
├── RunwayError
├── ServiceError
├── CrewError
└── CapacityError
```

### CLI-интерфейс (main.py)

**Класс SystemState** - синглтон для управления состоянием:
- `aircraft: dict[str, Aircraft]` - все самолёты
- `passengers: dict[str, Passenger]` - все пассажиры
- `crew_members: dict[str, CrewMember]` - весь экипаж
- `flights: dict[str, Flight]` - все рейсы
- `in_flight_services: dict[str, InFlightService]` - сервисы

**Класс Flight** - представление рейса в CLI:
- Связывает самолёт, маршрут, пассажиров
- Автоматический расчёт расстояния, топлива, времени полёта

**Меню:**
1. Создать самолёт (выбор из 10 моделей)
2. Добавить члена экипажа
3. Выпустить рейс
4. Зарегистрировать пассажира
5. Взлёт/посадка
6. Бортовое обслуживание
7. Проверка безопасности
8. Состояние системы
9. Загрузить демо-данные
0. Выход

**Доступные модели самолётов:**
- Boeing 737-800 (150 мест)
- Airbus A320neo (180 мест)
- Sukhoi Superjet 100 (98 мест)
- Boeing 777-300ER (350 мест)
- Airbus A380 (525 мест)
- Ilyushin Il-96 (300 мест)
- Tupolev Tu-204 (210 мест)
- Embraer E190 (100 мест)
- Bombardier CRJ900 (90 мест)
- Airbus A220 (135 мест)

**Аэропорты:**
- SVO - Шереметьево (Москва)
- DME - Домодедово (Москва)
- VKO - Внуково (Москва)
- LED - Пулково (Санкт-Петербург)
- KZN - Казань
- AER - Сочи
- ROV - Ростов-на-Дону
- KGD - Калининград
- UFA - Уфа
- OMS - Омск

## Бизнес-логика

### Процесс полёта:
1. Создание самолёта с экипажем
2. Создание рейса (маршрут, время)
3. Регистрация пассажиров
4. Предполётная проверка:
   - Минимальный экипаж
   - Экипаж на дежурстве
   - Наличие пассажиров (≥1)
   - Установлен маршрут
   - Статус ON_GROUND
5. Взлёт → статус IN_FLIGHT
6. Посадка → статус ON_GROUND
7. Очистка пассажиров и маршрута

### Валидация данных:
- Все строковые поля проверяются на пустоту
- Номера паспортов/лицензий - алфавитно-цифровые
- IATA-коды - 3 заглавные буквы
- Места - формат "12A" (ряд + буква A-K кроме I)
- Вместимость - положительное число ≤850

## Тестирование

**Структура тестов:**
- `tests/test_models.py` - юнит-тесты моделей
- `tests/test_main.py` - тесты CLI
- `tests/conftest.py` - фикстуры pytest

**Конфигурация:**
- `pytest.ini` - настройки pytest
- `.coveragerc` - настройки покрытия кода

## Технологический стек
- Python 3.12+
- pytest для тестирования
- Type hints (typing, __future__.annotations)
- Enum для перечислений
- datetime для работы с временем
- re для валидации строк

## Паттерны проектирования
- **Инкапсуляция**: приватные атрибуты с property
- **Валидация**: статические методы _validate_*
- **Композиция**: Aircraft содержит Passenger, CrewMember, FlightRoute, InFlightService
- **Синглтон**: SystemState в CLI
- **Фабричный метод**: Ticket.issue()
- **Перегрузка операторов**: FlightRoute.__add__()

## Особенности реализации
- Все строки нормализуются (upper(), strip())
- Копии списков в property для защиты внутреннего состояния
- Логирование изменений статуса в change_status()
- Автоматическое создание минимального экипажа при создании самолёта
- Демо-данные для быстрого тестирования
- Обработка KeyboardInterrupt в CLI

## Версия
1.0.0 (из __init__.py)
