/**
 * @file main.cpp
 * @author Dozhdikov Alexander, group 421702
 * @brief Main entry point for the Airline management system
 * @version 0.1
 * @date 2025-01-15
 * 
 * This file contains the main function that demonstrates the airline system
 * with various aircrafts, tools, and flights.
 */

#include "airline.hpp"
#include <vector>
#include <memory>

namespace {
    Aircraft createAircraft(const char* name, double size, double value, bool fragile, Dimension* dim, int id) {
        return Aircraft(name, Size(size, dim, false, id), value, fragile);
    }
    
    void initializeDimensions(Dimension& cm, Dimension& inch, Dimension& meter) {
        cm = Dimension("cm", 1.0, true, 1);
        inch = Dimension("in", 2.54, false, 2);
        meter = Dimension("m", 100.0, true, 3);
    }
    
    void initializeAircraftFleet(std::vector<Aircraft>& fleet, Dimension* dim) {
        const struct {
            const char* name;
            double size;
            double value;
            bool fragile;
        } aircraftData[] = {
            {"Boeing 737", 77.0, 850000000.0, true},
            {"Airbus A320", 73.7, 100000000.0, true},
            {"Boeing 777", 517.0, 200000000.0, true},
            {"Boeing 787 Dreamliner", 40.6, 5000000.0, false},
            {"Airbus A350 XWB", 30.5, 3000000.0, false},
            {"Boeing 747-8", 120.0, 50000.0, false},
            {"Airbus A380", 200.0, 75000.0, false},
            {"Boeing 707", 100.0, 50000000.0, true},
            {"Douglas DC-3", 150.0, 30000000.0, true},
            {"Boeing 787-9", 180.0, 2000000.0, false},
            {"Airbus A330", 250.0, 1500000.0, true},
            {"Boeing 737 MAX", 60.0, 800000.0, false},
            {"Boeing 777-300ER", 140.0, 1200000.0, false},
            {"Airbus A321", 160.0, 900000.0, false},
            {"Boeing 767", 80.0, 600000.0, true},
            {"Airbus A319", 70.0, 550000.0, true},
            {"Boeing 777-200LR", 120.0, 700000.0, true},
            {"Airbus A340", 110.0, 650000.0, true},
            {"Boeing 747-400", 150.0, 10000000.0, true},
            {"Temporary Aircraft 1", 100.0, 400000.0, false},
            {"Temporary Aircraft 2", 95.0, 380000.0, false},
            {"Boeing 777-9X", 130.0, 5000000.0, true},
            {"Airbus A350-1000", 125.0, 4800000.0, true},
            {"Boeing 787-10", 180.0, 300000.0, false},
            {"Airbus A330neo", 175.0, 280000.0, false},
            {"Thematic Aircraft 1", 85.0, 450000.0, false},
            {"Thematic Aircraft 2", 90.0, 470000.0, false},
            {"Thematic Aircraft 3", 88.0, 460000.0, false},
            {"Boeing 727", 140.0, 2500000.0, true},
            {"Boeing 757", 135.0, 2300000.0, true},
            {"Group Aircraft 1", 100.0, 500000.0, false},
            {"Group Aircraft 2", 105.0, 520000.0, false},
            {"Group Aircraft 3", 98.0, 490000.0, false},
            {"Boeing 737-300", 115.0, 600000.0, false},
            {"Airbus A300", 110.0, 580000.0, false},
            {"Boeing 737-400", 95.0, 350000.0, false},
            {"Airbus A310", 100.0, 370000.0, false},
            {"Boeing 737-200", 92.0, 340000.0, false}
        };
        
        fleet.reserve(sizeof(aircraftData) / sizeof(aircraftData[0]));
        for (size_t i = 0; i < sizeof(aircraftData) / sizeof(aircraftData[0]); ++i) {
            fleet.push_back(createAircraft(
                aircraftData[i].name,
                aircraftData[i].size,
                aircraftData[i].value,
                aircraftData[i].fragile,
                dim,
                static_cast<int>(i + 1)
            ));
        }
    }
    
