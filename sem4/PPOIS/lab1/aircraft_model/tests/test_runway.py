"""Тесты для модуля Runway."""
import pytest
from aircraft_model import Runway, RunwayStatus, RunwayError, ValidationError, Aircraft


class TestRunwayValidation:
    """Тесты валидации Runway."""

    def test_create_valid(self):
        r = Runway("RWY01", 3000)
        assert r.runway_id == "RWY01"
        assert r.length == 3000
        assert r.status == RunwayStatus.FREE

    def test_empty_id(self):
        with pytest.raises(ValidationError, match="Runway ID"):
            Runway("", 3000)

    def test_short_length(self):
        with pytest.raises(ValidationError, match="at least"):
            Runway("RWY01", 100)

    def test_excessive_length(self):
        with pytest.raises(ValidationError, match="cannot exceed"):
            Runway("RWY01", 10000)


class TestRunwayOperations:
    """Тесты операций с ВПП."""

    def test_request_takeoff_success(self, runway, aircraft):
        assert runway.request_takeoff(aircraft) is True
        assert runway.status == RunwayStatus.OCCUPIED

    def test_request_takeoff_occupied(self, runway, aircraft):
        runway.request_takeoff(aircraft)
        ac2 = Aircraft("Test", "RA-TEST2", 100)
        assert runway.request_takeoff(ac2) is False
        assert runway.queue_size == 1

    def test_request_landing_success(self, runway, aircraft):
        assert runway.request_landing(aircraft) is True
        assert runway.status == RunwayStatus.OCCUPIED

    def test_release_runway(self, runway, aircraft):
        runway.request_takeoff(aircraft)
        result = runway.release()
        assert result is None
        assert runway.status == RunwayStatus.FREE

    def test_release_with_queue(self, runway, aircraft):
        ac2 = Aircraft("Test", "RA-TEST2", 100)
        runway.request_takeoff(aircraft)
        runway.request_takeoff(ac2)
        result = runway.release()
        assert result == ac2.tail_number
        assert runway.status == RunwayStatus.OCCUPIED

    def test_close_runway(self, runway):
        assert runway.close() is True
        assert runway.status == RunwayStatus.CLOSED

    def test_close_with_queue_fails(self, runway, aircraft):
        ac2 = Aircraft("Test", "RA-TEST2", 100)
        runway.request_takeoff(aircraft)
        runway.request_takeoff(ac2)
        with pytest.raises(RunwayError, match="queue"):
            runway.close()

    def test_open_runway(self, runway):
        runway.close()
        assert runway.open() is True
        assert runway.status == RunwayStatus.FREE

    def test_can_accommodate(self, runway):
        assert runway.can_accommodate(2500) is True
        assert runway.can_accommodate(3500) is False
