/**
 * @file airline.hpp
 * @author Dozhdikov Alexander, group 421702
 * @brief Header file for the Airline management system
 * @date 2025-01-15
 * 
 * This file contains all classes for managing an airline system including
 * aircraft, flights, tools, cabinClimate control, security, and passenger management.
 */

#pragma once
#include <iostream>
#include <iomanip>
#include <stdexcept>
using namespace std;

/**
 * @class AircraftNotFoundException
 * @brief Exception thrown when aircraft is not found
 */
class AircraftNotFoundException : public runtime_error {
public:
    /**
     * @brief Construct a new AircraftNotFoundException object
     * 
     * @param msg constant pointer to the error message
     */
    AircraftNotFoundException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class NotEnoughAircraftException
 * @brief Exception thrown when there is not enough aircraft available
 */
class NotEnoughAircraftException : public runtime_error {
public:
    /**
     * @brief Construct a new NotEnoughAircraftException object
     * 
     * @param msg constant pointer to the error message
     */
    NotEnoughAircraftException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class ToolNotAvailableException
 * @brief Exception thrown when a tool is not available for use
 */
class ToolNotAvailableException : public runtime_error {
public:
    /**
     * @brief Construct a new ToolNotAvailableException object
     * 
     * @param msg constant pointer to the error message
     */
    ToolNotAvailableException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class InvalidConditionException
 * @brief Exception thrown when cabinClimate conditions are invalid
 */
class InvalidConditionException : public runtime_error {
public:
    /**
     * @brief Construct a new InvalidConditionException object
     * 
     * @param msg constant pointer to the error message
     */
    InvalidConditionException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class TimerNotSetException
 * @brief Exception thrown when timer is not properly set
 */
class TimerNotSetException : public runtime_error {
public:
    /**
     * @brief Construct a new TimerNotSetException object
     * 
     * @param msg constant pointer to the error message
     */
    TimerNotSetException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class OverexposedAircraftException
 * @brief Exception thrown when aircraft is overexposed to conditions
 */
class OverexposedAircraftException : public runtime_error {
public:
    /**
     * @brief Construct a new OverexposedAircraftException object
     * 
     * @param msg constant pointer to the error message
     */
    OverexposedAircraftException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class UnderexposedAircraftException
 * @brief Exception thrown when aircraft is underexposed to conditions
 */
class UnderexposedAircraftException : public runtime_error {
public:
    /**
     * @brief Construct a new UnderexposedAircraftException object
     * 
     * @param msg constant pointer to the error message
     */
    UnderexposedAircraftException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class StorageException
 * @brief Exception thrown when storage operation fails
 */
class StorageException : public runtime_error {
public:
    /**
     * @brief Construct a new StorageException object
     * 
     * @param msg constant pointer to the error message
     */
    StorageException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class SecurityBreachException
 * @brief Exception thrown when security breach is detected
 */
class SecurityBreachException : public runtime_error {
public:
    /**
     * @brief Construct a new SecurityBreachException object
     * 
     * @param msg constant pointer to the error message
     */
    SecurityBreachException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class MaintenanceFailedException
 * @brief Exception thrown when maintenance process fails
 */
class MaintenanceFailedException : public runtime_error {
public:
    /**
     * @brief Construct a new MaintenanceFailedException object
     * 
     * @param msg constant pointer to the error message
     */
    MaintenanceFailedException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class InsufficientSpaceException
 * @brief Exception thrown when there is insufficient space
 */
class InsufficientSpaceException : public runtime_error {
public:
    /**
     * @brief Construct a new InsufficientSpaceException object
     * 
     * @param msg constant pointer to the error message
     */
    InsufficientSpaceException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class InvalidAccessException
 * @brief Exception thrown when access is invalid or denied
 */
class InvalidAccessException : public runtime_error {
public:
    /**
     * @brief Construct a new InvalidAccessException object
     * 
     * @param msg constant pointer to the error message
     */
    InvalidAccessException(const char* msg) : runtime_error(msg) {}
};

/**
 * @class Dimension
 * @brief Class for representing measurement dimensions
 * 
 * Handles different measurement units and conversions between them.
 * Supports both metric and non-metric units with precision control.
 */
class Dimension {
private:
    const char* name;        ///< Name of the dimension unit
    double cmPerUnit;        ///< Conversion factor to centimeters per unit
    bool metric;            ///< Whether the dimension is metric
    int id;                 ///< Unique identifier for the dimension
    double precision;       ///< Precision value for measurements
    bool gateard;          ///< Whether this is a gateard dimension

public:
    /**
     * @brief Construct a new Dimension object
     * 
     * @param n constant pointer to the dimension name
     * @param c double value containing centimeters per unit
     * @param m boolean value indicating if metric
     * @param i integer value containing dimension identifier
     */
    Dimension(const char* n = "unit", double c = 1.0, bool m = true, int i = 0);

    /**
     * @brief Convert amount to centimeters
     * 
     * @param amount double value containing amount to convert
     * @return double containing converted value in centimeters
     */
    double toCentimeters(double amount) const;

    /**
     * @brief Check if dimension is metric
     * 
     * @return true if dimension is metric
     * @return false if dimension is not metric
     */
    bool isMetric() const;

    /**
     * @brief Get the dimension identifier
     * 
     * @return int containing dimension identifier
     */
    int getId() const;

    /**
     * @brief Set the precision value
     * 
     * @param p double value containing precision to set
     */
    void setPrecision(double p);

    /**
     * @brief Check if dimension is gateard
     * 
     * @return true if dimension is gateard
     * @return false if dimension is not gateard
     */
    bool isStandard() const;

    /**
     * @brief Convert centimeters to dimension units
     * 
     * @param cm double value containing centimeters to convert
     * @return double containing converted value in dimension units
     */
    double fromCentimeters(double cm) const;

    /**
     * @brief Convert to another dimension unit
     * 
     * @param amount double value containing amount to convert
     * @param targetDimension pointer to target Dimension object
     * @return double containing converted value
     */
    double convertTo(double amount, Dimension* targetDimension) const;

    /**
     * @brief Validate dimension conversion
     * 
     * @param amount double value containing amount to validate
     * @return bool indicating if conversion is valid
     */
    bool validateConversion(double amount) const;
};

/**
 * @class Size
 * @brief Class for representing aircraft size with dimension
 * 
 * Represents size with a specific dimension unit and handles
 * conversions and scaling operations.
 */
class Size {
private:
    double value;           ///< Size value in the dimension unit
    Dimension* dimension;  ///< Pointer to the dimension object
    bool approximate;       ///< Whether the size is approximate
    int id;                 ///< Unique identifier for the size

public:
    /**
     * @brief Construct a new Size object
     * 
     * @param v double value containing size value
     * @param d pointer to the Dimension object
     * @param appr boolean value indicating if approximate
     * @param i integer value containing size identifier
     */
    Size(double v = 0.0, Dimension* d = nullptr, bool appr = false, int i = 0);

    /**
     * @brief Convert size to centimeters
     * 
     * @return double containing size in centimeters
     * @throws StorageException if dimension is not set
     */
    double toCentimeters() const;

    /**
     * @brief Scale the size by a factor
     * 
     * @param factor double value containing scaling factor
     */
    void scale(double factor);

