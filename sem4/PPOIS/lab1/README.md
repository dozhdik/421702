# Лабораторная работа №1

## Вариант 46. Модель самолёта

**Предметная область:** Воздушное транспортное средство и процессы его эксплуатации.

**Цель работы:** Разработка ООП-модели авиационной системы, включающей сущности `Aircraft`, `Passenger`, `CrewMember`, `InFlightService`, а также реализацию операций регистрации на рейс, взлёта/посадки, бортового обслуживания, планирования маршрутов и обеспечения безопасности.

---

## Требования

| Компонент | Версия |
|-----------|--------|
| Python | 3.10+ |
| pytest | 7.0+ |

---

## Структура репозитория

```
lab1/
├── aircraft_model/           # Основной пакет модели
│   ├── __init__.py           # Публичное API пакета, явный __all__
│   ├── aircraft.py           # Класс Aircraft (самолёт)
│   ├── passenger.py          # Класс Passenger (пассажир)
│   ├── crew_member.py        # Класс CrewMember (член экипажа)
│   ├── flight_route.py       # Класс FlightRoute (маршрут)
│   ├── in_flight_service.py  # Класс InFlightService (бортовой сервис)
│   ├── enums.py              # Перечисления статусов и ролей
│   ├── exceptions.py         # Иерархия кастомных исключений
│   ├── main.py               # CLI-интерфейс
│   └── tests/                # Модульные тесты (pytest)
│       ├── __init__.py
│       ├── conftest.py       # Фикстуры pytest
│       ├── test_aircraft.py
│       ├── test_passenger.py
│       ├── test_crew_member.py
│       ├── test_flight_route.py
│       ├── test_in_flight_service.py
│       ├── test_enums.py
│       ├── test_exceptions.py
│       └── test_main.py
└── README.md                  # Данная документация
```

### Роль `__init__.py`

Файл [`aircraft_model/__init__.py`](aircraft_model/__init__.py) выполняет несколько функций:

1. **Публичное API** — явный `__all__` определяет, что экспортируется при `from aircraft_model import *`
2. **Инкапсуляция импортов** — скрывает внутреннюю структуру модулей
3. **Версионирование** — атрибут `__version__ = "1.0.0"`

---

## Использование (CLI-интерфейс)

### Основные команды

После запуска приложения доступно интерактивное меню:

```
=== Меню ===
1. Создать самолёт
2. Добавить члена экипажа
3. Выпустить рейс
4. Зарегистрировать пассажира на рейс
5. Запросить взлёт или посадку
6. Бортовое обслуживание
7. Проверка безопасности
8. Состояние системы
9. Загрузить демо-данные
0. Выход
=============
```

### Примеры использования

**1. Регистрация на рейс:**

```
> Выберите рейс: SU737
> Введите ФИО: Иван Петров
> Номер паспорта: IP123456
> Место (12A): 15A
Пассажир успешно зарегистрирован. На борту теперь 1 пассажиров.
```

**2. Взлёт самолёта:**

```
> Выберите (1/2): 1
> Введите борт: RA-737MM
> Рейс подтверждён
> Результаты предполётной проверки:
  Проверка минимального экипажа: пройдена
  Проверка дежурства экипажа: пройдена
  Проверка регистрации пассажиров: пройдена
  Проверка установки маршрута: пройдена
  Проверка статуса самолёта: пройдена
> Взлёт выполнен! Статус: IN_FLIGHT
```

**3. Посадка самолёта:**

```
> Выберите (1/2): 2
> Введите борт: RA-737MM
> Посадка выполнена! Статус: ON_GROUND
> Рейс завершён. Самолёт и экипаж готовы к повторному использованию.
```

**4. Бортовое обслуживание:**

```
> Выберите борт: RA-737MM
> Выберите (1-4): 1 (Питание)
> Номер паспорта: IP123456
> Услуга успешно предоставлена: Питание
```

**5. Проверка безопасности:**

```
> Выберите борт: RA-737MM
> Результаты проверок:
  crew_minimum: пройдена
  crew_on_duty: пройдена
  passengers_registered: пройдена
  route_set: пройдена
  status_ok: пройдена
> Все проверки безопасности пройдены!
```

---

## Архитектура и дизайн-решения

### ООП-модель

#### Диаграмма классов (ключевые отношения)

