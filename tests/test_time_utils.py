"""Unit tests for time utilities."""
import pytest
from datetime import time, date, datetime

from bot.utils.time_utils import (
    parse_time,
    format_time,
    format_time_range,
    is_valid_time_range,
    calculate_optimal_time,
    get_day_name,
    get_day_date,
    format_date,
    get_week_start,
)


class TestParseTime:
    """Tests for parse_time function."""

    def test_parse_valid_time(self):
        """Test parsing valid time strings."""
        assert parse_time("18:00") == time(18, 0)
        assert parse_time("09:30") == time(9, 30)
        assert parse_time("00:00") == time(0, 0)
        assert parse_time("23:59") == time(23, 59)

    def test_parse_time_single_digit_hour(self):
        """Test parsing time with single digit hour."""
        assert parse_time("9:00") == time(9, 0)

    def test_parse_time_24_as_midnight(self):
        """Test that 24:00 is treated as 00:00."""
        assert parse_time("24:00") == time(0, 0)

    def test_parse_invalid_time(self):
        """Test parsing invalid time strings."""
        assert parse_time("invalid") is None
        assert parse_time("25:00") is None  # Invalid hour
        assert parse_time("12:60") is None  # Invalid minute
        assert parse_time("") is None

    def test_parse_time_without_minutes(self):
        """Test that time without minutes defaults to :00."""
        assert parse_time("12") == time(12, 0)
        assert parse_time("18") == time(18, 0)

    def test_parse_time_edge_cases(self):
        """Test edge cases."""
        assert parse_time("00:00") == time(0, 0)
        assert parse_time("23:59") == time(23, 59)


class TestFormatTime:
    """Tests for format_time function."""

    def test_format_time(self):
        """Test time formatting."""
        assert format_time(time(18, 0)) == "18:00"
        assert format_time(time(9, 30)) == "09:30"
        assert format_time(time(0, 0)) == "00:00"

    def test_format_time_range(self):
        """Test time range formatting."""
        assert format_time_range(time(18, 0), time(22, 0)) == "18:00-22:00"
        assert format_time_range(time(10, 0), time(0, 0)) == "10:00-00:00"


class TestIsValidTimeRange:
    """Tests for is_valid_time_range function."""

    def test_valid_ranges(self):
        """Test valid time ranges."""
        assert is_valid_time_range(time(18, 0), time(22, 0)) is True
        assert is_valid_time_range(time(10, 0), time(11, 0)) is True
        assert is_valid_time_range(time(10, 0), time(0, 0)) is True  # Until midnight

    def test_invalid_ranges(self):
        """Test invalid time ranges."""
        assert is_valid_time_range(time(22, 0), time(18, 0)) is False  # End before start
        assert is_valid_time_range(time(18, 0), time(18, 0)) is False  # Same time

    def test_midnight_edge_case(self):
        """Test that 00:00 as end time means midnight (valid)."""
        assert is_valid_time_range(time(22, 0), time(0, 0)) is True
        assert is_valid_time_range(time(23, 0), time(0, 0)) is True