    /**
     * @brief Check if size is zero
     * 
     * @return true if size is zero or less
     * @return false if size is greater than zero
     */
    bool isZero() const;

    /**
     * @brief Get the size value
     * 
     * @return double containing size value
     */
    double getValue() const;

    /**
     * @brief Check if size is approximate
     * 
     * @return true if size is approximate
     * @return false otherwise
     */
    bool isApproximate() const;

    /**
     * @brief Convert size to different dimension
     * 
     * @param targetDimension pointer to target Dimension object
     * @return double containing converted size value
     */
    double convertToDimension(Dimension* targetDimension) const;

    /**
     * @brief Calculate size difference
     * 
     * @param otherSize constant reference to other Size object
     * @return double containing size difference in centimeters
     */
    double calculateDifference(const Size& otherSize) const;
};

/**
 * @class Aircraft
 * @brief Main class for representing aircraft in the airline
 * 
 * Represents an aircraft with comprehensive information including
 * name, size, value, fragility, certification status, and insurance value.
 * Provides operations for size management and certification.
 */
class Aircraft {
private:
    const char* name;           ///< Name of the aircraft
    Size size;                  ///< Size of the aircraft
    double value;               ///< Monetary value of the aircraft
    bool fragile;               ///< Whether the aircraft is fragile
    int year;                   ///< Year the aircraft was manufactured
    const char* manufacturer;   ///< Name of the manufacturer
    bool certified;             ///< Whether the aircraft is certified
    double insuranceValue;      ///< Insurance value of the aircraft

public:
    /**
     * @brief Construct a new Aircraft object
     * 
     * @param n constant pointer to the aircraft name
     * @param s constant reference to the Size object
     * @param v double value containing aircraft value
     * @param fr boolean value indicating if fragile
     */
    Aircraft(const char* n, const Size& s, double v, bool fr);

    /**
     * @brief Add size to the aircraft
     * 
     * @param v double value containing size to add in centimeters
     */
    void addSize(double v);

    /**
     * @brief Use a portion of the aircraft size
     * 
     * @param vCm double value containing size to use in centimeters
     * @throws NotEnoughAircraftException if requested size exceeds available size
     */
    void useSize(double vCm);

    /**
     * @brief Check if aircraft is fragile
     * 
     * @return true if aircraft is fragile
     * @return false if aircraft is not fragile
     */
    bool isFragile() const;

    /**
     * @brief Certify the aircraft
     */
    void certify();

    /**
     * @brief Set the insurance value
     * 
     * @param val double value containing insurance value
     */
    void setInsuranceValue(double val);

    /**
     * @brief Get the year the aircraft was manufactured
     * 
     * @return int containing manufacturing year
     */
    int getYear() const;

    /**
     * @brief Get the manufacturer name
     * 
     * @return const char* containing manufacturer name
     */
    const char* getManufacturer() const;

    /**
     * @brief Get the aircraft name
     * 
     * @return const char* containing aircraft name
     */
    const char* getName() const;

    /**
     * @brief Get the aircraft value
     * 
     * @return double containing aircraft value
     */
    double getValue() const;

    /**
     * @brief Check if aircraft is certified
     * 
     * @return true if aircraft is certified
     * @return false otherwise
     */
    bool isCertified() const;

    /**
     * @brief Calculate maintenance cost for aircraft
     * 
     * @return double containing maintenance cost
     */
    double calculateMaintenanceCost() const;

    /**
     * @brief Check if aircraft is available for flight
     * 
     * @return bool indicating if aircraft is available
     */
    bool isAvailableForFlight() const;

    /**
     * @brief Calculate depreciation value
     * 
     * @param currentYear integer value containing current year
     * @return double containing depreciation value
     */
    double calculateDepreciation(int currentYear) const;

    /**
     * @brief Check if aircraft needs inspection
     * 
     * @return bool indicating if inspection is needed
     */
    bool needsInspection() const;

    /**
     * @brief Calculate fuel consumption estimate
     * 
     * @param distance double value containing distance in km
     * @return double containing fuel consumption in liters
     */
    double calculateFuelConsumption(double distance) const;
};

/**
 * @class AirlineTool
 * @brief Base class for all airline tools
 * 
 * Provides common functionality for airline tools including
 * availability checking, cleaning, and durability management.
 */
class AirlineTool {
protected:
    const char* name;        ///< Name of the tool
    bool clean;             ///< Whether the tool is clean
    bool available;         ///< Whether the tool is available
    bool busy;              ///< Whether the tool is currently in use
    int durability;         ///< Durability level of the tool

public:
    /**
     * @brief Construct a new AirlineTool object
     * 
     * @param n constant pointer to the tool name
     * @param c boolean value indicating if clean
     * @param a boolean value indicating if available
     * @param d integer value containing durability level
     */
    AirlineTool(const char* n = "tool",
                bool c = true,
                bool a = true,
                int d = 100);

    /**
     * @brief Use the tool
     * 
     * @throws ToolNotAvailableException if tool is not usable
     */
    void useTool();

    /**
     * @brief Clean the tool
     */
    void cleanTool();

    /**
     * @brief Break the tool (set unavailable and zero durability)
     */
    void breakTool();

    /**
     * @brief Check if tool is available
     * 
     * @return true if tool is available, clean, and has durability
     * @return false otherwise
     */
    bool isAvailable() const;

    /**
     * @brief Get the tool name
     * 
     * @return const char* containing tool name
     */
    const char* getName() const;
};

/**
 * @class Seat
 * @brief Class for airline seats
 * 
 * Represents a seat tool with protective capabilities for passengers.
 */
class Seat : public AirlineTool {
private:
    bool protective;     ///< Whether the seat provides protection
    int width;           ///< Width of the seat
    int id;              ///< Unique identifier for the seat

public:
    /**
     * @brief Construct a new Seat object
     * 
     * @param n constant pointer to the seat name
     * @param p boolean value indicating if protective
     * @param w integer value containing seat width
     * @param i integer value containing seat identifier
     */
    Seat(const char* n = "Seat",
          bool p = true,
          int w = 50,
          int i = 0);

    /**
     * @brief Add protection to the seat
     */
    void addProtection();

    /**
     * @brief Remove protection from the seat
     */
    void removeProtection();

    /**
     * @brief Check if seat can protect passenger
     * 
     * @return true if seat is available and protective
     * @return false otherwise
     */
    bool canProtect() const;

    /**
     * @brief Get the seat width
     * 
     * @return int containing seat width
     */
    int getWidth() const;

    /**
     * @brief Calculate seat comfort score
     * 
     * @return double containing comfort score (0-10)
     */
    double calculateComfortScore() const;

    /**
     * @brief Check if seat is suitable for passenger
     * 
     * @param passengerWeight double value containing passenger weight
     * @return bool indicating if seat is suitable
     */
    bool isSuitableForPassenger(double passengerWeight) const;

