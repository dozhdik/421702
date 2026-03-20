#include <gtest/gtest.h>
#include <sstream>
#include <iostream>
#include <vector>
#include "../airline.hpp"

using namespace std;

static Dimension cmUnit("cm", 1.0, true, 1);

static Aircraft makeAircraft(const char* name, double cm, bool fragile = false) {
    Size s(cm, &cmUnit, false, 1);
    return Aircraft(name, s, 0.0, fragile);
}

TEST(Dimension, DefaultCtor) {
    Dimension d;
    EXPECT_NEAR(10.0, d.toCentimeters(10.0), 1e-9);
    EXPECT_TRUE(d.isMetric());
    EXPECT_EQ(0, d.getId());
}

TEST(Dimension, CustomCtor) {
    Dimension inch("in", 2.54, false, 7);
    EXPECT_NEAR(25.4, inch.toCentimeters(10.0), 1e-9);
    EXPECT_FALSE(inch.isMetric());
    EXPECT_EQ(7, inch.getId());
}

TEST(Dimension, IsMetricFlag) {
    Dimension metric("cm", 1.0, true, 2);
    Dimension imperial("in", 2.54, false, 3);
    EXPECT_TRUE(metric.isMetric());
    EXPECT_FALSE(imperial.isMetric());
}

TEST(Size, ToCentimeters_WithDimension) {
    Size s(200.0, &cmUnit);
    EXPECT_NEAR(200.0, s.toCentimeters(), 1e-9);
}

TEST(Size, ToCentimeters_NoDimension_Throws) {
    Size s(100.0, nullptr);
    EXPECT_THROW(s.toCentimeters(), StorageException);
}

TEST(Size, Scale_Up) {
    Size s(100.0, &cmUnit);
    s.scale(2.0);
    EXPECT_NEAR(200.0, s.toCentimeters(), 1e-9);
}

TEST(Size, Scale_DownToZero_IsZero) {
    Size s(100.0, &cmUnit);
    s.scale(0.0);
    EXPECT_TRUE(s.isZero());
}

TEST(Aircraft, Fragile_True) {
    Size s(100.0, &cmUnit);
    Aircraft passenger("passenger", s, 200.0, true);
    EXPECT_TRUE(passenger.isFragile());
}

TEST(Aircraft, Fragile_False) {
    Size s(100.0, &cmUnit);
    Aircraft cargo("cargo", s, 0.0, false);
    EXPECT_FALSE(cargo.isFragile());
}

TEST(Aircraft, AddSize_Increase) {
    Size s(100.0, &cmUnit);
    Aircraft a("aircraft", s, 0.0, false);
    a.addSize(50.0);
    EXPECT_FALSE(a.isFragile());
}

TEST(Aircraft, AddSize_FromZero_NoCrash) {
    Size s(0.0, &cmUnit);
    Aircraft a("aircraft", s, 0.0, false);
    a.addSize(100.0);
}

TEST(Aircraft, UseSize_Enough) {
    Size s(200.0, &cmUnit);
    Aircraft a("aircraft", s, 0.0, false);
    a.useSize(100.0);
    EXPECT_FALSE(a.isFragile());
}

TEST(Aircraft, UseSize_NotEnough_Throws) {
    Size s(50.0, &cmUnit);
    Aircraft a("aircraft", s, 0.0, false);
    EXPECT_THROW(a.useSize(100.0), NotEnoughAircraftException);
}

TEST(AirlineTool, DefaultAvailable) {
    AirlineTool t;
    EXPECT_TRUE(t.isAvailable());
}

TEST(AirlineTool, UseTool_DecreasesDurability) {
    AirlineTool t("tool", true, true, 2);
    EXPECT_TRUE(t.isAvailable());
    t.useTool();
    EXPECT_TRUE(t.isAvailable());
    t.useTool();
    EXPECT_FALSE(t.isAvailable());
}

TEST(AirlineTool, UseTool_Dirty_Throws) {
    AirlineTool t("tool", false, true, 10);
    EXPECT_THROW(t.useTool(), ToolNotAvailableException);
}

TEST(AirlineTool, UseTool_NotAvailable_Throws) {
    AirlineTool t("tool", true, false, 10);
    EXPECT_THROW(t.useTool(), ToolNotAvailableException);
}

TEST(AirlineTool, CleanTool_MakesAvailable) {
    AirlineTool t("tool", false, true, 10);
    EXPECT_FALSE(t.isAvailable());
    t.cleanTool();
    EXPECT_TRUE(t.isAvailable());
}

