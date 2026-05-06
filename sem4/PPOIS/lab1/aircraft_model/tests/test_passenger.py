"""Тесты для модуля Passenger."""
import pytest
from aircraft_model import Passenger, RegistrationError, ValidationError


class TestPassengerValidation:
    """Тесты валидации Passenger."""

    def test_create_valid(self):
        p = Passenger("Пётр Петров", "PASS1234", "12A")
        assert p.full_name == "Пётр Петров"
        assert p.passport_number == "PASS1234"
        assert p.seat_number == "12A"

    def test_empty_name(self):
        with pytest.raises(ValidationError, match="full_name"):
            Passenger("", "PASS1234")

    def test_short_name(self):
        with pytest.raises(ValidationError, match="at least 3"):
            Passenger("AB", "PASS1234")

    def test_invalid_passport_format(self):
        with pytest.raises(ValidationError, match="passport"):
            Passenger("Test", "invalid!")

    def test_short_passport(self):
        with pytest.raises(ValidationError, match="between 6 and 12"):
            Passenger("Test", "P1")

    def test_invalid_seat_format(self):
        with pytest.raises(ValidationError, match="seat"):
            Passenger("Test", "PASS1234", "12Z")


class TestPassengerRegistration:
    """Тесты регистрации пассажира."""

    def test_register_with_seat(self, passenger):
        assert passenger.register_for_flight() is True
        assert passenger.is_registered is True

    def test_register_twice_fails(self, registered_passenger):
        with pytest.raises(RegistrationError, match="already registered"):
            registered_passenger.register_for_flight()

    def test_register_without_seat_fails(self):
        p = Passenger("Test", "PASS1234")
        with pytest.raises(RegistrationError, match="seat not assigned"):
            p.register_for_flight()

    def test_assign_seat(self, passenger):
        passenger.assign_seat("15C")
        assert passenger.seat_number == "15C"