    /**
     * @brief Adjust seat position
     * 
     * @param position integer value containing position angle
     */
    void adjustPosition(int position);
};

/**
 * @class CabinLighting
 * @brief Class for cabin cabinLighting systems
 * 
 * Represents cabinLighting equipment with LED and dimming capabilities
 * for safe cabin illumination.
 */
class CabinLighting : public AirlineTool {
private:
    bool led;        ///< Whether the cabinLighting uses LED technology
    bool dimmed;     ///< Whether the cabinLighting is dimmed
    int id;          ///< Unique identifier for the cabinLighting

public:
    /**
     * @brief Construct a new CabinLighting object
     * 
     * @param n constant pointer to the cabinLighting name
     * @param l boolean value indicating if LED
     * @param d boolean value indicating if dimmed
     * @param i integer value containing cabinLighting identifier
     */
    CabinLighting(const char* n = "CabinLighting",
             bool l = true,
             bool d = false,
             int i = 0);

    /**
     * @brief Dim the cabinLighting
     */
    void dim();

    /**
     * @brief Brighten the cabinLighting
     */
    void brighten();

    /**
     * @brief Check if cabinLighting is safe for cabin
     * 
     * @return true if LED, not dimmed, and available
     * @return false otherwise
     */
    bool isSafeForCabin() const;

    /**
     * @brief Check if lighting uses LED technology
     * 
     * @return true if LED
     * @return false otherwise
     */
    bool isLED() const;

    /**
     * @brief Calculate power consumption
     * 
     * @return double containing power consumption in watts
     */
    double calculatePowerConsumption() const;

    /**
     * @brief Set brightness level
     * 
     * @param level integer value containing brightness level (0-100)
     */
    void setBrightness(int level);

    /**
     * @brief Check if lighting meets safety standards
     * 
     * @return bool indicating if meets standards
     */
    bool meetsSafetyStandards() const;
};

/**
 * @class SecurityCamera
 * @brief Class for security camera systems
 * 
 * Represents security cameras with recording and angle control capabilities.
 */
class SecurityCamera : public AirlineTool {
private:
    double angle;        ///< Camera viewing angle in degrees
    bool recording;      ///< Whether the camera is recording
    bool active;         ///< Whether the camera is active

public:
    /**
     * @brief Construct a new SecurityCamera object
     * 
     * @param n constant pointer to the camera name
     * @param a double value containing viewing angle
     * @param r boolean value indicating if recording
     * @param act boolean value indicating if active
     */
    SecurityCamera(const char* n = "Camera",
                   double a = 90.0,
                   bool r = false,
                   bool act = false);

    /**
     * @brief Start recording
     * 
     * @throws ToolNotAvailableException if camera is not available
     */
    void startRecording();

    /**
     * @brief Stop recording
     */
    void stopRecording();

    /**
     * @brief Check if camera is recording
     * 
     * @return true if camera is recording
     * @return false otherwise
     */
    bool isRecording() const;

    /**
     * @brief Get the camera viewing angle
     * 
     * @return double containing viewing angle in degrees
     */
    double getAngle() const;

    /**
     * @brief Adjust camera angle
     * 
     * @param newAngle double value containing new angle in degrees
     */
    void adjustAngle(double newAngle);

    /**
     * @brief Calculate coverage area
     * 
     * @param distance double value containing distance in meters
     * @return double containing coverage area in square meters
     */
    double calculateCoverageArea(double distance) const;

    /**
     * @brief Check if camera can monitor area
     * 
     * @param areaSize double value containing area size in square meters
     * @return bool indicating if area can be monitored
     */
    bool canMonitorArea(double areaSize) const;
};

/**
 * @class Gate
 * @brief Class for boarding gates
 * 
 * Represents boarding gates with capacity management for passengers.
 */
class Gate : public AirlineTool {
private:
    double capacity;     ///< Display capacity in square meters
    bool hasCover;       ///< Whether the gate has a cover
    bool inUse;          ///< Whether the gate is currently in use

public:
    /**
     * @brief Construct a new Gate object
     * 
     * @param n constant pointer to the gate name
     * @param c double value containing capacity in square meters
     * @param hc boolean value indicating if has cover
     * @param u boolean value indicating if in use
     */
    Gate(const char* n = "Gate",
                 double c = 2.0,
                 bool hc = true,
                 bool u = false);

    /**
     * @brief Start boarding at the gate
     * 
     * @throws ToolNotAvailableException if gate is not available
     */
    void startBoarding();

    /**
     * @brief Stop boarding at the gate
     */
    void stopBoarding();

    /**
     * @brief Check if gate can accommodate passengers of given capacity
     * 
     * @param sqMeters double value containing capacity in square meters
     * @return true if capacity is sufficient
     * @return false otherwise
     */
    bool canAccommodate(double sqMeters) const;

    /**
     * @brief Check if gate has cover
     * 
     * @return true if gate has cover
     * @return false otherwise
     */
    bool checkHasCover() const;

    /**
     * @brief Calculate boarding time estimate
     * 
     * @param passengerCount integer value containing number of passengers
     * @return double containing estimated time in minutes
     */
    double calculateBoardingTime(int passengerCount) const;

    /**
     * @brief Check if gate can handle passenger load
     * 
     * @param passengerCount integer value containing number of passengers
     * @return bool indicating if gate can handle load
     */
    bool canHandlePassengerLoad(int passengerCount) const;

    /**
     * @brief Calculate gate utilization percentage
     * 
     * @return double containing utilization percentage
     */
    double calculateUtilization() const;
};

/**
 * @class Timer
 * @brief Class for timing operations
 * 
 * Represents a timer for tracking elapsed time and managing time-based operations.
 */
class Timer {
private:
    int seconds;     ///< Total seconds for the timer
    bool running;    ///< Whether the timer is running
    int elapsed;     ///< Elapsed seconds
    int id;          ///< Unique identifier for the timer

public:
    /**
     * @brief Construct a new Timer object
     * 
     * @param s integer value containing seconds
     * @param r boolean value indicating if running
     * @param e integer value containing elapsed seconds
     * @param i integer value containing timer identifier
     */
    Timer(int s = 0, bool r = false, int e = 0, int i = 0);

    /**
     * @brief Start the timer
     * 
     * @param s integer value containing seconds to set
     * @throws TimerNotSetException if seconds is not positive
     */
    void start(int s);

    /**
     * @brief Advance the timer by delta seconds
     * 
     * @param delta integer value containing seconds to advance
     */
    void tick(int delta);

    /**
     * @brief Check if timer is finished
     * 
     * @return true if timer is finished
     * @return false otherwise
     */
    bool isFinished() const;

    /**
     * @brief Get elapsed seconds
     * 
     * @return int containing elapsed seconds
     */
    int getElapsed() const;

    /**
     * @brief Check if timer is running
     * 
     * @return true if timer is running
     * @return false otherwise
     */
    bool isRunning() const;

    /**
     * @brief Calculate remaining time
     * 
     * @return int containing remaining seconds
     */
    int calculateRemainingTime() const;

    /**
     * @brief Reset timer to zero
     */
    void reset();

    /**
     * @brief Pause the timer
     */
    void pause();

    /**
     * @brief Resume paused timer
     */
    void resume();
};

/**
 * @class MaintenanceKit
 * @brief Class for aircraft maintenance kits
 * 
 * Represents maintenance equipment with equip/unequip functionality.
 */
class MaintenanceKit : public AirlineTool {
private:
    bool equipped;   ///< Whether the maintenance kit is equipped

public:
    /**
     * @brief Construct a new MaintenanceKit object
     * 
     * @param n constant pointer to the kit name
     * @param eq boolean value indicating if equipped
     */
    MaintenanceKit(const char* n = "MaintenanceKit",
                   bool eq = false);

