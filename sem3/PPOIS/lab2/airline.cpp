#include "airline.hpp"
#include <cstring>
#include <cmath>

Dimension::Dimension(const char* n, double c, bool m, int i)
    : name(n), cmPerUnit(c), metric(m), id(i), precision(0.1), gateard(true) {}
double Dimension::toCentimeters(double amount) const {
    return amount * cmPerUnit;
}
bool Dimension::isMetric() const {
    return metric;
}
int Dimension::getId() const {
    return id;
}
void Dimension::setPrecision(double p) {
    precision = p;
}
bool Dimension::isStandard() const {
    return gateard;
}
double Dimension::fromCentimeters(double cm) const {
    if (cmPerUnit <= 0.0) return 0.0;
    return cm / cmPerUnit;
}
Size::Size(double v, Dimension* d, bool appr, int i)
    : value(v), dimension(d), approximate(appr), id(i) {}
double Size::toCentimeters() const {
    if (!dimension) {
        throw StorageException("Dimension is not set for size");
    }
    return dimension->toCentimeters(value);
}
void Size::scale(double factor) {
    value *= factor;
}
bool Size::isZero() const {
    return value <= 0.0;
}
double Size::getValue() const {
    return value;
}
bool Size::isApproximate() const {
    return approximate;
}
Aircraft::Aircraft(const char* n, const Size& s, double v, bool fr)
    : name(n), size(s), value(v), fragile(fr), year(0), manufacturer("Unknown"), certified(false), insuranceValue(0.0) {}
void Aircraft::addSize(double v) {
    double oldCm = size.toCentimeters();
    double newCm = oldCm + v;
    if (oldCm > 0.0) {
        double factor = newCm / oldCm;
        size.scale(factor);
    }
}
void Aircraft::useSize(double vCm) {
    double cm = size.toCentimeters();
    if (vCm > cm) {
        throw NotEnoughAircraftException("Not enough aircraft size");
    }
    if (cm > 0.0) {
        double factor = (cm - vCm) / cm;
        size.scale(factor);
    }
}
bool Aircraft::isFragile() const {
    return fragile;
}
void Aircraft::certify() {
    certified = true;
}
void Aircraft::setInsuranceValue(double val) {
    insuranceValue = val;
}
int Aircraft::getYear() const {
    return year;
}
const char* Aircraft::getManufacturer() const {
    return manufacturer;
}
const char* Aircraft::getName() const {
    return name;
}
double Aircraft::getValue() const {
    return value;
}
bool Aircraft::isCertified() const {
    return certified;
}
AirlineTool::AirlineTool(const char* n, bool c, bool a, int d)
    : name(n), clean(c), available(a), busy(false), durability(d) {}
void AirlineTool::useTool() {
    if (!available || !clean || durability <= 0) {
        throw ToolNotAvailableException("Tool not usable (unavailable, dirty, or broken)");
    }
    busy = true;
    durability--;
    if (durability <= 0) {
        durability = 0;
        available = false;
    }
    busy = false;
}
void AirlineTool::cleanTool() {
    clean = true;
}
void AirlineTool::breakTool() {
    available = false;
    durability = 0;
}
bool AirlineTool::isAvailable() const {
    return available && clean && durability > 0;
}
const char* AirlineTool::getName() const {
    return name;
}
Seat::Seat(const char* n, bool p, int w, int i)
    : AirlineTool(n, true, true, 100),
      protective(p), width(w), id(i) {}
void Seat::addProtection() {
    protective = true;
}
void Seat::removeProtection() {
    protective = false;
}
bool Seat::canProtect() const {
    return isAvailable() && protective;
}
int Seat::getWidth() const {
    return width;
}
CabinLighting::CabinLighting(const char* n, bool l, bool d, int i)
    : AirlineTool(n, true, true, 100),
      led(l), dimmed(d), id(i) {}
void CabinLighting::dim() {
    dimmed = true;
}
void CabinLighting::brighten() {
    dimmed = false;
}
bool CabinLighting::isSafeForCabin() const {
    return led && !dimmed && isAvailable();
}
bool CabinLighting::isLED() const {
    return led;
}
SecurityCamera::SecurityCamera(const char* n, double a, bool r, bool act)
    : AirlineTool(n, true, true, 100),
      angle(a), recording(r), active(act) {}
void SecurityCamera::startRecording() {
    if (!isAvailable()) {
        throw ToolNotAvailableException("Camera not available");
    }
    useTool();
    recording = true;
    active = true;
}
void SecurityCamera::stopRecording() {
    recording = false;
    active = false;
}
bool SecurityCamera::isRecording() const {
    return recording;
}
double SecurityCamera::getAngle() const {
    return angle;
}
Gate::Gate(const char* n, double c, bool hc, bool u)
    : AirlineTool(n, true, true, 100),
      capacity(c), hasCover(hc), inUse(u) {}
