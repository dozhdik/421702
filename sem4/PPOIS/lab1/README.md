# Лабораторная работа №1

## Вариант 46. Модель самолёта

**Предметная область:** Воздушное транспортное средство и процессы его эксплуатации.

**Цель работы:** Разработка ООП-модели авиационной системы, включающей сущности `Aircraft`, `Passenger`, `CrewMember`, `Runway`, `InFlightService`, `Ticket`, а также реализацию операций регистрации на рейс, взлёта/посадки, бортового обслуживания, планирования маршрутов и обеспечения безопасности.

---

## Требования и установка

### Системные требования

| Компонент | Версия |
|-----------|--------|
| Python | 3.10+ |
| pytest | 7.0+ |

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd lab1

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Запуск приложения
python3 -m aircraft_model.main
```

---

## Структура репозитория

```
lab1/
├── aircraft_model/           # Основной пакет модели
│   ├── __init__.py           # Публичное API пакета, явный __all__
│   ├── aircraft.py           # Класс Aircraft (самолёт)
│   ├── passenger.py          # Класс Passenger (пассажир)
│   ├── crew_member.py        # Класс CrewMember (член экипажа)
│   ├── runway.py             # Класс Runway (ВПП)
│   ├── ticket.py             # Класс Ticket (билет)
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
│       ├── test_runway.py
│       ├── test_ticket.py
│       ├── test_flight_route.py
│       ├── test_in_flight_service.py
│       ├── test_enums.py
│       ├── test_exceptions.py
│       └── test_main.py
├── README.md                  # Данная документация
└── PROJECT_CONTEXT.md         # Контекст проекта
```

### Роль `__init__.py`

Файл [`aircraft_model/__init__.py`](aircraft_model/__init__.py) выполняет несколько функций:

1. **Публичное API** — явный `__all__` определяет, что экспортируется при `from aircraft_model import *`
2. **Инкапсуляция импортов** — скрывает внутреннюю структуру модулей
3. **Версионирование** — атрибут `__version__ = "1.0.0"`

---

## Использование (CLI-интерфейс)

### Получение справки

```bash
python3 -m aircraft_model.main --help
```

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
│      Aircraft       │         │     Passenger        │
├─────────────────────┤         ├─────────────────────┤
│ - tail_number       │         │ - passport_number    │
│ - capacity          │  1..*   │ - seat_number        │
│ - status            │────────>│ - is_registered      │
│ - passengers: list  │         └─────────────────────┘
│ - crew: list        │
│ - service: IFS      │         ┌─────────────────────┐
└─────────┬───────────┘         │   CrewMember        │
          │                     ├─────────────────────┤
          │ 1..*                 │ - role: CrewRole    │
          ▼                     │ - license_number    │
┌─────────────────────┐         │ - is_on_duty        │
│    FlightRoute      │         └─────────────────────┘
├─────────────────────┤
│ - departure         │
│ - destination       │         ┌─────────────────────┐
│ - distance          │         │  InFlightService    │
└─────────────────────┘         ├─────────────────────┤
                                │ - inventory         │
┌─────────────────────┐         │ - service_limits   │
│       Runway        │         └─────────────────────┘
├─────────────────────┤
│ - length            │
│ - status            │         ┌─────────────────────┐
│ - queue             │         │       Ticket        │
└─────────────────────┘         ├─────────────────────┤
                                │ - status            │
                                │ - seat              │
                                └─────────────────────┘
```

#### Ответственности классов

| Класс | Ответственность |
|-------|-----------------|
| `Aircraft` | Управление состоянием самолёта, экипажем, пассажирами; взлёт/посадка |
| `Passenger` | Хранение данных пассажира, регистрация на рейс |
| `CrewMember` | Роль, дежурство, выполнение обязанностей |
| `Runway` | Управление очередью на взлёт/посадку |
| `FlightRoute` | Параметры маршрута (расстояние, время) |
| `InFlightService` | Учёт инвентаря, лимиты услуг |
| `Ticket` | Жизненный цикл билета |

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
                    │  ON_GROUND   │<───────────────────────┐
                    └──────┬───────┘                        │
                           │ can_take_off()                  │
                           ▼                                 │
                    ┌──────────────┐                        │
    ┌───────────────│  IN_FLIGHT   │───────────────────────┤
    │                └──────────────┘                       │
    │                                                    land()
    │ reset_after_landing()
    │                                                     │
    │ ┌──────────────┐                                     │
    │ │   LANDING    │ ────────────────────────────────────┘
    │ └──────────────┘
    │
    └──────────────────────────────────────┐
                                         │
                           ┌──────────────▼───────────────┐
                           │         BOARDING              │
                           └───────────────────────────────┘
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
            ├── RunwayError          — ошибки ВПП
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