    /**
     * @brief Equip the maintenance kit
     * 
     * @return bool indicating if successfully equipped
     */
    bool equip();

    /**
     * @brief Unequip the maintenance kit
     * 
     * @return bool indicating if successfully unequipped
     */
    bool unequip();

    /**
     * @brief Start maintenance process
     * 
     * @throws ToolNotAvailableException if kit is not available or not equipped
     */
    void maintain();

    /**
     * @brief Check if maintenance kit is equipped
     * 
     * @return true if equipped
     * @return false otherwise
     */
    bool isEquipped() const;

    /**
     * @brief Calculate maintenance efficiency
     * 
     * @return double containing efficiency percentage
     */
    double calculateMaintenanceEfficiency() const;

    /**
     * @brief Check if kit has required tools
     * 
     * @param toolCount integer value containing required tool count
     * @return bool indicating if has required tools
     */
    bool hasRequiredTools(int toolCount) const;
};

/**
 * @class CleaningKit
 * @brief Class for cleaning kits
 * 
 * Represents cleaning equipment for aircraft maintenance.
 */
class CleaningKit : public AirlineTool {
private:
    int id;      ///< Unique identifier for the cleaning kit

public:
    /**
     * @brief Construct a new CleaningKit object
     * 
     * @param n constant pointer to the kit name
     * @param i integer value containing kit identifier
     */
    CleaningKit(const char* n = "CleaningKit",
                int i = 0);

    /**
     * @brief Use the cleaning kit
     * 
     * @throws ToolNotAvailableException if kit is not available
     */
    void clean();

    /**
     * @brief Get the cleaning kit identifier
     * 
     * @return int containing kit identifier
     */
    int getId() const;
};

/**
 * @class ConditionProfile
 * @brief Class for cabinClimate condition profiles
 * 
 * Represents temperature profiles for gradual cabinClimate transitions.
 */
class ConditionProfile {
private:
    double startTemp;      ///< Starting temperature
    double targetTemp;     ///< Target temperature
    int duration;          ///< Duration in seconds
    bool gradual;          ///< Whether transition is gradual

public:
    /**
     * @brief Construct a new ConditionProfile object
     * 
     * @param s double value containing start temperature
     * @param t double value containing target temperature
     * @param d integer value containing duration in seconds
     * @param g boolean value indicating if gradual transition
     */
    ConditionProfile(double s = 20.0, double t = 20.0,
                     int d = 600, bool g = true);

    /**
     * @brief Get current temperature based on elapsed time
     * 
     * @param elapsed integer value containing elapsed seconds
     * @return double containing current temperature
     */
    double currentTemp(int elapsed) const;

    /**
     * @brief Check if target temperature is reached
     * 
     * @param current double value containing current temperature
     * @return true if target is reached
     * @return false otherwise
     */
    bool isReached(double current) const;

    /**
     * @brief Reset the profile with new parameters
     * 
     * @param s double value containing start temperature
     * @param t double value containing target temperature
     * @param d integer value containing duration in seconds
     */
    void reset(double s, double t, int d);

    /**
     * @brief Get the duration of the profile
     * 
     * @return int containing duration in seconds
     */
    int getDuration() const;

    /**
     * @brief Calculate temperature change rate
     * 
     * @return double containing change rate per second
     */
    double calculateTemperatureChangeRate() const;

    /**
     * @brief Check if profile is valid
     * 
     * @return bool indicating if profile is valid
     */
    bool isValidProfile() const;

    /**
     * @brief Get estimated completion time
     * 
     * @param currentElapsed integer value containing current elapsed seconds
     * @return int containing remaining seconds
     */
    int getEstimatedCompletionTime(int currentElapsed) const;
};

/**
 * @class CabinClimateControl
 * @brief Class for cabin climate control systems
 * 
 * Manages temperature, humidity, and door state for passenger comfort.
 */
class CabinClimateControl {
private:
    double temperature;        ///< Current temperature
    bool on;                   ///< Whether cabinClimate control is on
    bool doorClosed;           ///< Whether the door is closed
    Timer controlTimer;        ///< Timer for cabinClimate control
    ConditionProfile profile;  ///< Temperature transition profile
    int elapsedSeconds;        ///< Elapsed seconds since start
    double humidity;           ///< Current humidity level
    double targetHumidity;     ///< Target humidity level
    bool alarmActive;          ///< Whether alarm is active

public:
    /**
     * @brief Construct a new CabinClimateControl object
     * 
     * @param t double value containing initial temperature
     * @param o boolean value indicating if on
     * @param d boolean value indicating if door closed
     */
    CabinClimateControl(double t = 0.0, bool o = false, bool d = true);

    /**
     * @brief Set cabinClimate conditions
     * 
     * @param t double value containing target temperature
     * @param warmupMinutes integer value containing warmup time in minutes
     * @throws InvalidConditionException if temperature or warmup time is invalid or door is open
     */
    void setConditions(double t, int warmupMinutes = 10);

    /**
     * @brief Turn off cabinClimate control
     */
    void turnOff();

    /**
     * @brief Close the door
     */
    void closeDoor();

    /**
     * @brief Open the door
     */
    void openDoor();

    /**
     * @brief Set timer in minutes
     * 
     * @param minutes integer value containing minutes
     * @throws TimerNotSetException if minutes is not positive
     */
    void setTimerMinutes(int minutes);

    /**
     * @brief Advance time by delta seconds
     * 
     * @param secondsDelta integer value containing seconds to advance
     */
    void tick(int secondsDelta);

    /**
     * @brief Check if cabinClimate control is on
     * 
     * @return true if cabinClimate control is on
     * @return false otherwise
     */
    bool isOn() const;

    /**
     * @brief Get the current temperature
     * 
     * @return double containing current temperature
     */
    double getTemperature() const;

    /**
     * @brief Check if door is closed
     * 
     * @return true if door is closed
     * @return false otherwise
     */
    bool isDoorClosed() const;

    /**
     * @brief Set the humidity level
     * 
     * @param h double value containing humidity level
     */
    void setHumidity(double h);

    /**
     * @brief Activate the alarm
     */
    void activateAlarm();

    /**
     * @brief Check if alarm is active
     * 
     * @return true if alarm is active
     * @return false otherwise
     */
    bool isAlarmActive() const;

    /**
     * @brief Get the current humidity level
     * 
     * @return double containing humidity level
     */
    double getHumidity() const;

    /**
     * @brief Get the target humidity level
     * 
     * @return double containing target humidity level
     */
    double getTargetHumidity() const;

    /**
     * @brief Calculate energy consumption
     * 
     * @return double containing energy consumption in kWh
     */
    double calculateEnergyConsumption() const;

    /**
     * @brief Check if climate is optimal for passengers
     * 
     * @return bool indicating if climate is optimal
     */
    bool isOptimalClimate() const;

    /**
     * @brief Adjust temperature gradually
     * 
     * @param targetTemp double value containing target temperature
     * @param duration int value containing duration in minutes
     */
    void adjustTemperatureGradually(double targetTemp, int duration);