```
┌─────────────────────┐         ┌─────────────────────┐
│      Aircraft       │         │     Passenger       │
├─────────────────────┤         ├─────────────────────┤
│ - tail_number       │         │ - passport_number   │
│ - capacity          │  1..*   │ - seat_number       │
│ - status            │────────>│ - is_registered     │
│ - passengers: list  │         └─────────────────────┘
│ - crew: list        │
│ - service: IFS      │         ┌─────────────────────┐
└─────────┬───────────┘         │   FlightRoute       │
          │                     ├─────────────────────┤
          │ 1..*                │ - departure         │
          ▼                     │ - destination       │
┌─────────────────────┐         │ - distance          │
│    CrewMember       │         └─────────────────────┘
├─────────────────────┤
│ - role: CrewRole    │
│ - license_number    │         ┌─────────────────────┐
│ - is_on_duty        │         │  InFlightService    │
└─────────────────────┘         ├─────────────────────┤
                                │ - inventory         │
                                │ - service_limits    │
                                └─────────────────────┘
```

#### Ответственности классов

| Класс | Ответственность |
|-------|-----------------|
| `Aircraft` | Управление состоянием самолёта, экипажем, пассажирами; взлёт/посадка |
| `Passenger` | Хранение данных пассажира, регистрация на рейс |
| `CrewMember` | Роль, дежурство, выполнение обязанностей |
| `FlightRoute` | Параметры маршрута (расстояние, время) |
| `InFlightService` | Учёт инвентаря, лимиты услуг |

#### Композиция vs Агрегация

- **Композиция:** `Aircraft` владеет `InFlightService` (создаётся внутри `__init__`)
- **Агрегация:** `Aircraft` содержит список `Passenger` и `CrewMember` (управляются извне)

```python
# Композиция: service создаётся внутри Aircraft
class Aircraft:
    def __init__(self, ...):
        self._service: InFlightService = InFlightService()  # владеем

# Агрегация: пассажиры управляются извне
class Aircraft:
    def add_passenger(self, passenger: Passenger) -> bool:
        self._passengers.append(passenger)  # ссылка, не создание
```

### Детальное описание модулей

#### aircraft.py — Класс Aircraft (Самолёт)

Центральный класс системы, управляющий состоянием воздушного судна.

**Ключевые атрибуты:**

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `model` | `str` | Модель самолёта |
| `tail_number` | `str` | Бортовой номер (минимум 5 символов) |
| `capacity` | `int` | Вместимость (1-850 мест) |
| `status` | `AircraftStatus` | Текущий статус |
| `current_airport` | `str` | Текущий аэропорт |
| `_passengers` | `list[Passenger]` | Список пассажиров |
| `_crew` | `list[CrewMember]` | Экипаж |
| `_flight_route` | `FlightRoute` | Маршрут полёта |
| `_service` | `InFlightService` | Бортовой сервис |

**Основные методы:**

| Метод | Описание |
|-------|----------|
| `add_passenger()` / `remove_passenger()` | Управление пассажирами |
| `add_crew_member()` / `remove_crew_member()` | Управление экипажем |
| `preflight_check()` | Предполётная проверка (экипаж, пассажиры, маршрут) |
| `take_off()` / `land()` | Операции взлёта/посадки |
| `reset_after_landing()` | Сброс состояния после рейса |

**Минимальные требования к экипажу:**
- 1 пилот (`PILOT`)
- 2 бортпроводника (`FLIGHT_ATTENDANT`)

#### passenger.py — Класс Passenger (Пассажир)

**Атрибуты:**

| Атрибут | Тип | Описание |
|---------|-----|----------|
| `full_name` | `str` | ФИО (минимум 3 символа) |
| `passport_number` | `str` | Паспорт (6-12 символов) |
| `seat_number` | `str` | Место (формат: "12A") |
| `is_registered` | `bool` | Статус регистрации |

**Методы:**
- `assign_seat(seat)` — назначить место
- `register_for_flight()` — регистрация на рейс
- `cancel_registration()` — отмена регистрации

#### crew_member.py — Класс CrewMember (Член экипажа)

**Роли** (`CrewRole`): `PILOT`, `CO_PILOT`, `NAVIGATOR`, `FLIGHT_ATTENDANT`, `LEAD_ATTENDANT`, `ENGINEER`

**Методы:**
- `start_duty()` / `end_duty()` — начало/конец дежурства
- `perform_duty(duty_type)` — выполнение обязанностей
- `can_fly()` — проверка возможности полёта

#### flight_route.py — Класс FlightRoute (Маршрут)

**Константы:**
- `AVERAGE_SPEED_KMH = 800.0` — средняя скорость
- `AVERAGE_FUEL_CONSUMPTION = 3.5` л/км

**Методы:**
- `calculate_fuel()` — расчёт топлива (с 10% резервом)
- `estimate_duration()` — расчёт времени полёта
- `is_route_compatible(other)` — проверка совместимости маршрутов
- `__add__()` — объединение маршрутов

#### in_flight_service.py — Класс InFlightService (Бортовой сервис)

**Типы услуг** (`ServiceType`): `MEAL`, `BEVERAGE`, `ASSISTANCE`, `WIFI`

**Инвентарь по умолчанию:** 150 единиц каждого типа