class TestCalculateOptimalTime:
    """Tests for calculate_optimal_time function."""

    def test_single_booking(self):
        """Test with single booking."""

        class MockBooking:
            def __init__(self, time_from, time_to, status="confirmed"):
                self.time_from = time_from
                self.time_to = time_to
                self.status = status

        bookings = [MockBooking(time(18, 0), time(22, 0))]
        result = calculate_optimal_time(bookings)
        assert result == (time(18, 0), time(22, 0))

    def test_multiple_bookings_with_overlap(self):
        """Test with multiple overlapping bookings."""

        class MockBooking:
            def __init__(self, time_from, time_to, status="confirmed"):
                self.time_from = time_from
                self.time_to = time_to
                self.status = status

        bookings = [
            MockBooking(time(18, 0), time(22, 0)),
            MockBooking(time(19, 0), time(23, 0)),
            MockBooking(time(17, 0), time(21, 0)),
        ]
        result = calculate_optimal_time(bookings)
        # Optimal: latest start (19:00) to earliest end (21:00)
        assert result == (time(19, 0), time(21, 0))

    def test_no_overlap(self):
        """Test when there's no overlapping time."""

        class MockBooking:
            def __init__(self, time_from, time_to, status="confirmed"):
                self.time_from = time_from
                self.time_to = time_to
                self.status = status

        bookings = [
            MockBooking(time(18, 0), time(19, 0)),
            MockBooking(time(20, 0), time(22, 0)),
        ]
        result = calculate_optimal_time(bookings)
        assert result is None  # No common time

    def test_empty_bookings(self):
        """Test with empty bookings list."""
        assert calculate_optimal_time([]) is None

    def test_only_waitlist_bookings(self):
        """Test that waitlist bookings are ignored."""

        class MockBooking:
            def __init__(self, time_from, time_to, status="confirmed"):
                self.time_from = time_from
                self.time_to = time_to
                self.status = status

        bookings = [
            MockBooking(time(18, 0), time(22, 0), status="waitlist"),
        ]
        result = calculate_optimal_time(bookings)
        assert result is None

    def test_midnight_end_time(self):
        """Test with midnight (00:00) as end time."""

        class MockBooking:
            def __init__(self, time_from, time_to, status="confirmed"):
                self.time_from = time_from
                self.time_to = time_to
                self.status = status

        bookings = [
            MockBooking(time(22, 0), time(0, 0)),  # 22:00-00:00
            MockBooking(time(21, 0), time(23, 0)),
        ]
        result = calculate_optimal_time(bookings)
        assert result == (time(22, 0), time(23, 0))

    def test_optimal_time_ends_at_midnight(self):
        """Test when optimal time ends at midnight (all bookings end at 00:00)."""

        class MockBooking:
            def __init__(self, time_from, time_to, status="confirmed"):
                self.time_from = time_from
                self.time_to = time_to
                self.status = status

        bookings = [
            MockBooking(time(20, 0), time(0, 0)),  # 20:00-00:00
            MockBooking(time(22, 0), time(0, 0)),  # 22:00-00:00
        ]
        result = calculate_optimal_time(bookings)
        # Latest start is 22:00, earliest end is 00:00 (midnight)
        assert result == (time(22, 0), time(0, 0))


class TestDayFunctions:
    """Tests for day-related functions."""

    def test_get_day_name(self):
        """Test Ukrainian day names."""
        assert get_day_name("saturday") == "Субота"
        assert get_day_name("sunday") == "Неділя"
        assert get_day_name("unknown") == "unknown"

    def test_get_day_date(self):
        """Test getting date for a day of week."""
        week_start = date(2024, 2, 5)  # Monday
        assert get_day_date("saturday", week_start) == date(2024, 2, 10)
        assert get_day_date("sunday", week_start) == date(2024, 2, 11)

    def test_format_date(self):
        """Test Ukrainian date formatting."""
        assert format_date(date(2024, 2, 10)) == "10 лютого"
        assert format_date(date(2024, 1, 1)) == "1 січня"
        assert format_date(date(2024, 12, 31)) == "31 грудня"


class TestGetWeekStart:
    """Tests for get_week_start function."""

    def test_week_start_from_monday(self):
        """Test getting week start from Monday."""
        import pytz
        tz = pytz.timezone("Europe/Warsaw")
        dt = datetime(2024, 2, 5, 12, 0, tzinfo=tz)  # Monday
        assert get_week_start(dt) == date(2024, 2, 5)

    def test_week_start_from_sunday(self):
        """Test getting week start from Sunday."""
        import pytz
        tz = pytz.timezone("Europe/Warsaw")
        dt = datetime(2024, 2, 11, 12, 0, tzinfo=tz)  # Sunday
        assert get_week_start(dt) == date(2024, 2, 5)

    def test_week_start_from_wednesday(self):
        """Test getting week start from Wednesday."""
        import pytz
        tz = pytz.timezone("Europe/Warsaw")
        dt = datetime(2024, 2, 7, 12, 0, tzinfo=tz)  # Wednesday
        assert get_week_start(dt) == date(2024, 2, 5)
