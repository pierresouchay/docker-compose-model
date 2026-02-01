"""Tests for Go duration parsing."""

from datetime import timedelta

import pytest
from pydantic import BaseModel, ValidationError

from dcm.duration import GoDuration


def test_parse_seconds():
    """Test parsing seconds."""
    assert GoDuration.parse_go_duration("5s") == timedelta(seconds=5)
    assert GoDuration.parse_go_duration("1s") == timedelta(seconds=1)
    assert GoDuration.parse_go_duration("30s") == timedelta(seconds=30)


def test_parse_milliseconds():
    """Test parsing milliseconds."""
    assert GoDuration.parse_go_duration("100ms") == timedelta(milliseconds=100)
    assert GoDuration.parse_go_duration("500ms") == timedelta(milliseconds=500)
    assert GoDuration.parse_go_duration("1ms") == timedelta(milliseconds=1)


def test_parse_microseconds():
    """Test parsing microseconds."""
    assert GoDuration.parse_go_duration("100us") == timedelta(microseconds=100)
    assert GoDuration.parse_go_duration("500µs") == timedelta(microseconds=500)


def test_parse_nanoseconds():
    """Test parsing nanoseconds."""
    # Python timedelta can handle nanoseconds, but they're stored as microseconds
    result = GoDuration.parse_go_duration("1000ns")
    assert result == timedelta(microseconds=1)


def test_parse_minutes():
    """Test parsing minutes."""
    assert GoDuration.parse_go_duration("2m") == timedelta(minutes=2)
    assert GoDuration.parse_go_duration("30m") == timedelta(minutes=30)


def test_parse_hours():
    """Test parsing hours."""
    assert GoDuration.parse_go_duration("1h") == timedelta(hours=1)
    assert GoDuration.parse_go_duration("24h") == timedelta(hours=24)


def test_parse_combined():
    """Test parsing combined duration units."""
    assert GoDuration.parse_go_duration("1h30m") == timedelta(hours=1, minutes=30)
    assert GoDuration.parse_go_duration("1h30m45s") == timedelta(
        hours=1, minutes=30, seconds=45
    )
    assert GoDuration.parse_go_duration("2m30s") == timedelta(minutes=2, seconds=30)
    assert GoDuration.parse_go_duration("1h30m45s100ms") == timedelta(
        hours=1, minutes=30, seconds=45, milliseconds=100
    )


def test_parse_decimal():
    """Test parsing decimal values."""
    assert GoDuration.parse_go_duration("1.5s") == timedelta(seconds=1.5)
    assert GoDuration.parse_go_duration("2.5m") == timedelta(minutes=2.5)
    assert GoDuration.parse_go_duration("0.5h") == timedelta(hours=0.5)


def test_parse_invalid():
    """Test parsing invalid duration strings."""
    with pytest.raises(ValueError, match="Invalid Go duration format"):
        GoDuration.parse_go_duration("invalid")

    with pytest.raises(ValueError, match="Invalid Go duration format"):
        GoDuration.parse_go_duration("5x")


def test_parse_empty():
    """Test parsing empty string."""
    with pytest.raises(ValueError, match="Duration string cannot be empty"):
        GoDuration.parse_go_duration("   ")


def test_parse_non_string():
    """Test parsing non-string input."""
    with pytest.raises(ValueError, match="Duration must be a string"):
        GoDuration.parse_go_duration(123)  # type: ignore


def test_pydantic_integration():
    """Test integration with Pydantic models."""

    class TestModel(BaseModel):
        duration: GoDuration

    # Test with valid duration string
    model = TestModel(duration="5s")
    assert model.duration == timedelta(seconds=5)

    # Test with timedelta
    model = TestModel(duration=timedelta(seconds=10))
    assert model.duration == timedelta(seconds=10)

    # Test with invalid input
    with pytest.raises(ValidationError):
        TestModel(duration="invalid")


def test_pydantic_integration_complex():
    """Test Pydantic integration with complex duration strings."""

    class TestModel(BaseModel):
        interval: GoDuration
        timeout: GoDuration
        start_period: GoDuration

    model = TestModel(
        interval="30s",
        timeout="5s",
        start_period="1m",
    )

    assert model.interval == timedelta(seconds=30)
    assert model.timeout == timedelta(seconds=5)
    assert model.start_period == timedelta(minutes=1)


def test_healthcheck_scenario():
    """Test real-world healthcheck scenario from docker-compose."""

    class Healthcheck(BaseModel):
        interval: GoDuration
        timeout: GoDuration
        retries: int

    hc = Healthcheck(
        interval="5s",
        timeout="3s",
        retries=36,
    )

    assert hc.interval == timedelta(seconds=5)
    assert hc.timeout == timedelta(seconds=3)
    assert hc.retries == 36