    /**
     * @brief Calculate maintenance schedule
     * 
     * @return int containing days until next maintenance
     */
    int calculateMaintenanceSchedule() const;
};

/**
 * @class SecuritySystem
 * @brief Class for security systems
 * 
 * Manages security zones and alarm states for airline protection.
 */
class SecuritySystem {
private:
    int zones;          ///< Total number of security zones
    int activeZones;    ///< Number of currently active zones
    bool alarm;         ///< Whether alarm is enabled
    bool on;            ///< Whether security system is on

public:
    /**
     * @brief Construct a new SecuritySystem object
     * 
     * @param z integer value containing total zones
     * @param act integer value containing active zones
     * @param a boolean value indicating if alarm enabled
     * @param o boolean value indicating if system is on
     */
    SecuritySystem(int z = 4, int act = 0, bool a = true, bool o = false);

    /**
     * @brief Activate a security zone
     */
    void activateZone();

    /**
     * @brief Deactivate a security zone
     */
    void deactivateZone();

    /**
     * @brief Get number of free zones
     * 
     * @return int containing number of free zones
     */
    int freeZones() const;

    /**
     * @brief Check if security system is on
     * 
     * @return true if system is on
     * @return false otherwise
     */
    bool isOn() const;

    /**
     * @brief Activate all security zones
     */
    void activateAllZones();

    /**
     * @brief Deactivate all security zones
     */
    void deactivateAllZones();

    /**
     * @brief Check security breach status
     * 
     * @return bool indicating if breach detected
     */
    bool checkSecurityBreach() const;

    /**
     * @brief Calculate security coverage percentage
     * 
     * @return double containing coverage percentage
     */
    double calculateSecurityCoverage() const;
};

class FlightDispatcher;

/**
 * @class Flight
 * @brief Base class for all flight types
 * 
 * Abstract base class providing common interface for organizing flights.
 */
class Flight {
protected:
    const char* name;   ///< Name of the flight

public:
    /**
     * @brief Construct a new Flight object
     * 
     * @param n constant pointer to the flight name
     */
    Flight(const char* n);

    /**
     * @brief Destroy the Flight object
     */
    virtual ~Flight() {}

    /**
     * @brief Organize the flight (pure virtual)
     */
    virtual void organize() = 0;

    /**
     * @brief Get the flight name
     * 
     * @return const char* containing flight name
     */
    const char* getName() const {
        return name;
    }

    /**
     * @brief Check if flight is fully booked
     * 
     * @return bool indicating if flight is fully booked
     */
    virtual bool isFullyBooked() const;

    /**
     * @brief Calculate flight duration in hours
     * 
     * @return double containing flight duration
     */
    virtual double calculateFlightDuration() const;

    /**
     * @brief Check if flight is on time
     * 
     * @return bool indicating if flight is on time
     */
    virtual bool isOnTime() const;

    /**
     * @brief Get available seats count
     * 
     * @return int containing available seats
     */
    virtual int getAvailableSeats() const;
};

/**
 * @class PassengerFlight
 * @brief Class for passenger flights
 * 
 * Represents a passenger flight with two passengers, seat, cabinLighting, and timer.
 */
/**
 * @class PassengerFlight
 * @brief Class for passenger flights
 * 
 * Represents a passenger flight with two passengers, seat, cabinLighting, and timer.
 */
class PassengerFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* passenger1;          ///< First passenger aircraft
    Aircraft* passenger2;          ///< Second passenger aircraft
    Seat* use_seat;            ///< Seat to use for passengers

public:
    /**
     * @brief Construct a new PassengerFlight object
     * 
     * @param n constant pointer to the flight name
     * @param p1 pointer to the first passenger aircraft
     * @param p2 pointer to the second passenger aircraft
     * @param f pointer to the Seat object
     */
    PassengerFlight(const char* n,
                      Aircraft* p1,
                      Aircraft* p2,
                      Seat* f);

    /**
     * @brief Organize the passenger flight
     */
    void organize() override;
};

/**
 * @class CargoFlight
 * @brief Class for cargo flights
 * 
 * Represents a cargo flight with cargo, display gate, cabinLighting, and seat.
 */
class CargoFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* cargo;       ///< Sculpture aircraft
    Gate* gate;      ///< Display gate for cargo

public:
    /**
     * @brief Construct a new CargoFlight object
     * 
     * @param n constant pointer to the flight name
     * @param s pointer to the cargo aircraft
     * @param st pointer to the Gate object
     */
    CargoFlight(const char* n,
                       Aircraft* s,
                       Gate* st);

    /**
     * @brief Organize the cargo flight
     */
    void organize() override;
};

/**
 * @class CharterFlight
 * @brief Class for chartergraphy flights
 * 
 * Represents a chartergraphy flight with two chartergraphs, seat, cabinLighting, security camera, and timer.
 */
class CharterFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* charter1;              ///< First chartergraph aircraft
    Aircraft* charter2;              ///< Second chartergraph aircraft
    SecurityCamera* camera;       ///< Security camera

public:
    /**
     * @brief Construct a new CharterFlight object
     * 
     * @param n constant pointer to the flight name
     * @param ph1 pointer to the first chartergraph aircraft
     * @param ph2 pointer to the second chartergraph aircraft
     * @param cam pointer to the SecurityCamera object
     */
    CharterFlight(const char* n,
                         Aircraft* ph1,
                         Aircraft* ph2,
                         SecurityCamera* cam);

    /**
     * @brief Organize the chartergraphy flight
     */
    void organize() override;
};

/**
 * @class MixedFlight
 * @brief Class for mixed media flights
 * 
 * Represents a mixed media flight with three aircrafts, display gate, cabinLighting, seat, timer, and maintenance kit.
 */
class MixedFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* aircraft1;              ///< First mixed media aircraft
    Aircraft* aircraft2;             ///< Second mixed media aircraft
    Aircraft* aircraft3;            ///< Third mixed media aircraft
    Gate* gate;          ///< Display gate

public:
    /**
     * @brief Construct a new MixedFlight object
     * 
     * @param n constant pointer to the flight name
     * @param a1 pointer to the first aircraft
     * @param a2 pointer to the second aircraft
     * @param a3 pointer to the third aircraft
     * @param st pointer to the Gate object
     */
    MixedFlight(const char* n,
                        Aircraft* a1,
                        Aircraft* a2,
                        Aircraft* a3,
                        Gate* st);

    /**
     * @brief Organize the mixed media flight
     */
    void organize() override;
};

/**
 * @class BusinessFlight
 * @brief Class for business art flights
 * 
 * Represents a business art flight with two business aircrafts, display gate, cabinLighting, security camera, and timer.
 */
class BusinessFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* business1;             ///< First business aircraft
    Aircraft* business2;           ///< Second business aircraft
    Gate* gate;          ///< Display gate

public:
    /**
     * @brief Construct a new BusinessFlight object
     * 
     * @param n constant pointer to the flight name
     * @param d1 pointer to the first business aircraft
     * @param d2 pointer to the second business aircraft
     * @param st pointer to the Gate object
     */
    BusinessFlight(const char* n,
                         Aircraft* d1,
                         Aircraft* d2,
                         Gate* st);

