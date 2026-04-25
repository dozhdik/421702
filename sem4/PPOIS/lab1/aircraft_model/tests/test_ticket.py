"""Тесты для модуля Ticket."""
import pytest
from datetime import datetime, timedelta
from aircraft_model import Ticket, TicketStatus, FlightError, ValidationError


class TestTicketValidation:
    """Тесты валидации Ticket."""

    def test_create_valid(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        assert t.flight_number == "SU123"
        assert t.status == TicketStatus.BOOKED

    def test_invalid_flight_format(self):
        with pytest.raises(ValidationError, match="Flight number"):
            Ticket("INVALID", datetime.now(), "12A", 100, "PASS1234")

    def test_negative_price(self):
        with pytest.raises(ValidationError, match="negative"):
            Ticket("SU123", datetime.now(), "12A", -100, "PASS1234")


class TestTicketOperations:
    """Тесты операций с билетом."""

    def test_validate_booked_ticket(self, ticket):
        assert ticket.validate() is True

    def test_validate_cancelled_ticket_fails(self, ticket):
        ticket.cancel()
        with pytest.raises(FlightError, match="cancelled"):
            ticket.validate()

    def test_confirm_ticket(self, ticket):
        assert ticket.confirm() is True
        assert ticket.status == TicketStatus.CONFIRMED

    def test_use_ticket(self, ticket):
        ticket.confirm()
        assert ticket.use() is True
        assert ticket.status == TicketStatus.USED

    def test_cancel_ticket(self, ticket):
        assert ticket.cancel() is True
        assert ticket.status == TicketStatus.CANCELLED

    def test_refund_used_ticket_fails(self, ticket):
        ticket.use()
        assert ticket.refund() is False

    def test_is_valid(self, ticket):
        assert ticket.is_valid() is True
        ticket.cancel()
        assert ticket.is_valid() is False