**Методы:**
- `provide_meal(meal_type)` — предоставить питание
- `provide_beverage(beverage_type)` — предоставить напиток
- `provide_wifi(passenger_id)` — подключить Wi-Fi
- `restock(service_type, quantity)` — пополнить запасы

### Паттерны проектирования

| Паттерн | Применение в проекте |
|---------|---------------------|
| **Инкапсуляция** | Приватные атрибуты с property-доступом |
| **Валидация** | Статические методы `_validate_*` |
| **Композиция** | `Aircraft` содержит `InFlightService` |
| **Агрегация** | `Aircraft` содержит списки `Passenger`, `CrewMember` |
| **Синглтон** | `SystemState` в CLI |
| **Перегрузка операторов** | `FlightRoute.__add__()` |

### Особенности реализации

- Все строки нормализуются (`upper()`, `strip()`)
- Копии списков в property для защиты внутреннего состояния
- Логирование изменений статуса в `change_status()`
- Автоматическое создание минимального экипажа при создании самолёта
- Демо-данные для быстрого тестирования
- Обработка `KeyboardInterrupt` в CLI

---

### Принципы SOLID

#### 1. Single Responsibility Principle (SRP)

Каждый класс отвечает за одну зону ответственности:

```python
# [aircraft.py:56-73]
class Aircraft:
    @staticmethod
    def _validate_model(model: str) -> None:
        """Валидация модели — отдельная ответственность"""
        if not model or not model.strip():
            raise ValidationError("model", "Название модели не может быть пустым")
```

#### 2. Open/Closed Principle (OCP)

Классы открыты для расширения, закрыты для модификации:

```python
# [enums.py:9-15]
class AircraftStatus(Enum):
    """Статусы самолёта. Новые статусы добавляются через Enum.auto()"""
    ON_GROUND = auto()
    BOARDING = auto()
    IN_FLIGHT = auto()
    LANDING = auto()
    MAINTENANCE = auto()
```

#### 3. Liskov Substitution Principle (LSP)

Все исключения наследуются от `FlightError`, обеспечивая единый интерфейс обработки:

```python
# [exceptions.py:7-13]
class FlightError(Exception):
    """Базовый класс — любой потомок может заменить базовый"""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

class TakeoffError(FlightError): pass
class LandingError(FlightError): pass
class CapacityError(FlightError): pass
```

---

### Конечный автомат (FSM) жизненного цикла

Самолёт реализует FSM через enum `AircraftStatus` и методы `take_off()`/`land()`:

```
                    ┌──────────────┐
                    │  ON_GROUND   │<──────────────────────┐
                    └──────┬───────┘                       │
                           │ can_take_off()                │
                           ▼                               │
                    ┌──────────────┐                       │
    ┌───────────────│  IN_FLIGHT   │───────────────────────┤
    │               └──────────────┘                       │
    │                                                    land()
    │ reset_after_landing()
    │                                                      │
    │ ┌──────────────┐                                     │
    │ │   LANDING    │ ────────────────────────────────────┘
    │ └──────────────┘
    │
    └─────────────────────────────────────┐
                                          │
                           ┌──────────────▼───────────────┐
                           │         BOARDING             │
                           └──────────────────────────────┘
```

#### Валидация переходов

```python
# [aircraft.py:201-206]
def take_off(self) -> None:
    if not self.can_take_off():
        failed = [k for k, v in self.preflight_check().items() if not v]
        raise TakeoffError(f"Взлёт невозможен. Не пройдены проверки: {', '.join(failed)}")
    self.change_status(AircraftStatus.IN_FLIGHT)

# [aircraft.py:211-215]
def land(self) -> None:
    if self._status != AircraftStatus.IN_FLIGHT:
        raise FlightError(f"Посадка невозможна: текущий статус {self._status.name}")
    self.change_status(AircraftStatus.ON_GROUND)
```

---

### Обработка ошибок

#### Иерархия исключений

```
Exception
    └── FlightError (базовый для всей системы)
            ├── ValidationError      — ошибки валидации
            ├── RegistrationError    — ошибки регистрации
            ├── TakeoffError         — ошибки взлёта
            ├── LandingError         — ошибки посадки
            ├── ServiceError         — ошибки сервиса
            ├── CrewError            — ошибки экипажа
            └── CapacityError        — превышение вместимости
```

#### Применение исключений

```python
# [aircraft.py:131-139]
def add_passenger(self, passenger: Passenger) -> bool:
    if len(self._passengers) >= self._capacity:
        raise CapacityError(self._capacity, len(self._passengers) + 1)
    if not passenger.is_registered:
        raise FlightError(f"Пассажир не зарегистрирован на рейс")
    self._passengers.append(passenger)
    return True
```

---

### Сериализация и dataclasses

В проекте используется подход с property-доступом для immutability:

```python
# [aircraft.py:77-95]
@property
def model(self) -> str:
    """Read-only через property"""
    return self._model

@property
def status(self) -> AircraftStatus:
    return self._status
```

---

## Тестирование

### Запуск тестов

```bash
# Все тесты с покрытием
python3 -m pytest --cov=aircraft_model --cov-report=html

# Только быстрые тесты
python3 -m pytest -q

# Конкретный модуль
python3 -m pytest aircraft_model/tests/test_aircraft.py -v
```

### Покрытие тестами

| Модуль | Тесты | Что проверяется |
|--------|-------|-----------------|
| `test_aircraft.py` | 18 тестов | Валидация, свойства, пассажиры, экипаж, взлёт/посадка |
| `test_passenger.py` | 12 тестов | Регистрация, отмена, места, валидация |
| `test_crew_member.py` | 10 тестов | Дежурство, выполнение обязанностей |
| `test_flight_route.py` | 8 тестов | Валидация маршрута, свойства |
| `test_in_flight_service.py` | 10 тестов | Инвентарь, лимиты, услуги |
| `test_exceptions.py` | 9 тестов | Иерархия исключений |
| `test_enums.py` | 4 теста | Значения перечислений |

**Итого: ~140 тестов**

### Примеры тестовых сценариев

```python
# [test_aircraft.py:126-128]
def test_takeoff_success(self, aircraft_ready_for_takeoff):
    aircraft_ready_for_takeoff.take_off()
    assert aircraft_ready_for_takeoff.status == AircraftStatus.IN_FLIGHT

# [test_aircraft.py:130-132]
def test_takeoff_fails_checks(self, aircraft):
    with pytest.raises(TakeoffError, match="проверки"):
        aircraft.take_off()
```

### Фикстуры pytest

```python
# [conftest.py:81-86]
@pytest.fixture
def aircraft_ready_for_takeoff(aircraft_with_crew, registered_passenger, flight_route):
    """Самолёт готовый к взлёту."""
    aircraft_with_crew.add_passenger(registered_passenger)
    aircraft_with_crew.set_route(flight_route)
    return aircraft_with_crew
```

---

## Ответы на контрольные вопросы

### 1. Основные принципы ООП

| Принцип | Реализация в проекте |
|---------|---------------------|
| **Абстракция** | Классы моделируют сущности предметной области; скрыты детали реализации (валидация в private-методах `_validate_*`) |
| **Инкапсуляция** | Данные защищены через `_` prefix (`_model`, `_passengers`); доступ через property; `__all__` ограничивает публичный API |
| **Полиморфизм** | `ServiceType`, `AircraftStatus` — разные enum со своими состояниями; методы `validate()` работают полиморфно для всех подклассов `FlightError` |
| **Модульность** | Пакет разделён на модули по ответственности; [`__init__.py`](aircraft_model/__init__.py) управляет экспортами |

### 2. Принципы SOLID

| Принцип | Реализация |
|---------|------------|
| **S**ingle Responsibility | Каждый класс: `Aircraft` — только самолёт, `Passenger` — только пассажир |
| **O**pen/Closed | `AircraftStatus` расширяется через `Enum.auto()`, не меняя код |
| **L**iskov Substitution | `TakeoffError`, `LandingError` заменяют `FlightError` |
| **I**nterface Segregation | Минимальные интерфейсы через property и методы |
| **D**ependency Inversion | `SystemState` зависит от абстракций (`Optional[Aircraft]`) |

### 3. Базовые типы и конструкции Python

- **Встроенные типы:** `str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`
- **Конструкции:** `class`, `def`, `lambda`, `@property`, `@staticmethod`, `@classmethod`, `Enum`, `Optional`, `Dict`, `List`, `TYPE_CHECKING`
- **Управление потоком:** `if/elif/else`, `try/except/finally`, `for`, `while`, `match/case`

### 4. Сериализация/десериализация

В проекте реализована сериализация через:
- **Property-доступ** для read-only атрибутов (защита от мутации)
- **Методы жизненного цикла** объектов (`register_for_flight()`)

### 5. Конечный автомат (FSM)

FSM реализован в классе `Aircraft`:

```
States: ON_GROUND, BOARDING, IN_FLIGHT, LANDING, MAINTENANCE

Transitions:
  ON_GROUND  --take_off()-->  IN_FLIGHT
  IN_FLIGHT  --land()----->  ON_GROUND

Validation:
  take_off() требует: preflight_check() = True
  land() требует: status == IN_FLIGHT
```

См. [`enums.py`](aircraft_model/enums.py) — `AircraftStatus` и [`aircraft.py`](aircraft_model/aircraft.py) — `take_off()`, `land()`.

---

## Информация об авторе

| Поле | Значение |
|------|----------|
| **Студент** | Дождиков Александр Игоревич |
| **Группа** | 421702 |
---