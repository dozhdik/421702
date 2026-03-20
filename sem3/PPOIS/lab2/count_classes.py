# Manual counting based on airline.hpp analysis

classes = {
    # Exceptions (all have 0 fields, 1 method - constructor)
    "AircraftNotFoundException": {"fields": 0, "methods": 1, "associations": []},
    "NotEnoughAircraftException": {"fields": 0, "methods": 1, "associations": []},
    "ToolNotAvailableException": {"fields": 0, "methods": 1, "associations": []},
    "InvalidConditionException": {"fields": 0, "methods": 1, "associations": []},
    "TimerNotSetException": {"fields": 0, "methods": 1, "associations": []},
    "OverexposedAircraftException": {"fields": 0, "methods": 1, "associations": []},
    "UnderexposedAircraftException": {"fields": 0, "methods": 1, "associations": []},
    "StorageException": {"fields": 0, "methods": 1, "associations": []},
    "SecurityBreachException": {"fields": 0, "methods": 1, "associations": []},
    "MaintenanceFailedException": {"fields": 0, "methods": 1, "associations": []},
    "InsufficientSpaceException": {"fields": 0, "methods": 1, "associations": []},
    "InvalidAccessException": {"fields": 0, "methods": 1, "associations": []},
    
    # Regular classes
    "Dimension": {"fields": 6, "methods": 9, "associations": []},  # name, cmPerUnit, metric, id, precision, gateard
    "Size": {"fields": 4, "methods": 8, "associations": ["Dimension"]},  # value, dimension*, approximate, id
    "Aircraft": {"fields": 8, "methods": 18, "associations": ["Size"]},  # name, size, value, fragile, year, manufacturer, certified, insuranceValue
    "AirlineTool": {"fields": 5, "methods": 6, "associations": []},  # name, clean, available, busy, durability
    "Seat": {"fields": 8, "methods": 8, "associations": []},  # 5 from AirlineTool + 3 own (protective, width, id)
    "CabinLighting": {"fields": 8, "methods": 8, "associations": []},  # 5 from AirlineTool + 3 own (led, dimmed, id)
    "SecurityCamera": {"fields": 8, "methods": 8, "associations": []},  # 5 from AirlineTool + 3 own (angle, recording, active)
    "Gate": {"fields": 8, "methods": 8, "associations": []},  # 5 from AirlineTool + 3 own (capacity, hasCover, inUse)
    "Timer": {"fields": 4, "methods": 9, "associations": []},  # seconds, running, elapsed, id
    "MaintenanceKit": {"fields": 6, "methods": 7, "associations": []},  # 5 from AirlineTool + 1 own (equipped)
    "CleaningKit": {"fields": 6, "methods": 3, "associations": []},  # 5 from AirlineTool + 1 own (id)
    "ConditionProfile": {"fields": 4, "methods": 8, "associations": []},  # startTemp, targetTemp, duration, gradual
    "CabinClimateControl": {"fields": 9, "methods": 19, "associations": ["Timer", "ConditionProfile"]},  # temperature, on, doorClosed, controlTimer, profile, elapsedSeconds, humidity, targetHumidity, alarmActive
    "SecuritySystem": {"fields": 4, "methods": 9, "associations": []},  # zones, activeZones, alarm, on
    "Flight": {"fields": 1, "methods": 5, "associations": []},  # name
    "PassengerFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "Seat"]},  # 1 from Flight + 3 own (passenger1*, passenger2*, use_seat*)
    "CargoFlight": {"fields": 3, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 2 own (cargo*, gate*)
    "CharterFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "SecurityCamera"]},  # 1 from Flight + 3 own (charter1*, charter2*, camera*)
    "MixedFlight": {"fields": 5, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 4 own (aircraft1*, aircraft2*, aircraft3*, gate*)
    "BusinessFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 3 own (business1*, business2*, gate*)
    "VintageFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "CabinClimateControl"]},  # 1 from Flight + 3 own (vintage1*, vintage2*, cabinClimate*)
    "ModernFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 3 own (modern1*, modern2*, gate*)
    "EconomyFlight": {"fields": 3, "methods": 2, "associations": ["Aircraft", "Seat"]},  # 1 from Flight + 2 own (economy*, seat*)
    "InternationalFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 3 own (international1*, international2*, gate*)
    "DomesticFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "SecurityCamera"]},  # 1 from Flight + 3 own (domestic1*, domestic2*, camera*)
    "LongHaulFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "Seat"]},  # 1 from Flight + 3 own (longHaul1*, longHaul2*, seat*)
    "MaintenanceFlight": {"fields": 3, "methods": 2, "associations": ["Aircraft", "MaintenanceKit"]},  # 1 from Flight + 2 own (aircraft*, maintenanceKit*)
    "SeasonalFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 3 own (seasonal1*, seasonal2*, gate*)
    "RegularFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "SecuritySystem"]},  # 1 from Flight + 3 own (regular1*, regular2*, security*)
    "InteractiveFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "SecurityCamera"]},  # 1 from Flight + 3 own (interactive1*, interactive2*, camera*)
    "ThematicFlight": {"fields": 5, "methods": 2, "associations": ["Aircraft", "Gate"]},  # 1 from Flight + 4 own (theme1*, theme2*, theme3*, gate*)
    "RetrospectiveFlight": {"fields": 4, "methods": 2, "associations": ["Aircraft", "CabinClimateControl"]},  # 1 from Flight + 3 own (retro1*, retro2*, cabinClimate*)
    "GroupFlight": {"fields": 5, "methods": 2, "associations": ["Aircraft", "Seat"]},  # 1 from Flight + 4 own (group1*, group2*, group3*, seat*)
    "SoloFlight": {"fields": 3, "methods": 2, "associations": ["Aircraft"]},  # 1 from Flight + 2 own (solo1*, solo2*)
    "FlightDispatcher": {"fields": 1, "methods": 2, "associations": ["Flight"]},  # name, organizeFlight takes Flight*
    "Passenger": {"fields": 6, "methods": 18, "associations": ["Aircraft"]},  # name, accessLevel, hasTicket, visitDuration, favoriteCount, guidedTour; viewAircraft takes Aircraft*
    "AirlineMenu": {"fields": 4, "methods": 11, "associations": ["Flight", "Passenger"]},  # MAX_FLIGHTS (const), flights[], flightCount, currentPassenger*
    "BookingSystem": {"fields": 7, "methods": 15, "associations": ["Passenger", "Flight"]},  # systemName, totalBookings, totalRevenue, isActive, maxBookings, currentBookingPassenger*, currentBookingFlight*
}

total_fields = sum(c["fields"] for c in classes.values())
total_methods = sum(c["methods"] for c in classes.values())
total_associations = sum(len(c["associations"]) for c in classes.values())
exception_count = sum(1 for name in classes if "Exception" in name)
regular_class_count = len(classes) - exception_count

print(f"Total fields: {total_fields}")
print(f"Total methods: {total_methods}")
print(f"Total associations: {total_associations}")
print(f"Exceptions: {exception_count}")
print(f"Regular classes: {regular_class_count}")
print(f"Total classes: {len(classes)}")