TEST(Seat, CanProtect_True) {
    Seat f("Seat", true, 50, 1);
    EXPECT_TRUE(f.canProtect());
}

TEST(Seat, NoProtection_CannotProtect) {
    Seat f("Seat", false, 50, 1);
    EXPECT_FALSE(f.canProtect());
}

TEST(Seat, AddProtection_MakesProtective) {
    Seat f("Seat", false, 50, 1);
    f.addProtection();
    EXPECT_TRUE(f.canProtect());
}

TEST(CabinLighting, IsSafeForAircraft_True) {
    CabinLighting l("CabinLighting", true, false, 1);
    EXPECT_TRUE(l.isSafeForCabin());
}

TEST(CabinLighting, Dimmed_NotSafe) {
    CabinLighting l("CabinLighting", true, true, 1);
    EXPECT_FALSE(l.isSafeForCabin());
    l.brighten();
    EXPECT_TRUE(l.isSafeForCabin());
}

TEST(CabinLighting, NotLED_NotSafe) {
    CabinLighting l("CabinLighting", false, false, 1);
    EXPECT_FALSE(l.isSafeForCabin());
}

TEST(SecurityCamera, StartRecording_Ok) {
    SecurityCamera cam("Camera", 90.0, false, false);
    cam.startRecording();
    EXPECT_TRUE(cam.isRecording());
}

TEST(SecurityCamera, StopRecording_Ok) {
    SecurityCamera cam("Camera", 90.0, true, true);
    cam.stopRecording();
    EXPECT_FALSE(cam.isRecording());
}

TEST(SecurityCamera, NotAvailable_Throws) {
    SecurityCamera cam("Camera", 90.0, false, false);
    AirlineTool* base = &cam;
    base->breakTool();
    EXPECT_THROW(cam.startRecording(), ToolNotAvailableException);
}

TEST(Gate, CanDisplay_True) {
    Gate gate("Stand", 5.0, true, false);
    EXPECT_TRUE(gate.canAccommodate(3.0));
    EXPECT_FALSE(gate.canAccommodate(6.0));
}

TEST(Gate, StartDisplay_Ok) {
    Gate gate("Stand", 5.0, true, false);
    gate.startBoarding();
}

TEST(Gate, NotAvailable_Throws) {
    Gate gate("Stand", 5.0, true, false);
    AirlineTool* base = &gate;
    base->breakTool();
    EXPECT_THROW(gate.startBoarding(), ToolNotAvailableException);
}

TEST(Timer, StartAndFinish) {
    Timer t;
    t.start(10);
    EXPECT_FALSE(t.isFinished());
    t.tick(5);
    EXPECT_FALSE(t.isFinished());
    t.tick(5);
    EXPECT_TRUE(t.isFinished());
}

TEST(Timer, Start_Invalid_Throws) {
    Timer t;
    EXPECT_THROW(t.start(0), TimerNotSetException);
    EXPECT_THROW(t.start(-5), TimerNotSetException);
}

TEST(Timer, Tick_NegativeOrZeroIgnored) {
    Timer t;
    t.start(10);
    t.tick(0);
    t.tick(-5);
    EXPECT_FALSE(t.isFinished());
}

TEST(Timer, Tick_NotRunning_NoEffect) {
    Timer t;
    t.start(10);
    t.tick(10);
    EXPECT_TRUE(t.isFinished());
    t.tick(10);
    EXPECT_TRUE(t.isFinished());
}

TEST(MaintenanceKit, EquipUnplugSequence) {
    MaintenanceKit rk("MaintenanceKit", false);
    EXPECT_FALSE(rk.unequip());
    EXPECT_TRUE(rk.equip());
    EXPECT_FALSE(rk.unequip());
}

TEST(MaintenanceKit, Restore_NotEquipped_NoCrash) {
    MaintenanceKit rk("MaintenanceKit", false);
    rk.maintain();
}

TEST(MaintenanceKit, Restore_NotAvailable_Throws) {
    MaintenanceKit rk("MaintenanceKit", true);
    AirlineTool* base = &rk;
    base->breakTool();
    EXPECT_THROW(rk.maintain(), ToolNotAvailableException);
}

TEST(CleaningKit, Clean_Ok) {
    CleaningKit ck("CleaningKit", 1);
    ck.clean();
}