    /**
     * @brief Organize the business art flight
     */
    void organize() override;
};

/**
 * @class VintageFlight
 * @brief Class for vintage flights
 * 
 * Represents a vintage flight with two vintage aircrafts, seat, cabinClimate control, and maintenance kit.
 */
class VintageFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* vintage1;            ///< First vintage aircraft
    Aircraft* vintage2;           ///< Second vintage aircraft
    CabinClimateControl* cabinClimate;     ///< Climate control system

public:
    /**
     * @brief Construct a new VintageFlight object
     * 
     * @param n constant pointer to the flight name
     * @param v1 pointer to the first vintage aircraft
     * @param v2 pointer to the second vintage aircraft
     * @param cc pointer to the CabinClimateControl object
     */
    VintageFlight(const char* n,
                      Aircraft* v1,
                      Aircraft* v2,
                      CabinClimateControl* cc);

    /**
     * @brief Organize the vintage flight
     */
    void organize() override;
};

/**
 * @class ModernFlight
 * @brief Class for modern flights
 * 
 * Represents a modern flight with two modern aircrafts, display gate, cabinLighting, security camera, and timer.
 */
class ModernFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* modern1;       ///< First modern aircraft
    Aircraft* modern2;      ///< Second modern aircraft
    Gate* gate;          ///< Display gate

public:
    /**
     * @brief Construct a new ModernFlight object
     * 
     * @param n constant pointer to the flight name
     * @param c1 pointer to the first modern aircraft
     * @param c2 pointer to the second modern aircraft
     * @param st pointer to the Gate object
     */
    ModernFlight(const char* n,
                           Aircraft* c1,
                           Aircraft* c2,
                           Gate* st);

    /**
     * @brief Organize the modern flight
     */
    void organize() override;
};

/**
 * @class EconomyFlight
 * @brief Class for economy flights
 * 
 * Represents a economy flight with one economy aircraft, seat, and cabinLighting.
 */
class EconomyFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* economy;      ///< Minimalist aircraft
    Seat* seat;            ///< Seat for display

public:
    /**
     * @brief Construct a new EconomyFlight object
     * 
     * @param n constant pointer to the flight name
     * @param m pointer to the economy aircraft
     * @param f pointer to the Seat object
     */
    EconomyFlight(const char* n,
                         Aircraft* m,
                         Seat* f);

    /**
     * @brief Organize the economy flight
     */
    void organize() override;
};

/**
 * @class InternationalFlight
 * @brief Class for international art flights
 * 
 * Represents an international art flight with two international aircrafts, display gate, cabinLighting, seat, and timer.
 */
class InternationalFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* international1;        ///< First international aircraft
    Aircraft* international2;       ///< Second international aircraft
    Gate* gate;      ///< Display gate

public:
    /**
     * @brief Construct a new InternationalFlight object
     * 
     * @param n constant pointer to the flight name
     * @param a1 pointer to the first international aircraft
     * @param a2 pointer to the second international aircraft
     * @param st pointer to the Gate object
     */
    InternationalFlight(const char* n,
                       Aircraft* a1,
                       Aircraft* a2,
                       Gate* st);

    /**
     * @brief Organize the international flight
     */
    void organize() override;
};

/**
 * @class DomesticFlight
 * @brief Class for domestic flights
 * 
 * Represents a domestic flight with two domestic aircrafts, seat, cabinLighting, and security camera.
 */
class DomesticFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* domestic1;        ///< First domestic aircraft
    Aircraft* domestic2;        ///< Second domestic aircraft
    SecurityCamera* camera;    ///< Security camera

public:
    /**
     * @brief Construct a new DomesticFlight object
     * 
     * @param n constant pointer to the flight name
     * @param p1 pointer to the first domestic aircraft
     * @param p2 pointer to the second domestic aircraft
     * @param cam pointer to the SecurityCamera object
     */
    DomesticFlight(const char* n,
                       Aircraft* p1,
                       Aircraft* p2,
                       SecurityCamera* cam);

    /**
     * @brief Organize the domestic flight
     */
    void organize() override;
};

/**
 * @class LongHaulFlight
 * @brief Class for longHaul flights
 * 
 * Represents a longHaul flight with two longHaul aircrafts, seat, cabinLighting, and timer.
 */
class LongHaulFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* longHaul1;        ///< First longHaul aircraft
    Aircraft* longHaul2;        ///< Second longHaul aircraft
    Seat* seat;              ///< Seat for display

public:
    /**
     * @brief Construct a new LongHaulFlight object
     * 
     * @param n constant pointer to the flight name
     * @param l1 pointer to the first longHaul aircraft
     * @param l2 pointer to the second longHaul aircraft
     * @param f pointer to the Seat object
     */
    LongHaulFlight(const char* n,
                       Aircraft* l1,
                       Aircraft* l2,
                       Seat* f);

    /**
     * @brief Organize the longHaul flight
     */
    void organize() override;
};

/**
 * @class MaintenanceFlight
 * @brief Class for maintenance flights
 * 
 * Represents a maintenance flight with aircraft, maintenance kit, cleaning kit, cabinClimate control, and timer.
 */
class MaintenanceFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* aircraft;           ///< Aircraft to maintain
    MaintenanceKit* maintenanceKit; ///< Restoration kit

public:
    /**
     * @brief Construct a new MaintenanceFlight object
     * 
     * @param n constant pointer to the flight name
     * @param a pointer to the aircraft to maintain
     * @param rk pointer to the MaintenanceKit object
     */
    MaintenanceFlight(const char* n,
                           Aircraft* a,
                           MaintenanceKit* rk);

    /**
     * @brief Organize the maintenance flight
     */
    void organize() override;
};

/**
 * @class SeasonalFlight
 * @brief Class for seasonalorary flights
 * 
 * Represents a seasonalorary flight with two seasonalorary aircrafts, display gate, cabinLighting, security camera, and timer.
 */
class SeasonalFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* seasonal1;             ///< First seasonalorary aircraft
    Aircraft* seasonal2;            ///< Second seasonalorary aircraft
    Gate* gate;       ///< Display gate

public:
    /**
     * @brief Construct a new SeasonalFlight object
     * 
     * @param n constant pointer to the flight name
     * @param t1 pointer to the first seasonalorary aircraft
     * @param t2 pointer to the second seasonalorary aircraft
     * @param st pointer to the Gate object
     */
    SeasonalFlight(const char* n,
                        Aircraft* t1,
                        Aircraft* t2,
                        Gate* st);

    /**
     * @brief Organize the seasonalorary flight
     */
    void organize() override;
};

/**
 * @class RegularFlight
 * @brief Class for regular flights
 * 
 * Represents a regular flight with two regular aircrafts, seat, cabinClimate control, security system, and timer.
 */
class RegularFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* regular1;        ///< First regular aircraft
    Aircraft* regular2;       ///< Second regular aircraft
    SecuritySystem* security;   ///< Security system

public:
    /**
     * @brief Construct a new RegularFlight object
     * 
     * @param n constant pointer to the flight name
     * @param p1 pointer to the first regular aircraft
     * @param p2 pointer to the second regular aircraft
     * @param sec pointer to the SecuritySystem object
     */
    RegularFlight(const char* n,
                       Aircraft* p1,
                       Aircraft* p2,
                       SecuritySystem* sec);

    /**
     * @brief Organize the regular flight
     */
    void organize() override;
};