void Gate::startBoarding() {
    if (!isAvailable()) {
        throw ToolNotAvailableException("Display gate not available");
    }
    useTool();
    inUse = true;
}
void Gate::stopBoarding() {
    inUse = false;
}
bool Gate::canAccommodate(double sqMeters) const {
    return sqMeters <= capacity;
}
bool Gate::checkHasCover() const {
    return hasCover;
}
Timer::Timer(int s, bool r, int e, int i)
    : seconds(s), running(r), elapsed(e), id(i) {}
void Timer::start(int s) {
    if (s <= 0) {
        throw TimerNotSetException("Timer seconds must be > 0");
    }
    seconds = s;
    elapsed = 0;
    running = true;
}
void Timer::tick(int delta) {
    if (delta <= 0) return;
    if (!running) return;
    elapsed += delta;
    if (elapsed >= seconds) {
        elapsed = seconds;
        running = false;
    }
}
bool Timer::isFinished() const {
    return !running && elapsed >= seconds && seconds > 0;
}
int Timer::getElapsed() const {
    return elapsed;
}
bool Timer::isRunning() const {
    return running;
}
MaintenanceKit::MaintenanceKit(const char* n, bool eq)
    : AirlineTool(n, true, true, 100),
      equipped(eq) {}
bool MaintenanceKit::equip() {
    equipped = true;
    cout << "Maintenance kit equipped.\n";
    return equipped;
}
bool MaintenanceKit::unequip() {
    equipped = false;
    cout << "Maintenance kit unequipped.\n";
    return equipped;
}
void MaintenanceKit::maintain() {
    if (!equipped) {
        cout << "Maintenance kit is not equipped. Cannot start maintenance.\n";
        return;
    }
    if (!isAvailable()) {
        throw ToolNotAvailableException("Maintenance kit is not available");
    }
    useTool();
    cout << "Starting maintenance process...\n";
    cout << "Cleaning and repairing aircraft...\n";
    cout << "Maintenance process completed.\n";
}
bool MaintenanceKit::isEquipped() const {
    return equipped;
}
CleaningKit::CleaningKit(const char* n, int i)
    : AirlineTool(n, true, true, 100),
      id(i) {}
void CleaningKit::clean() {
    if (!isAvailable()) {
        throw ToolNotAvailableException("Cleaning kit is not available");
    }
    useTool();
    cout << "Using cleaning kit... clean-clean-clean...\n";
}
int CleaningKit::getId() const {
    return id;
}
ConditionProfile::ConditionProfile(double s, double t, int d, bool g)
    : startTemp(s), targetTemp(t), duration(d), gradual(g) {}
double ConditionProfile::currentTemp(int elapsed) const {
    if (!gradual || elapsed >= duration || duration <= 0) {
        return targetTemp;
    }
    double ratio = (double)elapsed / duration;
    return startTemp + (targetTemp - startTemp) * ratio;
}
bool ConditionProfile::isReached(double current) const {
    return current >= targetTemp;
}
void ConditionProfile::reset(double s, double t, int d) {
    startTemp = s;
    targetTemp = t;
    duration = d;
}
int ConditionProfile::getDuration() const {
    return duration;
}
CabinClimateControl::CabinClimateControl(double t, bool o, bool d)
    : temperature(t),
      on(o),
      doorClosed(d),
      controlTimer(),
      profile(),
      elapsedSeconds(0),
      humidity(50.0),
      targetHumidity(50.0),
      alarmActive(false) {}
