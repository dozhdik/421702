"""Расширенные тесты для модуля Ticket."""
import pytest
from datetime import datetime, timedelta
from aircraft_model import Ticket, TicketStatus, FlightError, ValidationError


class TestTicketExtended:
    """Дополнительные тесты для Ticket."""

    def test_issue_factory_method(self):
        t = Ticket.issue("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        assert t.flight_number == "SU123"
        assert t.status == TicketStatus.BOOKED

    def test_validate_refunded_ticket(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        t.refund()
        with pytest.raises(FlightError, match="refunded"):
            t.validate()

    def test_validate_used_ticket(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        t.use()
        with pytest.raises(FlightError, match="already been used"):
            t.validate()

    def test_confirm_already_confirmed(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        t.confirm()
        assert t.confirm() is False

    def test_use_cancelled_ticket_fails(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        t.cancel()
        with pytest.raises(FlightError):
            t.use()

    def test_cancel_already_cancelled(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        t.cancel()
        assert t.cancel() is False

    def test_refund_cancelled_ticket(self):
        t = Ticket("SU123", datetime.now() + timedelta(days=1), "12A", 5000.0, "PASS1234")
        t.cancel()
        assert t.refund() is True
        assert t.status == TicketStatus.REFUNDED

    def test_properties(self):
        dt = datetime.now() + timedelta(days=1)
        t = Ticket("SU123", dt, "12A", 5000.0, "PASS1234")
        assert t.flight_number == "SU123"
        assert t.flight_datetime == dt
        assert t.seat == "12A"
        assert t.price == 5000.0
        assert t.passport_number == "PASS1234"
