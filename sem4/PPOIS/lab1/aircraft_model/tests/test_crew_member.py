"""Тесты для модуля CrewMember."""
import pytest
from aircraft_model import CrewMember, CrewRole, CrewError, ValidationError


class TestCrewMemberValidation:
    """Тесты валидации CrewMember."""

    def test_create_valid(self):
        cm = CrewMember("Иван Иванов", CrewRole.PILOT, "PLT12345")
        assert cm.full_name == "Иван Иванов"
        assert cm.role == CrewRole.PILOT
        assert cm.license_number == "PLT12345"

    def test_empty_name(self):
        with pytest.raises(ValidationError, match="full_name"):
            CrewMember("", CrewRole.PILOT, "PLT12345")

    def test_short_name(self):
        with pytest.raises(ValidationError, match="at least 3"):
            CrewMember("AB", CrewRole.PILOT, "PLT12345")

    def test_short_license(self):
        with pytest.raises(ValidationError, match="license"):
            CrewMember("Иван Иванов", CrewRole.PILOT, "AB")


class TestCrewMemberDuty:
    """Тесты дежурства."""

    def test_start_end_duty(self, crew_member):
        assert crew_member.is_on_duty is False
        assert crew_member.start_duty() is True
        assert crew_member.is_on_duty is True
        assert crew_member.end_duty() is True
        assert crew_member.is_on_duty is False

    def test_start_duty_twice(self, crew_member):
        crew_member.start_duty()
        assert crew_member.start_duty() is False

    def test_end_duty_not_on_duty(self, crew_member):
        assert crew_member.end_duty() is False

    def test_perform_duty_on_duty(self, crew_member):
        crew_member.start_duty()
        result = crew_member.perform_duty("test")
        assert result["status"] == "completed"

    def test_perform_duty_off_duty_fails(self, crew_member):
        with pytest.raises(CrewError, match="not on duty"):
            crew_member.perform_duty("test")

    def test_can_fly_pilot(self, crew_member):
        crew_member.start_duty()
        assert crew_member.can_fly() is True

    def test_can_fly_attendant(self):
        cm = CrewMember("Test", CrewRole.FLIGHT_ATTENDANT, "FA12345")
        cm.start_duty()
        assert cm.can_fly() is False

    def test_can_fly_off_duty(self, crew_member):
        assert crew_member.can_fly() is False