void CabinClimateControl::setConditions(double t, int warmupMinutes) {
    if (t <= 0.0 || t > 30.0) {
        throw InvalidConditionException("Invalid cabinClimate temperature");
    }
    if (!doorClosed) {
        throw InvalidConditionException("Climate control door is open");
    }
    if (warmupMinutes <= 0) {
        throw InvalidConditionException("Warmup minutes must be > 0");
    }
    profile.reset(temperature, t, warmupMinutes * 60);
    elapsedSeconds = 0;
    on = true;
}
void CabinClimateControl::turnOff() {
    on = false;
    temperature = 0.0;
}
void CabinClimateControl::closeDoor() {
    doorClosed = true;
}
void CabinClimateControl::openDoor() {
    doorClosed = false;
}
void CabinClimateControl::setTimerMinutes(int minutes) {
    if (minutes <= 0) {
        throw TimerNotSetException("Timer minutes must be > 0");
    }
    controlTimer.start(minutes * 60);
}
void CabinClimateControl::tick(int secondsDelta) {
    if (secondsDelta <= 0) return;
    if (on) {
        elapsedSeconds += secondsDelta;
        temperature = profile.currentTemp(elapsedSeconds);
    }
    controlTimer.tick(secondsDelta);
    if (controlTimer.isFinished() && on) {
        turnOff();
    }
}
bool CabinClimateControl::isOn() const {
    return on;
}
double CabinClimateControl::getTemperature() const {
    return temperature;
}
bool CabinClimateControl::isDoorClosed() const {
    return doorClosed;
}
void CabinClimateControl::setHumidity(double h) {
    humidity = h;
}
void CabinClimateControl::activateAlarm() {
    alarmActive = true;
}
bool CabinClimateControl::isAlarmActive() const {
    return alarmActive;
}
double CabinClimateControl::getHumidity() const {
    return humidity;
}
double CabinClimateControl::getTargetHumidity() const {
    return targetHumidity;
}
SecuritySystem::SecuritySystem(int z, int act, bool a, bool o)
    : zones(z), activeZones(act), alarm(a), on(o) {}
void SecuritySystem::activateZone() {
    if (activeZones < zones) {
        activeZones++;
        on = true;
    }
}
void SecuritySystem::deactivateZone() {
    if (activeZones > 0) {
        activeZones--;
        if (activeZones == 0) {
            on = false;
        }
    }
}
int SecuritySystem::freeZones() const {
    return zones - activeZones;
}
bool SecuritySystem::isOn() const {
    return on;
}
Flight::Flight(const char* n) : name(n) {}
PassengerFlight::PassengerFlight(const char* n,
                                       Aircraft* p1,
                                       Aircraft* p2,
                                       Seat* f)
    : Flight(n),
      passenger1(p1), passenger2(p2),
      use_seat(f) {}
void PassengerFlight::organize() {
    if (!use_seat) throw ToolNotAvailableException("No seat for passenger flight");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing passengers for boarding...\n";
    if (passenger1) passenger1->useSize(50.0);
    if (passenger2) passenger2->useSize(50.0);
    cout << "Seating passengers...\n";
    use_seat->useTool();
    cout << "Passenger flight organized successfully!\n";
}
CargoFlight::CargoFlight(const char* n,
                                          Aircraft* s,
                                          Gate* st)
    : Flight(n), cargo(s), gate(st) {}
void CargoFlight::organize() {
    if (!gate) {
        throw ToolNotAvailableException("No gate");
    }
    if (!gate->canAccommodate(1.5)) {
        throw InsufficientSpaceException("Display gate too small for cargo");
    }
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing cargo for loading...\n";
    if (cargo) cargo->useSize(100.0);
    cout << "Loading cargo at gate...\n";
    gate->startBoarding();
    cout << "Cargo flight organized successfully!\n";
}
CharterFlight::CharterFlight(const char* n,
                                             Aircraft* ph1,
                                             Aircraft* ph2,
                                             SecurityCamera* cam)
    : Flight(n), charter1(ph1), charter2(ph2), camera(cam) {}
void CharterFlight::organize() {
    if (!camera) {
        throw ToolNotAvailableException("No security camera for charter flight");
    }
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing charter aircraft for boarding...\n";
    if (charter1) charter1->useSize(30.0);
    if (charter2) charter2->useSize(30.0);
    camera->startRecording();
    cout << "Charter flight organized successfully!\n";
}
MixedFlight::MixedFlight(const char* n,
                                           Aircraft* a1,
                                           Aircraft* a2,
                                           Aircraft* a3,
                                           Gate* st)
    : Flight(n), aircraft1(a1), aircraft2(a2), aircraft3(a3),
      gate(st) {}
void MixedFlight::organize() {
    if (!gate) throw ToolNotAvailableException("No gate");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing mixed aircraft...\n";
    if (aircraft1) aircraft1->useSize(40.0);
    if (aircraft2) aircraft2->useSize(40.0);
    if (aircraft3) aircraft3->useSize(40.0);
    gate->startBoarding();
    cout << "Mixed flight organized successfully!\n";
}
BusinessFlight::BusinessFlight(const char* n,
                                           Aircraft* d1,
                                           Aircraft* d2,
                                           Gate* st)
    : Flight(n), business1(d1), business2(d2),
      gate(st) {}