# [runway.py:103-109]
def request_takeoff(self, aircraft: Aircraft) -> bool:
    if self._status == RunwayStatus.CLOSED:
        raise RunwayError(f"Runway {self._runway_id} is closed")
    if self._status == RunwayStatus.MAINTENANCE:
        raise RunwayError(f"Runway {self._runway_id} is under maintenance")
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

Класс `Ticket` реализует методы жизненного цикла:

```python
# [ticket.py:164-174]
def confirm(self) -> bool:
    """Подтвердить билет"""
    if self._status != TicketStatus.BOOKED:
        return False
    self._status = TicketStatus.CONFIRMED
    return True

def use(self) -> bool:
    """Пометить как использованный"""
    if self._status not in (TicketStatus.BOOKED, TicketStatus.CONFIRMED):
        raise FlightError(f"Cannot use ticket with status: {self._status.name}")
    self._status = TicketStatus.USED
    return True
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
| `test_ticket.py` | 15 тестов | Жизненный цикл, валидация |
| `test_flight_route.py` | 8 тестов | Валидация маршрута, свойства |
| `test_runway.py` | 12 тестов | Очередь, запросы, статус |
| `test_in_flight_service.py` | 10 тестов | Инвентарь, лимиты, услуги |
| `test_exceptions.py` | 9 тестов | Иерархия исключений |
| `test_enums.py` | 5 тестов | Значения перечислений |

**Итого: 161 тест**

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

## Соответствие требованиям лабораторной

| Требование | Статус | Подтверждение |
|------------|--------|---------------|
| Python 3.10+ | ✅ | `python3 -m pytest` — Python 3.12.3 |
| Аннотации типов | ✅ | Все классы и методы имеют type hints |
| PEP8 | ✅ | Формат кода соответствует стандарту |
| Кастомные исключения | ✅ | 10 классов в [`exceptions.py`](aircraft_model/exceptions.py) |
| CLI (argparse/typer/click) | ✅ | Интерактивный CLI в [`main.py`](aircraft_model/main.py) |
| pytest | ✅ | 161 тест, покрытие ~90% |
| Структура пакета с `__init__.py` | ✅ | Явный `__all__`, версия |
| GitHub | ✅ | Git-репозиторий инициализирован |
| Markdown-документация | ✅ | Данный README.md |

---

## Ответы на контрольные вопросы

### 1. Основные принципы ООП

| Принцип | Реализация в проекте |
|---------|---------------------|
| **Абстракция** | Классы моделируют сущности предметной области; скрыты детали реализации (валидация в private-методах `_validate_*`) |
| **Инкапсуляция** | Данные защищены через `_` prefix (`_model`, `_passengers`); доступ через property; `__all__` ограничивает публичный API |
| **Полиморфизм** | `TicketStatus`, `AircraftStatus` — разные enum со своими состояниями; методы `validate()` работают полиморфно для всех подклассов `FlightError` |
| **Модульность** | Пакет разделён на модули по ответственности; [`__init__.py`](aircraft_model/__init__.py) управляет экспортами |

### 2. Принципы SOLID

| Принцип | Реализация |
|---------|------------|
| **S**ingle Responsibility | Каждый класс: `Aircraft` — только самолёт, `Runway` — только ВПП |
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
- **Методы жизненного цикла** объектов (`register_for_flight()`, `use()`, `confirm()`)
- **Фабричный метод** `Ticket.issue()` для создания объектов

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
| **Студент** | dozhdik |
| **Группа** | PPOIS |
| **Дата** | 2026 |
| **Репозиторий** | GitHub |

---

*Документация сгенерирована на основе анализа исходного кода проекта.*