TEST(CleaningKit, Clean_NotAvailable_Throws) {
    CleaningKit ck("CleaningKit", 1);
    AirlineTool* base = &ck;
    base->breakTool();
    EXPECT_THROW(ck.clean(), ToolNotAvailableException);
}

TEST(ConditionProfile, Gradual) {
    ConditionProfile cp(20.0, 18.0, 10, true);
    double mid = cp.currentTemp(5);
    EXPECT_GT(mid, 18.0);
    EXPECT_LT(mid, 20.0);
}

TEST(ConditionProfile, Gradual_AfterDuration) {
    ConditionProfile cp(20.0, 18.0, 10, true);
    double end = cp.currentTemp(20);
    EXPECT_NEAR(18.0, end, 1e-9);
}

TEST(ConditionProfile, Jump) {
    ConditionProfile cp(20.0, 18.0, 10, false);
    EXPECT_NEAR(18.0, cp.currentTemp(0), 1e-9);
    EXPECT_TRUE(cp.isReached(18.0));
    EXPECT_TRUE(cp.isReached(19.0));
}

TEST(ConditionProfile, Reset) {
    ConditionProfile cp;
    cp.reset(30.0, 19.0, 5);
    double mid = cp.currentTemp(3);
    EXPECT_GT(mid, 19.0);
    EXPECT_LE(mid, 30.0);
}

TEST(CabinClimateControl, SetConditions_Ok) {
    CabinClimateControl cc(0.0, false, true);
    cc.setConditions(20.0, 10);
    EXPECT_TRUE(cc.isOn());
    cc.tick(10 * 60);
    EXPECT_NEAR(20.0, cc.getTemperature(), 1e-9);
}

TEST(CabinClimateControl, SetConditions_InvalidLow_Throws) {
    CabinClimateControl cc(0.0, false, true);
    EXPECT_THROW(cc.setConditions(0.0), InvalidConditionException);
    EXPECT_THROW(cc.setConditions(-10.0), InvalidConditionException);
}

TEST(CabinClimateControl, SetConditions_InvalidHigh_Throws) {
    CabinClimateControl cc(0.0, false, true);
    EXPECT_THROW(cc.setConditions(31.0), InvalidConditionException);
}

TEST(CabinClimateControl, SetConditions_DoorOpen_Throws) {
    CabinClimateControl cc(0.0, false, false);
    EXPECT_THROW(cc.setConditions(20.0), InvalidConditionException);
}

TEST(CabinClimateControl, SetTimerMinutes_Invalid_Throws) {
    CabinClimateControl cc(0.0, false, true);
    EXPECT_THROW(cc.setTimerMinutes(0), TimerNotSetException);
}

TEST(CabinClimateControl, Tick_TurnsOff) {
    CabinClimateControl cc(0.0, false, true);
    cc.setConditions(20.0);
    cc.setTimerMinutes(1);
    EXPECT_TRUE(cc.isOn());
    cc.tick(30);
    EXPECT_TRUE(cc.isOn());
    cc.tick(30);
    EXPECT_FALSE(cc.isOn());
}

TEST(SecuritySystem, Zones_OnOff) {
    SecuritySystem s(4, 0, true, false);
    EXPECT_EQ(4, s.freeZones());
    s.activateZone();
    EXPECT_EQ(3, s.freeZones());
    s.activateZone();
    s.activateZone();
    s.activateZone();
    EXPECT_EQ(0, s.freeZones());
    s.deactivateZone();
    EXPECT_EQ(1, s.freeZones());
}

TEST(SecuritySystem, Deactivate_NoActive_NoCrash) {
    SecuritySystem s(4, 0, true, false);
    EXPECT_EQ(4, s.freeZones());
    s.deactivateZone();
    EXPECT_EQ(4, s.freeZones());
}

TEST(PassengerFlight, Organize_Success) {
    Aircraft p1 = makeAircraft("passenger1", 1000.0);
    Aircraft p2 = makeAircraft("passenger2", 1000.0);
    Seat f("Seat", true, 50, 1);
    PassengerFlight ex("Painting", &p1, &p2, &f);
    ex.organize();
}

