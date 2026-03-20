# Лабораторная работа №2: Airline Management System

### Документация к лабораторной работе располагается по следующей <a href="https://press-cs.ru/PPOIS/BookWarehouse">ссылке</a>.

## Класс число_полей число_поведений(число_методов) -> Ассоциации:

Dimension 6 1(9)

Size 4 1(8) -> Dimension

Aircraft 8 1(18) -> Size

AirlineTool 5 1(6)

Seat 8 1(8)

CabinLighting 8 1(8)

SecurityCamera 8 1(8)

Gate 8 1(8)

Timer 4 1(9)

MaintenanceKit 6 1(7)

CleaningKit 6 1(3)

ConditionProfile 4 1(8)

CabinClimateControl 9 1(19) -> Timer, ConditionProfile

SecuritySystem 4 1(9)

Flight 1 1(5)

PassengerFlight 4 1(2) -> Aircraft, Seat

CargoFlight 3 1(2) -> Aircraft, Gate

CharterFlight 4 1(2) -> Aircraft, SecurityCamera

MixedFlight 5 1(2) -> Aircraft, Gate

BusinessFlight 4 1(2) -> Aircraft, Gate

VintageFlight 4 1(2) -> Aircraft, CabinClimateControl

ModernFlight 4 1(2) -> Aircraft, Gate

EconomyFlight 3 1(2) -> Aircraft, Seat

InternationalFlight 4 1(2) -> Aircraft, Gate

DomesticFlight 4 1(2) -> Aircraft, SecurityCamera

LongHaulFlight 4 1(2) -> Aircraft, Seat

MaintenanceFlight 3 1(2) -> Aircraft, MaintenanceKit

SeasonalFlight 4 1(2) -> Aircraft, Gate

RegularFlight 4 1(2) -> Aircraft, SecuritySystem

InteractiveFlight 4 1(2) -> Aircraft, SecurityCamera

ThematicFlight 5 1(2) -> Aircraft, Gate

RetrospectiveFlight 4 1(2) -> Aircraft, CabinClimateControl

GroupFlight 5 1(2) -> Aircraft, Seat

SoloFlight 3 1(2) -> Aircraft

FlightDispatcher 1 1(2) -> Flight

Passenger 6 1(18) -> Aircraft

AirlineMenu 4 1(11) -> Flight, Passenger

BookingSystem 7 1(15) -> Passenger, Flight

### Исключение количество_полей количество_методов:

AircraftNotFoundException 0 1

NotEnoughAircraftException 0 1

ToolNotAvailableException 0 1

InvalidConditionException 0 1

TimerNotSetException 0 1

OverexposedAircraftException 0 1

UnderexposedAircraftException 0 1

StorageException 0 1

SecurityBreachException 0 1

MaintenanceFailedException 0 1

InsufficientSpaceException 0 1

InvalidAccessException 0 1

## Итого:

Поля: 182

Поведения (методы): 38(229)

Ассоциации: 47

Исключения: 12

Классы: 50

## Test Coverage

**Current test coverage: 86.5%**

- **Covered lines:** 850
- **Total lines:** 983
- **Uncovered lines:** 133

For detailed coverage report, see [Coverage Report](coverage_report.html) or [Detailed lcov Report](coverage_html/index.html).