void BusinessFlight::organize() {
    if (!gate) throw ToolNotAvailableException("No gate");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing business aircraft...\n";
    if (business1) business1->useSize(60.0);
    if (business2) business2->useSize(60.0);
    gate->startBoarding();
    cout << "Business flight organized successfully!\n";
}
VintageFlight::VintageFlight(const char* n,
                                      Aircraft* v1,
                                      Aircraft* v2,
                                      CabinClimateControl* cc)
    : Flight(n), vintage1(v1), vintage2(v2),
      cabinClimate(cc) {}
void VintageFlight::organize() {
    if (!cabinClimate) throw ToolNotAvailableException("No climate control");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing vintage aircraft...\n";
    if (vintage1) vintage1->useSize(45.0);
    if (vintage2) vintage2->useSize(45.0);
    cabinClimate->setConditions(22.0, 15);
    cout << "Vintage flight organized successfully!\n";
}
ModernFlight::ModernFlight(const char* n,
                                                Aircraft* c1,
                                                Aircraft* c2,
                                                Gate* st)
    : Flight(n), modern1(c1), modern2(c2),
      gate(st) {}
void ModernFlight::organize() {
    if (!gate) throw ToolNotAvailableException("No gate");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing modern aircraft...\n";
    if (modern1) modern1->useSize(55.0);
    if (modern2) modern2->useSize(55.0);
    gate->startBoarding();
    cout << "Modern flight organized successfully!\n";
}
EconomyFlight::EconomyFlight(const char* n,
                                            Aircraft* m,
                                            Seat* f)
    : Flight(n), economy(m), seat(f) {}
void EconomyFlight::organize() {
    if (!seat) throw ToolNotAvailableException("No seat");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing economy aircraft...\n";
    if (economy) economy->useSize(35.0);
    seat->useTool();
    cout << "Economy flight organized successfully!\n";
}
InternationalFlight::InternationalFlight(const char* n,
                                       Aircraft* a1,
                                       Aircraft* a2,
                                       Gate* st)
    : Flight(n), international1(a1), international2(a2),
      gate(st) {}
void InternationalFlight::organize() {
    if (!gate) throw ToolNotAvailableException("No gate");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing international aircraft...\n";
    if (international1) international1->useSize(65.0);
    if (international2) international2->useSize(65.0);
    gate->startBoarding();
    cout << "International flight organized successfully!\n";
}
DomesticFlight::DomesticFlight(const char* n,
                                       Aircraft* p1,
                                       Aircraft* p2,
                                       SecurityCamera* cam)
    : Flight(n), domestic1(p1), domestic2(p2),
      camera(cam) {}
void DomesticFlight::organize() {
    if (!camera) throw ToolNotAvailableException("No security camera");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing domestic aircraft...\n";
    if (domestic1) domestic1->useSize(50.0);
    if (domestic2) domestic2->useSize(50.0);
    camera->startRecording();
    cout << "Domestic flight organized successfully!\n";
}
LongHaulFlight::LongHaulFlight(const char* n,
                                         Aircraft* l1,
                                         Aircraft* l2,
                                         Seat* f)
    : Flight(n), longHaul1(l1), longHaul2(l2),
      seat(f) {}
void LongHaulFlight::organize() {
    if (!seat) throw ToolNotAvailableException("No seat");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing long haul aircraft...\n";
    if (longHaul1) longHaul1->useSize(75.0);
    if (longHaul2) longHaul2->useSize(75.0);
    seat->useTool();
    cout << "Long haul flight organized successfully!\n";
}
MaintenanceFlight::MaintenanceFlight(const char* n,
                                              Aircraft* a,
                                              MaintenanceKit* rk)
    : Flight(n), aircraft(a),
      maintenanceKit(rk) {}
void MaintenanceFlight::organize() {
    if (!maintenanceKit) throw ToolNotAvailableException("No maintenance kit");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Starting maintenance process...\n";
    if (aircraft) aircraft->useSize(20.0);
    maintenanceKit->equip();
    maintenanceKit->maintain();
    cout << "Maintenance flight organized successfully!\n";
}
SeasonalFlight::SeasonalFlight(const char* n,
                                          Aircraft* t1,
                                          Aircraft* t2,
                                          Gate* st)
    : Flight(n), seasonal1(t1), seasonal2(t2),
      gate(st) {}
void SeasonalFlight::organize() {
    if (!gate) throw ToolNotAvailableException("No gate");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing seasonal aircraft...\n";
    if (seasonal1) seasonal1->useSize(50.0);
    if (seasonal2) seasonal2->useSize(50.0);
    gate->startBoarding();
    cout << "Seasonal flight organized successfully!\n";
}
RegularFlight::RegularFlight(const char* n,
                                          Aircraft* p1,
                                          Aircraft* p2,
                                          SecuritySystem* sec)
    : Flight(n), regular1(p1), regular2(p2),
      security(sec) {}