    void initializeTools(
        std::vector<Seat>& seats,
        std::vector<CabinLighting>& lights,
        std::vector<SecurityCamera>& cameras,
        std::vector<Gate>& gates,
        std::vector<MaintenanceKit>& kits,
        std::vector<CleaningKit>& cleaningKits,
        std::vector<CabinClimateControl>& climates,
        std::vector<SecuritySystem>& securitySystems,
        std::vector<Timer>& timers
    ) {
        seats.push_back(Seat("Classic Seat", true, 50, 1));
        seats.push_back(Seat("Modern Seat", true, 60, 2));
        seats.push_back(Seat("Protective Seat", true, 55, 3));
        
        lights.push_back(CabinLighting("Airline CabinLighting", true, false, 1));
        lights.push_back(CabinLighting("Accent CabinLighting", true, false, 2));
        lights.push_back(CabinLighting("Dim CabinLighting", true, true, 3));
        
        cameras.push_back(SecurityCamera("Main Security Camera", 90.0, false, false));
        cameras.push_back(SecurityCamera("Secondary Camera", 120.0, false, false));
        cameras.push_back(SecurityCamera("Entrance Camera", 180.0, false, false));
        
        gates.push_back(Gate("Main Boarding Gate", 5.0, true, false));
        gates.push_back(Gate("Cargo Gate", 3.0, true, false));
        gates.push_back(Gate("Seasonal Gate", 4.0, true, false));
        
        kits.push_back(MaintenanceKit("Professional Maintenance Kit", false));
        kits.push_back(MaintenanceKit("Standard Maintenance Kit", false));
        
        cleaningKits.push_back(CleaningKit("Aircraft Cleaning Kit", 1));
        cleaningKits.push_back(CleaningKit("Interior Cleaning Kit", 2));
        
        climates.push_back(CabinClimateControl(0.0, false, true));
        climates.push_back(CabinClimateControl(0.0, false, true));
        
        securitySystems.push_back(SecuritySystem(6, 0, true, false));
        securitySystems.push_back(SecuritySystem(4, 0, true, false));
        
        for (int i = 1; i <= 18; ++i) {
            timers.push_back(Timer(0, false, 0, i));
        }
    }
}

/**
 * @brief Run the airline system
 * 
 * Creates aircrafts, tools, flights, and runs the airline menu system.
 * This function can be called from main() or from tests.
 * 
 * @param skipMenuRun if true, skips menu.run() call (useful for testing)
 * @return int exit code (0 on success, 1 on error)
 */