TEST(CargoFlight, Organize_Success) {
    Aircraft s = makeAircraft("cargo", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    CargoFlight ex("Sculpture", &s, &gate);
    ex.organize();
}

TEST(CharterFlight, Organize_Success) {
    Aircraft ph1 = makeAircraft("charter1", 1000.0);
    Aircraft ph2 = makeAircraft("charter2", 1000.0);
    SecurityCamera cam("Camera", 90.0, false, false);
    CharterFlight ex("Photography", &ph1, &ph2, &cam);
    ex.organize();
}

TEST(MixedFlight, Organize_Success) {
    Aircraft a1 = makeAircraft("aircraft1", 1000.0);
    Aircraft a2 = makeAircraft("aircraft2", 1000.0);
    Aircraft a3 = makeAircraft("aircraft3", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    MixedFlight ex("Mixed Media", &a1, &a2, &a3, &gate);
    ex.organize();
}

TEST(BusinessFlight, Organize_Success) {
    Aircraft d1 = makeAircraft("business1", 1000.0);
    Aircraft d2 = makeAircraft("business2", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    BusinessFlight ex("Digital Art", &d1, &d2, &gate);
    ex.organize();
}

TEST(VintageFlight, Organize_Success) {
    Aircraft v1 = makeAircraft("vintage1", 1000.0);
    Aircraft v2 = makeAircraft("vintage2", 1000.0);
    CabinClimateControl cc(0.0, false, true);
    VintageFlight ex("Vintage", &v1, &v2, &cc);
    ex.organize();
}

TEST(ModernFlight, Organize_Success) {
    Aircraft c1 = makeAircraft("modern1", 1000.0);
    Aircraft c2 = makeAircraft("modern2", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    ModernFlight ex("Conseasonalorary", &c1, &c2, &gate);
    ex.organize();
}

TEST(EconomyFlight, Organize_Success) {
    Aircraft m = makeAircraft("economy", 1000.0);
    Seat f("Seat", true, 50, 1);
    EconomyFlight ex("Minimalist", &m, &f);
    ex.organize();
}

TEST(InternationalFlight, Organize_Success) {
    Aircraft a1 = makeAircraft("international1", 1000.0);
    Aircraft a2 = makeAircraft("international2", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    InternationalFlight ex("Abstract", &a1, &a2, &gate);
    ex.organize();
}

TEST(DomesticFlight, Organize_Success) {
    Aircraft p1 = makeAircraft("domestic1", 1000.0);
    Aircraft p2 = makeAircraft("domestic2", 1000.0);
    SecurityCamera cam("Camera", 90.0, false, false);
    DomesticFlight ex("Portrait", &p1, &p2, &cam);
    ex.organize();
}

TEST(LongHaulFlight, Organize_Success) {
    Aircraft l1 = makeAircraft("longHaul1", 1000.0);
    Aircraft l2 = makeAircraft("longHaul2", 1000.0);
    Seat f("Seat", true, 50, 1);
    LongHaulFlight ex("Landscape", &l1, &l2, &f);
    ex.organize();
}

TEST(MaintenanceFlight, Organize_Success) {
    Aircraft a = makeAircraft("aircraft", 1000.0);
    MaintenanceKit rk("MaintenanceKit", false);
    MaintenanceFlight ex("Restoration", &a, &rk);
    ex.organize();
}

TEST(SeasonalFlight, Organize_Success) {
    Aircraft t1 = makeAircraft("seasonal1", 1000.0);
    Aircraft t2 = makeAircraft("seasonal2", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    SeasonalFlight ex("Temporary", &t1, &t2, &gate);
    ex.organize();
}

TEST(RegularFlight, Organize_Success) {
    Aircraft p1 = makeAircraft("regular1", 1000.0);
    Aircraft p2 = makeAircraft("regular2", 1000.0);
    SecuritySystem sec(4, 0, true, false);
    RegularFlight ex("Permanent", &p1, &p2, &sec);
    ex.organize();
}

TEST(InteractiveFlight, Organize_Success) {
    Aircraft i1 = makeAircraft("interactive1", 1000.0);
    Aircraft i2 = makeAircraft("interactive2", 1000.0);
    SecurityCamera cam("Camera", 90.0, false, false);
    InteractiveFlight ex("Interactive", &i1, &i2, &cam);
    ex.organize();
}

TEST(ThematicFlight, Organize_Success) {
    Aircraft th1 = makeAircraft("theme1", 1000.0);
    Aircraft th2 = makeAircraft("theme2", 1000.0);
    Aircraft th3 = makeAircraft("theme3", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    ThematicFlight ex("Thematic", &th1, &th2, &th3, &gate);
    ex.organize();
}

TEST(RetrospectiveFlight, Organize_Success) {
    Aircraft r1 = makeAircraft("retro1", 1000.0);
    Aircraft r2 = makeAircraft("retro2", 1000.0);
    CabinClimateControl cc(0.0, false, true);
    RetrospectiveFlight ex("Retrospective", &r1, &r2, &cc);
    ex.organize();
}

TEST(GroupFlight, Organize_Success) {
    Aircraft g1 = makeAircraft("group1", 1000.0);
    Aircraft g2 = makeAircraft("group2", 1000.0);
    Aircraft g3 = makeAircraft("group3", 1000.0);
    Seat f("Seat", true, 50, 1);
    GroupFlight ex("Group", &g1, &g2, &g3, &f);
    ex.organize();
}

TEST(SoloFlight, Organize_Success) {
    Aircraft s1 = makeAircraft("solo1", 1000.0);
    Aircraft s2 = makeAircraft("solo2", 1000.0);
    SoloFlight ex("Solo", &s1, &s2);
    ex.organize();
}

TEST(PassengerFlight, NoSeat_Throws) {
    Aircraft p1 = makeAircraft("passenger1", 1000.0);
    Aircraft p2 = makeAircraft("passenger2", 1000.0);
    PassengerFlight ex("Painting", &p1, &p2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(CargoFlight, NoGate_Throws) {
    Aircraft s = makeAircraft("cargo", 1000.0);
    CargoFlight ex("Sculpture", &s, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(CharterFlight, NoCamera_Throws) {
    Aircraft ph1 = makeAircraft("charter1", 1000.0);
    Aircraft ph2 = makeAircraft("charter2", 1000.0);
    CharterFlight ex("Photography", &ph1, &ph2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(MixedFlight, NoAircraft_Throws) {
    Aircraft a2 = makeAircraft("aircraft2", 1000.0);
    Aircraft a3 = makeAircraft("aircraft3", 1000.0);
    Gate gate("Stand", 5.0, true, false);
    MixedFlight ex("Mixed Media", nullptr, &a2, &a3, &gate);
    ex.organize();
}

TEST(BusinessFlight, NoGate_Throws) {
    Aircraft d1 = makeAircraft("business1", 1000.0);
    Aircraft d2 = makeAircraft("business2", 1000.0);
    BusinessFlight ex("Digital Art", &d1, &d2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(VintageFlight, NoClimate_Throws) {
    Aircraft v1 = makeAircraft("vintage1", 1000.0);
    Aircraft v2 = makeAircraft("vintage2", 1000.0);
    VintageFlight ex("Vintage", &v1, &v2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(EconomyFlight, NoSeat_Throws) {
    Aircraft m = makeAircraft("economy", 1000.0);
    EconomyFlight ex("Minimalist", &m, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(InternationalFlight, NoGate_Throws) {
    Aircraft a1 = makeAircraft("international1", 1000.0);
    Aircraft a2 = makeAircraft("international2", 1000.0);
    InternationalFlight ex("Abstract", &a1, &a2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(DomesticFlight, NoAircraft_Throws) {
    Aircraft p2 = makeAircraft("domestic2", 1000.0);
    SecurityCamera cam("Camera", 90.0, false, false);
    DomesticFlight ex("Portrait", nullptr, &p2, &cam);
    ex.organize();
}

TEST(LongHaulFlight, NoSeat_Throws) {
    Aircraft l1 = makeAircraft("longHaul1", 1000.0);
    Aircraft l2 = makeAircraft("longHaul2", 1000.0);
    LongHaulFlight ex("Landscape", &l1, &l2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(MaintenanceFlight, NoAircraft_Throws) {
    MaintenanceKit rk("MaintenanceKit", false);
    MaintenanceFlight ex("Restoration", nullptr, &rk);
    ex.organize();
}

TEST(SeasonalFlight, NoGate_Throws) {
    Aircraft t1 = makeAircraft("seasonal1", 1000.0);
    Aircraft t2 = makeAircraft("seasonal2", 1000.0);
    SeasonalFlight ex("Temporary", &t1, &t2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(RegularFlight, NoSecurity_Throws) {
    Aircraft p1 = makeAircraft("regular1", 1000.0);
    Aircraft p2 = makeAircraft("regular2", 1000.0);
    RegularFlight ex("Permanent", &p1, &p2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(InteractiveFlight, NoCamera_Throws) {
    Aircraft i1 = makeAircraft("interactive1", 1000.0);
    Aircraft i2 = makeAircraft("interactive2", 1000.0);
    InteractiveFlight ex("Interactive", &i1, &i2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(ThematicFlight, NoGate_Throws) {
    Aircraft th1 = makeAircraft("theme1", 1000.0);
    Aircraft th2 = makeAircraft("theme2", 1000.0);
    Aircraft th3 = makeAircraft("theme3", 1000.0);
    ThematicFlight ex("Thematic", &th1, &th2, &th3, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(RetrospectiveFlight, NoClimate_Throws) {
    Aircraft r1 = makeAircraft("retro1", 1000.0);
    Aircraft r2 = makeAircraft("retro2", 1000.0);
    RetrospectiveFlight ex("Retrospective", &r1, &r2, nullptr);
    EXPECT_THROW(ex.organize(), ToolNotAvailableException);
}

TEST(GroupFlight, NoAircraft_Throws) {
    Aircraft g2 = makeAircraft("group2", 1000.0);
    Aircraft g3 = makeAircraft("group3", 1000.0);
    Seat f("Seat", true, 50, 1);
    GroupFlight ex("Group", nullptr, &g2, &g3, &f);
    ex.organize();
}

TEST(SoloFlight, Organize_Success_NoExceptions) {
    Aircraft s1 = makeAircraft("solo1", 1000.0);
    Aircraft s2 = makeAircraft("solo2", 1000.0);
    SoloFlight ex("Solo", &s1, &s2);
    ex.organize();
}

class DummyFlight : public Flight {
public:
    bool organized;
    DummyFlight(const char* n) : Flight(n), organized(false) {}
    void organize() override { organized = true; }
};

TEST(AirlineMenu, Run_ValidChoiceThenExit) {
    DummyFlight d("Dummy");
    AirlineMenu m;
    m.addFlight(&d);
    istringstream input("1\n0\n");
    streambuf* oldCin = cin.rdbuf(input.rdbuf());
    m.run();
    cin.rdbuf(oldCin);
    EXPECT_TRUE(d.organized);
}

TEST(AirlineMenu, Run_InvalidChoiceThenExit) {
    DummyFlight d("Dummy");
    AirlineMenu m;
    m.addFlight(&d);
    istringstream input("5\n1\n0\n");
    streambuf* oldCin = cin.rdbuf(input.rdbuf());
    m.run();
    cin.rdbuf(oldCin);
    EXPECT_TRUE(d.organized);
}

TEST(AirlineMenu, Run_InvalidInput_Break) {
    DummyFlight d("Dummy");
    AirlineMenu m;
    m.addFlight(&d);
    istringstream input("abc\n");
    streambuf* oldCin = cin.rdbuf(input.rdbuf());
    m.run();
    cin.rdbuf(oldCin);
    EXPECT_FALSE(d.organized);
}

TEST(Passenger, PurchaseTicket_Ok) {
    Passenger v("Passenger", 1, false);
    v.purchaseTicket();
    v.enterAirline();
}

TEST(Passenger, EnterGallery_NoTicket_Throws) {
    Passenger v("Passenger", 1, false);
    EXPECT_THROW(v.enterAirline(), InvalidAccessException);
}

TEST(Passenger, ViewAircraft_Ok) {
    Passenger v("Passenger", 1, true);
    Aircraft a = makeAircraft("aircraft", 100.0);
    v.viewAircraft(&a);
}

TEST(Passenger, ViewAircraft_NotFound_Throws) {
    Passenger v("Passenger", 1, true);
    EXPECT_THROW(v.viewAircraft(nullptr), AircraftNotFoundException);
}

TEST(Passenger, CanAccessRestricted_True) {
    Passenger v("Passenger", 3, true);
    EXPECT_TRUE(v.canAccessRestricted());
}

TEST(Passenger, CanAccessRestricted_False) {
    Passenger v("Passenger", 2, true);
    EXPECT_FALSE(v.canAccessRestricted());
}

TEST(MainSystem, InitializeDimensions) {
    Dimension cm, inch, meter;
    Aircraft testAircraft("Test", Size(100.0, &cmUnit, false, 1), 1000.0, false);
    EXPECT_FALSE(testAircraft.isFragile());
}

TEST(MainSystem, InitializeAircraftFleet) {
    Dimension cmUnit("cm", 1.0, true, 1);
    std::vector<Aircraft> fleet;
    fleet.push_back(Aircraft("Boeing 737", Size(77.0, &cmUnit, false, 1), 850000000.0, true));
    fleet.push_back(Aircraft("Airbus A320", Size(73.7, &cmUnit, false, 2), 100000000.0, true));
    EXPECT_EQ(2, fleet.size());
    EXPECT_TRUE(fleet[0].isFragile());
    EXPECT_TRUE(fleet[1].isFragile());
}

TEST(MainSystem, InitializeTools) {
    std::vector<Seat> seats;
    std::vector<CabinLighting> lights;
    std::vector<SecurityCamera> cameras;
    std::vector<Gate> gates;
    
    seats.push_back(Seat("Classic Seat", true, 50, 1));
    lights.push_back(CabinLighting("Airline CabinLighting", true, false, 1));
    cameras.push_back(SecurityCamera("Main Security Camera", 90.0, false, false));
    gates.push_back(Gate("Main Boarding Gate", 5.0, true, false));
    
    EXPECT_EQ(1, seats.size());
    EXPECT_EQ(1, lights.size());
    EXPECT_EQ(1, cameras.size());
    EXPECT_EQ(1, gates.size());
    EXPECT_TRUE(seats[0].canProtect());
    EXPECT_TRUE(lights[0].isSafeForCabin());
}

int runAirlineSystem(bool skipMenuRun = false);

TEST(MainSystem, RunAirlineSystem_CompleteInitialization) {
    int result = runAirlineSystem(true);
    EXPECT_EQ(0, result);
}

TEST(MainSystem, RunAirlineSystem_ErrorHandling) {
    int result = runAirlineSystem(true);
    EXPECT_EQ(0, result);
}
TEST(Dimension, FromCentimeters) {
    Dimension cm("cm", 1.0, true, 1);
    Dimension inch("in", 2.54, false, 2);
    
    EXPECT_NEAR(10.0, cm.fromCentimeters(10.0), 1e-9);
    EXPECT_NEAR(10.0, inch.fromCentimeters(25.4), 1e-9);
    EXPECT_NEAR(0.0, cm.fromCentimeters(0.0), 1e-9);
}

TEST(Dimension, FromCentimeters_ZeroDivisor) {
    Dimension zero("zero", 0.0, false, 3);
    EXPECT_NEAR(0.0, zero.fromCentimeters(100.0), 1e-9);
}

TEST(Dimension, SetPrecision) {
    Dimension d("cm", 1.0, true, 1);
    d.setPrecision(0.5);
    EXPECT_TRUE(d.isMetric());
}

TEST(Dimension, IsStandard) {
    Dimension d("cm", 1.0, true, 1);
    EXPECT_TRUE(d.isStandard());
}

TEST(Size, GetValue) {
    Size s(150.0, &cmUnit, false, 1);
    EXPECT_NEAR(150.0, s.getValue(), 1e-9);
}

TEST(Size, IsApproximate) {
    Size exact(100.0, &cmUnit, false, 1);
    Size approx(100.0, &cmUnit, true, 2);
    EXPECT_FALSE(exact.isApproximate());
    EXPECT_TRUE(approx.isApproximate());
}

TEST(Aircraft, GetName) {
    Size s(100.0, &cmUnit);
    Aircraft a("Test Aircraft", s, 1000.0, false);
    EXPECT_STREQ("Test Aircraft", a.getName());
}

TEST(Aircraft, GetValue) {
    Size s(100.0, &cmUnit);
    Aircraft a("Test", s, 5000.0, false);
    EXPECT_NEAR(5000.0, a.getValue(), 1e-9);
}

TEST(Aircraft, IsCertified) {
    Size s(100.0, &cmUnit);
    Aircraft a("Test", s, 1000.0, false);
    EXPECT_FALSE(a.isCertified());
    a.certify();
    EXPECT_TRUE(a.isCertified());
}

TEST(Aircraft, SetInsuranceValue) {
    Size s(100.0, &cmUnit);
    Aircraft a("Test", s, 1000.0, false);
    a.setInsuranceValue(5000.0);
    EXPECT_FALSE(a.isFragile());
}

TEST(Aircraft, GetYear) {
    Size s(100.0, &cmUnit);
    Aircraft a("Test", s, 1000.0, false);
    EXPECT_EQ(0, a.getYear());
}

TEST(Aircraft, GetManufacturer) {
    Size s(100.0, &cmUnit);
    Aircraft a("Test", s, 1000.0, false);
    EXPECT_STREQ("Unknown", a.getManufacturer());
}

TEST(AirlineTool, GetName) {
    Seat seat("Test Seat", true, 50, 1);
    EXPECT_STREQ("Test Seat", seat.getName());
}

TEST(Seat, GetWidth) {
    Seat seat("Test", true, 75, 1);
    EXPECT_EQ(75, seat.getWidth());
}

TEST(Seat, RemoveProtection) {
    Seat seat("Test", true, 50, 1);
    EXPECT_TRUE(seat.canProtect());
    seat.removeProtection();
    EXPECT_FALSE(seat.canProtect());
}

TEST(CabinLighting, IsLED) {
    CabinLighting led("LED", true, false, 1);
    CabinLighting nonLED("NonLED", false, false, 2);
    EXPECT_TRUE(led.isLED());
    EXPECT_FALSE(nonLED.isLED());
}

TEST(SecurityCamera, GetAngle) {
    SecurityCamera cam("Test", 120.0, false, false);
    EXPECT_NEAR(120.0, cam.getAngle(), 1e-9);
}

TEST(Gate, CheckHasCover) {
    Gate gateWithCover("Gate1", 5.0, true, false);
    Gate gateWithoutCover("Gate2", 3.0, false, false);
    EXPECT_TRUE(gateWithCover.checkHasCover());
    EXPECT_FALSE(gateWithoutCover.checkHasCover());
}

TEST(Timer, GetElapsed) {
    Timer timer(100, false, 0, 1);
    timer.start(300);
    timer.tick(50);
    EXPECT_EQ(50, timer.getElapsed());
}

TEST(Timer, IsRunning) {
    Timer timer(0, false, 0, 1);
    EXPECT_FALSE(timer.isRunning());
    timer.start(100);
    EXPECT_TRUE(timer.isRunning());
    timer.tick(100);
    EXPECT_FALSE(timer.isRunning());
}

TEST(MaintenanceKit, IsEquipped) {
    MaintenanceKit kit("Test", false);
    EXPECT_FALSE(kit.isEquipped());
    kit.equip();
    EXPECT_TRUE(kit.isEquipped());
}

TEST(CleaningKit, GetId) {
    CleaningKit kit("Test", 5);
    EXPECT_EQ(5, kit.getId());
}

TEST(ConditionProfile, GetDuration) {
    ConditionProfile profile(25.0, 30.0, 120, true);
    EXPECT_EQ(120, profile.getDuration());
}

TEST(CabinClimateControl, GetHumidity) {
    CabinClimateControl climate(50.0, false, true);
    EXPECT_NEAR(50.0, climate.getHumidity(), 1e-9);
}

TEST(CabinClimateControl, GetTargetHumidity) {
    CabinClimateControl climate(50.0, false, true);
    climate.setConditions(20.0, 10);
    EXPECT_NEAR(50.0, climate.getHumidity(), 1e-9);
}

TEST(SecuritySystem, IsOn) {
    SecuritySystem security(6, 0, true, true);
    EXPECT_TRUE(security.isOn());
    SecuritySystem securityOff(6, 0, true, false);
    EXPECT_FALSE(securityOff.isOn());
}

TEST(Passenger, GetName) {
    Passenger p("John Doe", 2, true);
    EXPECT_STREQ("John Doe", p.getName());
}

TEST(Passenger, GetVisitDuration) {
    Passenger p("Test", 2, true);
    EXPECT_NEAR(0.0, p.getVisitDuration(), 1e-9);
    Aircraft a = makeAircraft("Test", 100.0);
    p.viewAircraft(&a);
    EXPECT_NEAR(5.0, p.getVisitDuration(), 1e-9);
}

TEST(AirlineMenu, GetFlightCount) {
    AirlineMenu menu;
    EXPECT_EQ(0, menu.getFlightCount());
    
    Aircraft a1 = makeAircraft("A1", 100.0);
    Aircraft a2 = makeAircraft("A2", 100.0);
    Seat seat("Seat", true, 50, 1);
    
    PassengerFlight flight("Test Flight", &a1, &a2, &seat);
    menu.addFlight(&flight);
    EXPECT_EQ(1, menu.getFlightCount());
}

TEST(AirlineMenu, GetCurrentPassenger) {
    AirlineMenu menu;
    EXPECT_EQ(nullptr, menu.getCurrentPassenger());
    
    Passenger p("Test", 2, true);
    menu.setPassenger(&p);
    EXPECT_EQ(&p, menu.getCurrentPassenger());
}