void RegularFlight::organize() {
    if (!security) throw ToolNotAvailableException("No security system");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing regular aircraft...\n";
    if (regular1) regular1->useSize(55.0);
    if (regular2) regular2->useSize(55.0);
    security->activateAllZones();
    cout << "Regular flight organized successfully!\n";
}
InteractiveFlight::InteractiveFlight(const char* n,
                                             Aircraft* i1,
                                             Aircraft* i2,
                                             SecurityCamera* cam)
    : Flight(n), interactive1(i1), interactive2(i2),
      camera(cam) {}
void InteractiveFlight::organize() {
    if (!camera) throw ToolNotAvailableException("No security camera");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing interactive aircraft...\n";
    if (interactive1) interactive1->useSize(60.0);
    if (interactive2) interactive2->useSize(60.0);
    camera->startRecording();
    cout << "Interactive flight organized successfully!\n";
}
ThematicFlight::ThematicFlight(const char* n,
                                       Aircraft* th1,
                                       Aircraft* th2,
                                       Aircraft* th3,
                                       Gate* st)
    : Flight(n), theme1(th1), theme2(th2), theme3(th3),
      gate(st) {}
void ThematicFlight::organize() {
    if (!gate) throw ToolNotAvailableException("No gate");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing thematic aircraft...\n";
    if (theme1) theme1->useSize(45.0);
    if (theme2) theme2->useSize(45.0);
    if (theme3) theme3->useSize(45.0);
    gate->startBoarding();
    cout << "Thematic flight organized successfully!\n";
}
RetrospectiveFlight::RetrospectiveFlight(const char* n,
                                                   Aircraft* r1,
                                                   Aircraft* r2,
                                                   CabinClimateControl* cc)
    : Flight(n), retro1(r1), retro2(r2),
      cabinClimate(cc) {}
void RetrospectiveFlight::organize() {
    if (!cabinClimate) throw ToolNotAvailableException("No climate control");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing retrospective aircraft...\n";
    if (retro1) retro1->useSize(50.0);
    if (retro2) retro2->useSize(50.0);
    cabinClimate->setConditions(21.0, 12);
    cout << "Retrospective flight organized successfully!\n";
}
GroupFlight::GroupFlight(const char* n,
                                 Aircraft* g1,
                                 Aircraft* g2,
                                 Aircraft* g3,
                                 Seat* f)
    : Flight(n), group1(g1), group2(g2), group3(g3),
      seat(f) {}
void GroupFlight::organize() {
    if (!seat) throw ToolNotAvailableException("No seat");
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing group aircraft...\n";
    if (group1) group1->useSize(55.0);
    if (group2) group2->useSize(55.0);
    if (group3) group3->useSize(55.0);
    seat->useTool();
    cout << "Group flight organized successfully!\n";
}
SoloFlight::SoloFlight(const char* n,
                                Aircraft* s1,
                                Aircraft* s2)
    : Flight(n), solo1(s1), solo2(s2) {}
void SoloFlight::organize() {
    cout << "\n=== Organizing flight: " << getName() << " ===\n";
    cout << "Preparing solo aircraft...\n";
    if (solo1) solo1->useSize(70.0);
    if (solo2) solo2->useSize(70.0);
    cout << "Solo flight organized successfully!\n";
}
FlightDispatcher::FlightDispatcher(const char* n)
    : name(n) {}
void FlightDispatcher::organizeFlight(Flight* flight) {
    if (!flight) {
        throw AircraftNotFoundException("Flight is null");
    }
    flight->organize();
}
Passenger::Passenger(const char* n, int al, bool ht)
    : name(n), accessLevel(al), hasTicket(ht), visitDuration(0.0), favoriteCount(0), guidedTour(false) {}