int runAirlineSystem(bool skipMenuRun = false) {
    try {
        Dimension cmUnit, inchUnit, meterUnit;
        initializeDimensions(cmUnit, inchUnit, meterUnit);
        
        std::vector<Aircraft> aircraftFleet;
        initializeAircraftFleet(aircraftFleet, &cmUnit);
        
        std::vector<Seat> seats;
        std::vector<CabinLighting> lights;
        std::vector<SecurityCamera> cameras;
        std::vector<Gate> gates;
        std::vector<MaintenanceKit> maintenanceKits;
        std::vector<CleaningKit> cleaningKits;
        std::vector<CabinClimateControl> climates;
        std::vector<SecuritySystem> securitySystems;
        std::vector<Timer> timers;
        
        initializeTools(seats, lights, cameras, gates, maintenanceKits, 
                       cleaningKits, climates, securitySystems, timers);
        
        FlightDispatcher dispatcher("Main FlightDispatcher");
        
        PassengerFlight passengerFlight(
            "Domestic Passenger Flight",
            &aircraftFleet[0], &aircraftFleet[1],
            &seats[0]
        );
        
        CargoFlight cargoFlight(
            "Freight Cargo Flight",
            &aircraftFleet[2], &gates[1]
        );
        
        CharterFlight charterFlight(
            "Private Charter Flight",
            &aircraftFleet[3], &aircraftFleet[4],
            &cameras[0]
        );
        
        MixedFlight mixedMediaFlight(
            "Combined Cargo Flight",
            &aircraftFleet[35], &aircraftFleet[36], &aircraftFleet[37],
            &gates[0]
        );
        
        BusinessFlight businessArtFlight(
            "Business Class Flight",
            &aircraftFleet[5], &aircraftFleet[6],
            &gates[2]
        );
        
        VintageFlight vintageFlight(
            "Classic Aircraft Flight",
            &aircraftFleet[7], &aircraftFleet[8],
            &climates[0]
        );
        
        ModernFlight modernFlight(
            "Modern Aircraft Flight",
            &aircraftFleet[9], &aircraftFleet[10],
            &gates[0]
        );
        
        EconomyFlight economyFlight(
            "Economy Class Flight",
            &aircraftFleet[11], &seats[1]
        );
        
        InternationalFlight internationalFlight(
            "Transcontinental Flight",
            &aircraftFleet[12], &aircraftFleet[13],
            &gates[0]
        );
        
        DomesticFlight domesticFlight(
            "Regional Domestic Flight",
            &aircraftFleet[14], &aircraftFleet[15],
            &cameras[2]
        );
        
        LongHaulFlight longHaulFlight(
            "Transoceanic Flight",
            &aircraftFleet[16], &aircraftFleet[17],
            &seats[1]
        );
        
        MaintenanceFlight maintenanceFlight(
            "Aircraft Maintenance Flight",
            &aircraftFleet[18], &maintenanceKits[0]
        );
        
        SeasonalFlight seasonalFlight(
            "Seasonal Special Flight",
            &aircraftFleet[19], &aircraftFleet[20],
            &gates[2]
        );
        
        RegularFlight regularFlight(
            "Scheduled Regular Flight",
            &aircraftFleet[21], &aircraftFleet[22],
            &securitySystems[1]
        );
        
        InteractiveFlight interactiveFlight(
            "Entertainment Flight",
            &aircraftFleet[23], &aircraftFleet[24],
            &cameras[0]
        );
        
        ThematicFlight thematicFlight(
            "Special Route Flight",
            &aircraftFleet[25], &aircraftFleet[26], &aircraftFleet[27],
            &gates[0]
        );
        
        RetrospectiveFlight retrospectiveFlight(
            "Heritage Aircraft Flight",
            &aircraftFleet[28], &aircraftFleet[29],
            &climates[0]
        );
        
        GroupFlight groupFlight(
            "Group Charter Flight",
            &aircraftFleet[30], &aircraftFleet[31], &aircraftFleet[32],
            &seats[1]
        );
        
        SoloFlight soloFlight(
            "Private Solo Flight",
            &aircraftFleet[33], &aircraftFleet[34]
        );
        
        Passenger customer("Airline Passenger", 2, false);
        customer.purchaseTicket();
        customer.enterAirline();
        
        AirlineMenu menuSystem;
        menuSystem.setPassenger(&customer);
        
        Flight* allFlights[] = {
            &passengerFlight, &cargoFlight, &charterFlight, &mixedMediaFlight,
            &businessArtFlight, &vintageFlight, &modernFlight, &economyFlight,
            &internationalFlight, &domesticFlight, &longHaulFlight, &maintenanceFlight,
            &seasonalFlight, &regularFlight, &interactiveFlight, &thematicFlight,
            &retrospectiveFlight, &groupFlight, &soloFlight
        };
        
        for (Flight* flight : allFlights) {
            menuSystem.addFlight(flight);
        }
        
        if (!skipMenuRun) {
            menuSystem.run();
        }
    }
    catch (const std::exception& ex) {
        std::cerr << "\n[ERROR] System failure: " << ex.what() << std::endl;
        return 1;
    }
    return 0;
}

/**
 * @brief Main function
 * 
 * Entry point for the airline management system.
 * 
 * @return int exit code (0 on success, 1 on error)
 */
#ifndef TESTING
int main() {
    return runAirlineSystem();
}
#endif