/**
 * @class InteractiveFlight
 * @brief Class for interactive flights
 * 
 * Represents an interactive flight with two interactive aircrafts, display gate, cabinLighting, security camera, and timer.
 */
class InteractiveFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* interactive1;      ///< First interactive aircraft
    Aircraft* interactive2;     ///< Second interactive aircraft
    SecurityCamera* camera;     ///< Security camera

public:
    /**
     * @brief Construct a new InteractiveFlight object
     * 
     * @param n constant pointer to the flight name
     * @param i1 pointer to the first interactive aircraft
     * @param i2 pointer to the second interactive aircraft
     * @param cam pointer to the SecurityCamera object
     */
    InteractiveFlight(const char* n,
                         Aircraft* i1,
                         Aircraft* i2,
                         SecurityCamera* cam);

    /**
     * @brief Organize the interactive flight
     */
    void organize() override;
};

/**
 * @class ThematicFlight
 * @brief Class for thematic flights
 * 
 * Represents a thematic flight with three thematic aircrafts, seat, display gate, cabinLighting, and timer.
 */
class ThematicFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* theme1;            ///< First thematic aircraft
    Aircraft* theme2;           ///< Second thematic aircraft
    Aircraft* theme3;           ///< Third thematic aircraft
    Gate* gate;       ///< Display gate

public:
    /**
     * @brief Construct a new ThematicFlight object
     * 
     * @param n constant pointer to the flight name
     * @param th1 pointer to the first thematic aircraft
     * @param th2 pointer to the second thematic aircraft
     * @param th3 pointer to the third thematic aircraft
     * @param st pointer to the Gate object
     */
    ThematicFlight(const char* n,
                      Aircraft* th1,
                      Aircraft* th2,
                      Aircraft* th3,
                      Gate* st);

    /**
     * @brief Organize the thematic flight
     */
    void organize() override;
};

/**
 * @class RetrospectiveFlight
 * @brief Class for retrospective flights
 * 
 * Represents a retrospective flight with two retrospective aircrafts, seat, cabinClimate control, maintenance kit, and timer.
 */
class RetrospectiveFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* retro1;            ///< First retrospective aircraft
    Aircraft* retro2;           ///< Second retrospective aircraft
    CabinClimateControl* cabinClimate;    ///< Climate control system

public:
    /**
     * @brief Construct a new RetrospectiveFlight object
     * 
     * @param n constant pointer to the flight name
     * @param r1 pointer to the first retrospective aircraft
     * @param r2 pointer to the second retrospective aircraft
     * @param cc pointer to the CabinClimateControl object
     */
    RetrospectiveFlight(const char* n,
                            Aircraft* r1,
                            Aircraft* r2,
                            CabinClimateControl* cc);

    /**
     * @brief Organize the retrospective flight
     */
    void organize() override;
};

/**
 * @class GroupFlight
 * @brief Class for group flights
 * 
 * Represents a group flight with three group aircrafts, display gate, cabinLighting, seat, security camera, and timer.
 */
class GroupFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* group1;            ///< First group aircraft
    Aircraft* group2;            ///< Second group aircraft
    Aircraft* group3;            ///< Third group aircraft
    Seat* seat;               ///< Seat for display

public:
    /**
     * @brief Construct a new GroupFlight object
     * 
     * @param n constant pointer to the flight name
     * @param g1 pointer to the first group aircraft
     * @param g2 pointer to the second group aircraft
     * @param g3 pointer to the third group aircraft
     * @param f pointer to the Seat object
     */
    GroupFlight(const char* n,
                   Aircraft* g1,
                   Aircraft* g2,
                   Aircraft* g3,
                   Seat* f);

    /**
     * @brief Organize the group flight
     */
    void organize() override;
};

/**
 * @class SoloFlight
 * @brief Class for solo flights
 * 
 * Represents a solo flight with two solo aircrafts, seat, cabinLighting, display gate, and timer.
 */
class SoloFlight : public Flight {
    friend class FlightDispatcher;
private:
    Aircraft* solo1;             ///< First solo aircraft
    Aircraft* solo2;             ///< Second solo aircraft

public:
    /**
     * @brief Construct a new SoloFlight object
     * 
     * @param n constant pointer to the flight name
     * @param s1 pointer to the first solo aircraft
     * @param s2 pointer to the second solo aircraft
     */
    SoloFlight(const char* n,
                   Aircraft* s1,
                   Aircraft* s2);

    /**
     * @brief Organize the solo flight
     */
    void organize() override;
};

/**
 * @class FlightDispatcher
 * @brief Class for airline flightDispatchers
 * 
 * Manages organization of all types of flights in the airline.
 */
class FlightDispatcher {
private:
    const char* name;    ///< Name of the flightDispatcher

public:
    /**
     * @brief Construct a new FlightDispatcher object
     * 
     * @param n constant pointer to the flightDispatcher name
     */
    FlightDispatcher(const char* n = "FlightDispatcher");

    /**
     * @brief Organize any flight using polymorphism
     * 
     * @param flight pointer to the Flight object
     */
    void organizeFlight(Flight* flight);
};

/**
 * @class Passenger
 * @brief Class for airline passengers
 * 
 * Represents a passenger with access level, ticket status, and visit tracking.
 */
class Passenger {
private:
    const char* name;        ///< Name of the passenger
    int accessLevel;          ///< Access level of the passenger
    bool hasTicket;          ///< Whether the passenger has a ticket
    double visitDuration;    ///< Duration of the visit in minutes
    int favoriteCount;       ///< Number of favorite aircrafts
    bool guidedTour;         ///< Whether the passenger is on a guided tour

public:
    /**
     * @brief Construct a new Passenger object
     * 
     * @param n constant pointer to the passenger name
     * @param al integer value containing access level
     * @param ht boolean value indicating if has ticket
     */
    Passenger(const char* n = "Passenger", int al = 1, bool ht = false);

    /**
     * @brief Purchase a ticket
     */
    void purchaseTicket();

    /**
     * @brief Enter the airline
     * 
     * @throws InvalidAccessException if passenger does not have a ticket
     */
    void enterAirline();

    /**
     * @brief View an aircraft
     * 
     * @param aircraft pointer to the Aircraft object to view
     * @throws AircraftNotFoundException if aircraft is null
     */
    void viewAircraft(Aircraft* aircraft);

    /**
     * @brief Add an aircraft to favorites
     */
    void addFavorite();

    /**
     * @brief Join a guided tour
     */
    void joinGuidedTour();

    /**
     * @brief Check if passenger can access restricted areas
     * 
     * @return true if access level is 3 or higher and has ticket
     * @return false otherwise
     */
    bool canAccessRestricted() const;

    /**
     * @brief Get the access level
     * 
     * @return int containing access level
     */
    int getAccessLevel() const;

    /**
     * @brief Get the passenger name
     * 
     * @return const char* containing passenger name
     */
    const char* getName() const;

    /**
     * @brief Get the visit duration
     * 
     * @return double containing visit duration in minutes
     */
    double getVisitDuration() const;