void Passenger::purchaseTicket() {
    hasTicket = true;
    cout << "Passenger " << name << " purchased ticket.\n";
}
void Passenger::enterAirline() {
    if (!hasTicket) {
        throw InvalidAccessException("Passenger needs ticket to enter");
    }
    cout << "Passenger " << name << " entered airline.\n";
}
void Passenger::viewAircraft(Aircraft* aircraft) {
    if (!aircraft) {
        throw AircraftNotFoundException("Aircraft not found");
    }
    cout << "Passenger " << name << " viewing " << aircraft->getManufacturer() << " aircraft.\n";
    visitDuration += 5.0;
}
void Passenger::addFavorite() {
    favoriteCount++;
    cout << "Passenger " << name << " added favorite. Total: " << favoriteCount << "\n";
}
void Passenger::joinGuidedTour() {
    guidedTour = true;
    cout << "Passenger " << name << " joined guided tour.\n";
}
bool Passenger::canAccessRestricted() const {
    return accessLevel >= 3 && hasTicket;
}
int Passenger::getAccessLevel() const {
    return accessLevel;
}
const char* Passenger::getName() const {
    return name;
}
double Passenger::getVisitDuration() const {
    return visitDuration;
}
AirlineMenu::AirlineMenu() : flightCount(0), currentPassenger(nullptr) {
    for (int i = 0; i < MAX_FLIGHTS; i++) {
        flights[i] = nullptr;
    }
}
void AirlineMenu::show() const {
    cout << "\n==== AIRLINE MENU ====\n";
    for (int i = 0; i < flightCount; i++) {
        cout << (i + 1) << ") " << flights[i]->getName() << "\n";
    }
    cout << "0) Exit\n";
}
void AirlineMenu::addFlight(Flight* e) {
    if (e && flightCount < MAX_FLIGHTS) {
        flights[flightCount] = e;
        flightCount++;
    }
}
void AirlineMenu::setPassenger(Passenger* v) {
    currentPassenger = v;
}
void AirlineMenu::run() {
    while (true) {
        show();
        cout << "Select flight number: ";
        int choice = 0;
        if (!(cin >> choice)) {
            cout << "Invalid input, exiting.\n";
            return;
        }
        if (choice == 0) {
            cout << "Exiting airline menu.\n";
            return;
        }
        if (choice < 1 || choice > flightCount) {
            cout << "No such option.\n";
            continue;
        }
        flights[choice - 1]->organize();
        cout << "Flight \"" << flights[choice - 1]->getName()
             << "\" successfully organized.\n";
    }
}
int AirlineMenu::getFlightCount() const {
    return flightCount;
}
Passenger* AirlineMenu::getCurrentPassenger() const {
    return currentPassenger;
}
int AirlineMenu::searchFlights(const char* searchTerm) const {
    int count = 0;
    for (int i = 0; i < flightCount; i++) {
        if (flights[i] && strstr(flights[i]->getName(), searchTerm)) {
            count++;
        }
    }
    return count;
}
int AirlineMenu::filterAvailableFlights() const {
    int count = 0;
    for (int i = 0; i < flightCount; i++) {
        if (flights[i] && !flights[i]->isFullyBooked()) {
            count++;
        }
    }
    return count;
}
void AirlineMenu::sortFlightsByName() {
    for (int i = 0; i < flightCount - 1; i++) {
        for (int j = i + 1; j < flightCount; j++) {
            if (flights[i] && flights[j] && strcmp(flights[i]->getName(), flights[j]->getName()) > 0) {
                Flight* temp = flights[i];
                flights[i] = flights[j];
                flights[j] = temp;
            }
        }
    }
}
Flight* AirlineMenu::getFlightByIndex(int index) const {
    if (index >= 0 && index < flightCount) {
        return flights[index];
    }
    return nullptr;
}
BookingSystem::BookingSystem(const char* name, int max)
    : systemName(name), totalBookings(0), totalRevenue(0.0), isActive(true), maxBookings(max),
      currentBookingPassenger(nullptr), currentBookingFlight(nullptr) {}
bool BookingSystem::createBooking(Passenger* passenger, Flight* flight) {
    if (!isActive || totalBookings >= maxBookings || !passenger || !flight) {
        return false;
    }
    if (flight->isFullyBooked()) {
        return false;
    }
    currentBookingPassenger = passenger;
    currentBookingFlight = flight;
    totalBookings++;
    return true;
}
bool BookingSystem::cancelBooking(int bookingId) {
    if (bookingId < 0 || bookingId >= totalBookings) {
        return false;
    }
    totalBookings--;
    return true;
}
double BookingSystem::calculateTicketPrice(Flight* flight, Passenger* passenger) {
    if (!flight || !passenger) {
        return 0.0;
    }
    double basePrice = 500.0;
    double discount = passenger->calculateLoyaltyDiscount(basePrice);
    return basePrice - discount;
}
bool BookingSystem::processPayment(double amount, const char* cardNumber) {
    if (amount <= 0.0 || !cardNumber || strlen(cardNumber) < 13) {
        return false;
    }
    totalRevenue += amount;
    return true;
}
bool BookingSystem::transferMoney(const char* fromCard, const char* toCard, double amount) {
    if (!fromCard || !toCard || amount <= 0.0) {
        return false;
    }
    if (strlen(fromCard) < 13 || strlen(toCard) < 13) {
        return false;
    }
    return true;
}
bool BookingSystem::verifyPassword(const char* accountId, const char* password) {
    if (!accountId || !password) {
        return false;
    }
    return strlen(password) >= 6;
}
bool BookingSystem::checkFlightAvailability(Flight* flight) {
    if (!flight) {
        return false;
    }
    return !flight->isFullyBooked();
}
bool BookingSystem::reserveSeat(Passenger* passenger, int seatNumber) {
    if (!passenger || seatNumber < 1 || seatNumber > 500) {
        return false;
    }
    return true;
}
bool BookingSystem::cancelSeatReservation(int seatNumber) {
    if (seatNumber < 1 || seatNumber > 500) {
        return false;
    }
    return true;
}
double BookingSystem::calculateBaggageFee(double weight) {
    if (weight <= 0.0) {
        return 0.0;
    }
    if (weight <= 23.0) {
        return 0.0;
    }
    double excess = weight - 23.0;
    return excess * 10.0;
}
bool BookingSystem::checkVisaRequirement(Passenger* passenger, Flight* flight) {
    if (!passenger || !flight) {
        return false;
    }
    return passenger->hasValidVisa("International");
}
double BookingSystem::getTotalRevenue() const {
    return totalRevenue;
}
int BookingSystem::getTotalBookings() const {
    return totalBookings;
}
bool BookingSystem::isSystemActive() const {
    return isActive;
}
double Aircraft::calculateMaintenanceCost() const {
    double baseCost = 1000.0;
    if (certified) {
        baseCost *= 0.9;
    }
    int age = 2025 - year;
    return baseCost * (1.0 + age * 0.05);
}
bool Aircraft::isAvailableForFlight() const {
    return certified && !fragile;
}
double Aircraft::calculateDepreciation(int currentYear) const {
    if (year <= 0 || currentYear < year) {
        return value;
    }
    int age = currentYear - year;
    double depreciationRate = 0.1;
    return value * (1.0 - depreciationRate * age);
}
bool Aircraft::needsInspection() const {
    int age = 2025 - year;
    return age > 5;
}
double Aircraft::calculateFuelConsumption(double distance) const {
    if (distance <= 0.0) {
        return 0.0;
    }
    double baseConsumption = 3.5;
    return distance * baseConsumption / 100.0;
}
double Passenger::calculateTotalBaggageWeight(double checkedWeight, double carryOnWeight) const {
    return checkedWeight + carryOnWeight;
}
bool Passenger::hasValidVisa(const char* destinationCountry) const {
    if (!destinationCountry) {
        return false;
    }
    return accessLevel >= 2;
}
double Passenger::calculateLoyaltyDiscount(double basePrice) const {
    if (favoriteCount > 10) {
        return basePrice * 0.15;
    } else if (favoriteCount > 5) {
        return basePrice * 0.10;
    }
    return 0.0;
}
bool Passenger::requestSpecialMeal(const char* mealType) {
    if (!mealType) {
        return false;
    }
    return hasTicket;
}
bool Passenger::checkInForFlight(const char* flightNumber) {
    if (!flightNumber || !hasTicket) {
        return false;
    }
    return true;
}
bool Passenger::cancelReservation(int reservationId) {
    if (reservationId < 0) {
        return false;
    }
    return hasTicket;
}
double Passenger::calculateTotalTravelCost(double ticketPrice, double baggageFee, double mealFee) const {
    return ticketPrice + baggageFee + mealFee;
}
bool Flight::isFullyBooked() const {
    return false;
}
double Flight::calculateFlightDuration() const {
    return 2.5;
}
bool Flight::isOnTime() const {
    return true;
}
int Flight::getAvailableSeats() const {
    return 150;
}
int Timer::calculateRemainingTime() const {
    if (seconds <= 0) {
        return 0;
    }
    return seconds - elapsed;
}
void Timer::reset() {
    elapsed = 0;
    running = false;
}
void Timer::pause() {
    running = false;
}
void Timer::resume() {
    if (seconds > 0 && elapsed < seconds) {
        running = true;
    }
}
void SecuritySystem::activateAllZones() {
    activeZones = zones;
}
void SecuritySystem::deactivateAllZones() {
    activeZones = 0;
}
bool SecuritySystem::checkSecurityBreach() const {
    return activeZones < zones && on;
}
double SecuritySystem::calculateSecurityCoverage() const {
    if (zones == 0) {
        return 0.0;
    }
    return (activeZones * 100.0) / zones;
}
double CabinClimateControl::calculateEnergyConsumption() const {
    if (!on) {
        return 0.0;
    }
    return 2.5 * (temperature / 20.0);
}
bool CabinClimateControl::isOptimalClimate() const {
    return temperature >= 20.0 && temperature <= 24.0 && humidity >= 40.0 && humidity <= 60.0;
}
void CabinClimateControl::adjustTemperatureGradually(double targetTemp, int duration) {
    if (duration > 0 && targetTemp > 0.0 && targetTemp <= 30.0) {
        profile.reset(temperature, targetTemp, duration * 60);
        elapsedSeconds = 0;
        on = true;
    }
}
int CabinClimateControl::calculateMaintenanceSchedule() const {
    return 30;
}
double Gate::calculateBoardingTime(int passengerCount) const {
    if (passengerCount <= 0) {
        return 0.0;
    }
    return passengerCount * 0.5;
}
bool Gate::canHandlePassengerLoad(int passengerCount) const {
    double requiredCapacity = passengerCount * 0.5;
    return capacity >= requiredCapacity;
}
double Gate::calculateUtilization() const {
    if (capacity <= 0.0) {
        return 0.0;
    }
    return inUse ? 75.0 : 25.0;
}
void SecurityCamera::adjustAngle(double newAngle) {
    if (newAngle >= 0.0 && newAngle <= 360.0) {
        angle = newAngle;
    }
}
double SecurityCamera::calculateCoverageArea(double distance) const {
    if (distance <= 0.0) {
        return 0.0;
    }
    double radius = distance * tan(angle * 3.14159 / 180.0 / 2.0);
    return 3.14159 * radius * radius;
}
bool SecurityCamera::canMonitorArea(double areaSize) const {
    if (areaSize <= 0.0 || !active) {
        return false;
    }
    double maxArea = calculateCoverageArea(50.0);
    return areaSize <= maxArea;
}
double CabinLighting::calculatePowerConsumption() const {
    if (led) {
        return dimmed ? 5.0 : 10.0;
    }
    return dimmed ? 20.0 : 40.0;
}
void CabinLighting::setBrightness(int level) {
    if (level >= 0 && level <= 100) {
        dimmed = (level < 50);
    }
}
bool CabinLighting::meetsSafetyStandards() const {
    return led && isAvailable();
}
double Seat::calculateComfortScore() const {
    double score = 5.0;
    if (protective) {
        score += 2.0;
    }
    if (width > 50) {
        score += 1.0;
    }
    if (isAvailable()) {
        score += 2.0;
    }
    return score > 10.0 ? 10.0 : score;
}
bool Seat::isSuitableForPassenger(double passengerWeight) const {
    if (passengerWeight <= 0.0) {
        return false;
    }
    return passengerWeight <= 150.0 && isAvailable();
}
void Seat::adjustPosition(int position) {
    if (position >= -45 && position <= 45) {
    }
}
double ConditionProfile::calculateTemperatureChangeRate() const {
    if (duration <= 0) {
        return 0.0;
    }
    return (targetTemp - startTemp) / duration;
}
bool ConditionProfile::isValidProfile() const {
    return duration > 0 && startTemp >= -50.0 && targetTemp <= 50.0;
}
int ConditionProfile::getEstimatedCompletionTime(int currentElapsed) const {
    if (currentElapsed < 0) {
        return duration;
    }
    int remaining = duration - currentElapsed;
    return remaining > 0 ? remaining : 0;
}
double MaintenanceKit::calculateMaintenanceEfficiency() const {
    if (!isEquipped()) {
        return 0.0;
    }
    return isAvailable() ? 85.0 : 50.0;
}
bool MaintenanceKit::hasRequiredTools(int toolCount) const {
    return isEquipped() && toolCount > 0 && toolCount <= 10;
}
double Size::convertToDimension(Dimension* targetDimension) const {
    if (!targetDimension || !dimension) {
        return 0.0;
    }
    double cm = toCentimeters();
    return targetDimension->fromCentimeters(cm);
}
double Size::calculateDifference(const Size& otherSize) const {
    double thisCm = toCentimeters();
    double otherCm = otherSize.toCentimeters();
    return thisCm > otherCm ? thisCm - otherCm : otherCm - thisCm;
}
double Dimension::convertTo(double amount, Dimension* targetDimension) const {
    if (!targetDimension) {
        return 0.0;
    }
    double cm = toCentimeters(amount);
    return targetDimension->fromCentimeters(cm);
}
bool Dimension::validateConversion(double amount) const {
    return amount >= 0.0 && cmPerUnit > 0.0;
}