    /**
     * @brief Calculate total baggage weight
     * 
     * @param checkedWeight double value containing checked baggage weight
     * @param carryOnWeight double value containing carry-on weight
     * @return double containing total weight
     */
    double calculateTotalBaggageWeight(double checkedWeight, double carryOnWeight) const;

    /**
     * @brief Check if passenger has valid visa
     * 
     * @param destinationCountry constant pointer to destination country
     * @return bool indicating if visa is valid
     */
    bool hasValidVisa(const char* destinationCountry) const;

    /**
     * @brief Calculate ticket discount based on loyalty status
     * 
     * @param basePrice double value containing base ticket price
     * @return double containing discounted price
     */
    double calculateLoyaltyDiscount(double basePrice) const;

    /**
     * @brief Request special meal
     * 
     * @param mealType constant pointer to meal type
     * @return bool indicating if request was successful
     */
    bool requestSpecialMeal(const char* mealType);

    /**
     * @brief Check in for flight
     * 
     * @param flightNumber constant pointer to flight number
     * @return bool indicating if check-in was successful
     */
    bool checkInForFlight(const char* flightNumber);

    /**
     * @brief Cancel flight reservation
     * 
     * @param reservationId integer value containing reservation ID
     * @return bool indicating if cancellation was successful
     */
    bool cancelReservation(int reservationId);

    /**
     * @brief Calculate total travel cost
     * 
     * @param ticketPrice double value containing ticket price
     * @param baggageFee double value containing baggage fee
     * @param mealFee double value containing meal fee
     * @return double containing total cost
     */
    double calculateTotalTravelCost(double ticketPrice, double baggageFee, double mealFee) const;
};

/**
 * @class AirlineMenu
 * @brief Class for airline menu system
 * 
 * Manages flights and provides interactive menu for passengers.
 */
class AirlineMenu {
private:
    static const int MAX_FLIGHTS = 50;   ///< Maximum number of flights
    Flight* flights[MAX_FLIGHTS]; ///< Array of flight pointers
    int flightCount;                      ///< Current number of flights
    Passenger* currentPassenger;                  ///< Current passenger

public:
    /**
     * @brief Construct a new AirlineMenu object
     */
    AirlineMenu();

    /**
     * @brief Show the menu
     */
    void show() const;

    /**
     * @brief Add an flight to the menu
     * 
     * @param e pointer to the Flight object to add
     */
    void addFlight(Flight* e);

    /**
     * @brief Set the current passenger
     * 
     * @param v pointer to the Passenger object
     */
    void setPassenger(Passenger* v);

    /**
     * @brief Run the menu system
     */
    void run();

    /**
     * @brief Get the number of flights in the menu
     * 
     * @return int containing number of flights
     */
    int getFlightCount() const;

    /**
     * @brief Get the current passenger
     * 
     * @return Passenger* pointer to current passenger or nullptr
     */
    Passenger* getCurrentPassenger() const;

    /**
     * @brief Search flights by name
     * 
     * @param searchTerm constant pointer to search term
     * @return int containing number of matching flights
     */
    int searchFlights(const char* searchTerm) const;

    /**
     * @brief Filter flights by availability
     * 
     * @return int containing number of available flights
     */
    int filterAvailableFlights() const;

    /**
     * @brief Sort flights by name
     */
    void sortFlightsByName();

    /**
     * @brief Get flight by index
     * 
     * @param index integer value containing flight index
     * @return Flight* pointer to flight or nullptr
     */
    Flight* getFlightByIndex(int index) const;
};

/**
 * @class BookingSystem
 * @brief Class for managing flight bookings and reservations
 * 
 * Handles booking operations, payment processing, and reservation management.
 */
class BookingSystem {
private:
    const char* systemName;        ///< Name of the booking system
    int totalBookings;            ///< Total number of bookings
    double totalRevenue;          ///< Total revenue from bookings
    bool isActive;                ///< Whether the system is active
    int maxBookings;              ///< Maximum number of bookings allowed
    Passenger* currentBookingPassenger;  ///< Current passenger making booking
    Flight* currentBookingFlight;       ///< Current flight being booked

public:
    /**
     * @brief Construct a new BookingSystem object
     * 
     * @param name constant pointer to system name
     * @param max integer value containing maximum bookings
     */
    BookingSystem(const char* name = "BookingSystem", int max = 1000);

    /**
     * @brief Create a new booking
     * 
     * @param passenger pointer to Passenger object
     * @param flight pointer to Flight object
     * @return bool indicating if booking was successful
     */
    bool createBooking(Passenger* passenger, Flight* flight);

    /**
     * @brief Cancel an existing booking
     * 
     * @param bookingId integer value containing booking ID
     * @return bool indicating if cancellation was successful
     */
    bool cancelBooking(int bookingId);

    /**
     * @brief Calculate ticket price for a flight
     * 
     * @param flight pointer to Flight object
     * @param passenger pointer to Passenger object
     * @return double containing calculated price
     */
    double calculateTicketPrice(Flight* flight, Passenger* passenger);

    /**
     * @brief Process payment for booking
     * 
     * @param amount double value containing payment amount
     * @param cardNumber constant pointer to card number
     * @return bool indicating if payment was successful
     */
    bool processPayment(double amount, const char* cardNumber);

    /**
     * @brief Transfer money from one card to another
     * 
     * @param fromCard constant pointer to source card number
     * @param toCard constant pointer to destination card number
     * @param amount double value containing amount to transfer
     * @return bool indicating if transfer was successful
     */
    bool transferMoney(const char* fromCard, const char* toCard, double amount);

    /**
     * @brief Verify password for account
     * 
     * @param accountId constant pointer to account ID
     * @param password constant pointer to password
     * @return bool indicating if password is correct
     */
    bool verifyPassword(const char* accountId, const char* password);

    /**
     * @brief Check if flight is available for booking
     * 
     * @param flight pointer to Flight object
     * @return bool indicating if flight is available
     */
    bool checkFlightAvailability(Flight* flight);

    /**
     * @brief Reserve a seat for passenger
     * 
     * @param passenger pointer to Passenger object
     * @param seatNumber integer value containing seat number
     * @return bool indicating if reservation was successful
     */
    bool reserveSeat(Passenger* passenger, int seatNumber);

    /**
     * @brief Cancel seat reservation
     * 
     * @param seatNumber integer value containing seat number
     * @return bool indicating if cancellation was successful
     */
    bool cancelSeatReservation(int seatNumber);

    /**
     * @brief Calculate baggage fee
     * 
     * @param weight double value containing baggage weight in kg
     * @return double containing calculated fee
     */
    double calculateBaggageFee(double weight);

    /**
     * @brief Check visa requirements for international flight
     * 
     * @param passenger pointer to Passenger object
     * @param flight pointer to Flight object
     * @return bool indicating if visa is required
     */
    bool checkVisaRequirement(Passenger* passenger, Flight* flight);

    /**
     * @brief Get total revenue
     * 
     * @return double containing total revenue
     */
    double getTotalRevenue() const;

    /**
     * @brief Get total bookings count
     * 
     * @return int containing total bookings
     */
    int getTotalBookings() const;

    /**
     * @brief Check if system is active
     * 
     * @return bool indicating if system is active
     */
    bool isSystemActive() const;
};