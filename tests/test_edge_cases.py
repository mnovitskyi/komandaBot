"""Edge case and boundary condition tests."""
import pytest
from datetime import time, date

from bot.services.booking import BookingService
from bot.database.models import Session, Booking
from bot.utils.time_utils import (
    parse_time,
    is_valid_time_range,
    calculate_optimal_time,
)


pytestmark = pytest.mark.asyncio


class TestTimeEdgeCases:
    """Edge cases for time handling."""

    def test_midnight_booking(self):
        """Test booking until midnight (00:00)."""
        time_from = parse_time("22:00")
        time_to = parse_time("00:00")

        assert time_from == time(22, 0)
        assert time_to == time(0, 0)
        assert is_valid_time_range(time_from, time_to) is True

    def test_very_short_booking(self):
        """Test very short booking (1 hour)."""
        assert is_valid_time_range(time(18, 0), time(19, 0)) is True

    def test_all_day_booking(self):
        """Test booking from morning to midnight."""
        assert is_valid_time_range(time(10, 0), time(0, 0)) is True

    def test_boundary_times(self):
        """Test boundary time values."""
        assert parse_time("00:00") == time(0, 0)
        assert parse_time("23:59") == time(23, 59)
        assert parse_time("24:00") == time(0, 0)  # Treated as midnight


class TestOptimalTimeEdgeCases:
    """Edge cases for optimal time calculation."""

    class MockBooking:
        def __init__(self, time_from, time_to, status="confirmed"):
            self.time_from = time_from
            self.time_to = time_to
            self.status = status

    def test_exact_overlap(self):
        """Test when all bookings have exact same times."""
        bookings = [
            self.MockBooking(time(18, 0), time(22, 0)),
            self.MockBooking(time(18, 0), time(22, 0)),
            self.MockBooking(time(18, 0), time(22, 0)),
        ]
        result = calculate_optimal_time(bookings)
        assert result == (time(18, 0), time(22, 0))

    def test_one_minute_overlap(self):
        """Test with only 1 hour overlap."""
        bookings = [
            self.MockBooking(time(18, 0), time(20, 0)),
            self.MockBooking(time(19, 0), time(21, 0)),
        ]
        result = calculate_optimal_time(bookings)
        assert result == (time(19, 0), time(20, 0))

    def test_adjacent_no_overlap(self):
        """Test adjacent time slots with no overlap."""
        bookings = [
            self.MockBooking(time(18, 0), time(19, 0)),
            self.MockBooking(time(19, 0), time(20, 0)),
        ]
        result = calculate_optimal_time(bookings)
        # 19:00 is both end of first and start of second, so no overlap
        assert result is None

    def test_mixed_statuses(self):
        """Test that only confirmed bookings are considered."""
        bookings = [
            self.MockBooking(time(10, 0), time(12, 0), "confirmed"),
            self.MockBooking(time(20, 0), time(22, 0), "waitlist"),
            self.MockBooking(time(11, 0), time(13, 0), "confirmed"),
        ]
        result = calculate_optimal_time(bookings)
        # Should only consider confirmed (10-12 and 11-13), optimal is 11-12
        assert result == (time(11, 0), time(12, 0))


class TestSlotBoundaries:
    """Tests for slot capacity boundaries."""

    async def test_exactly_max_slots(self, db_session, games, time_range):
        """Test filling exactly max slots (no waitlist)."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")

        # Fill exactly 4 slots (PUBG max)
        for i in range(4):
            session = await service.get_session_by_id(session.id)
            result = await service.book(
                session=session,
                user_id=1000 + i,
                username=f"user{i}",
                time_from=time_range["time_from"],
                time_to=time_range["time_to"],
            )
            assert result.success is True
            assert result.is_waitlist is False
            assert result.booking.status == "confirmed"

    async def test_one_over_max_slots(self, db_session, games, time_range):
        """Test that 5th booking for PUBG (max 4) goes to waitlist."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")

        # Fill 4 slots
        for i in range(4):
            session = await service.get_session_by_id(session.id)
            await service.book(
                session=session,
                user_id=1000 + i,
                username=f"user{i}",
                time_from=time_range["time_from"],
                time_to=time_range["time_to"],
            )

        # 5th booking should go to waitlist
        session = await service.get_session_by_id(session.id)
        result = await service.book(
            session=session,
            user_id=2000,
            username="waitlist_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is True
        assert result.is_waitlist is True
        assert result.booking.position == 5

    async def test_cs_has_5_slots(self, db_session, games, time_range):
        """Test that CS has 5 slots (not 4 like PUBG)."""
        service = BookingService(db_session)

        session = await service.create_session(games["cs"], 123456789, "saturday")

        # Fill 5 slots for CS
        for i in range(5):
            session = await service.get_session_by_id(session.id)
            result = await service.book(
                session=session,
                user_id=1000 + i,
                username=f"user{i}",
                time_from=time_range["time_from"],
                time_to=time_range["time_to"],
            )
            assert result.is_waitlist is False

        # 6th should be waitlist
        session = await service.get_session_by_id(session.id)
        result = await service.book(
            session=session,
            user_id=2000,
            username="waitlist_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )
        assert result.is_waitlist is True


class TestConcurrentOperations:
    """Tests for concurrent-like operations."""

    async def test_cancel_and_rebook(self, db_session, games, time_range):
        """Test cancelling and rebooking."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")

        # Book
        await service.book(session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        # Cancel
        session = await service.get_session_by_id(session.id)
        await service.cancel(session, 9999, "testuser")

        # Rebook
        session = await service.get_session_by_id(session.id)
        result = await service.book(session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        assert result.success is True

    async def test_multiple_cancellations_waitlist_promotion(self, db_session, games, time_range):
        """Test multiple cancellations with waitlist promotions."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")

        # Fill 4 slots + 2 waitlist
        for i in range(6):
            session = await service.get_session_by_id(session.id)
            await service.book(session, 1000 + i, f"user{i}", time_range["time_from"], time_range["time_to"])

        # Cancel 2 confirmed users
        session = await service.get_session_by_id(session.id)
        result1 = await service.cancel(session, 1000, "user0")
        assert result1.promoted_user is not None

        session = await service.get_session_by_id(session.id)
        result2 = await service.cancel(session, 1001, "user1")
        assert result2.promoted_user is not None


class TestDataIntegrity:
    """Tests for data integrity."""

    async def test_booking_history_on_book(self, db_session, games, time_range):
        """Test that booking creates history entry."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        await service.book(session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        stats = await service.get_user_stats(9999)
        assert stats["total_bookings"] == 1

    async def test_booking_history_on_cancel(self, db_session, games, time_range):
        """Test that cancellation creates history entry."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        await service.book(session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        session = await service.get_session_by_id(session.id)
        await service.cancel(session, 9999, "testuser")

        stats = await service.get_user_stats(9999)
        assert stats["total_cancellations"] == 1

    async def test_played_status_on_close(self, db_session, games, time_range):
        """Test that closing session marks confirmed as played."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        await service.book(session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        await service.close_all_sessions(123456789)

        stats = await service.get_user_stats(9999)
        assert stats["total_played"] == 1


class TestInputValidation:
    """Tests for input validation edge cases."""

    def test_parse_time_with_spaces(self):
        """Test time strings with spaces - int() handles some whitespace."""
        # Leading/trailing spaces in parts are handled by int()
        assert parse_time(" 18:00") == time(18, 0)
        assert parse_time("18:00 ") == time(18, 0)
        # Space before colon is also handled by int()
        assert parse_time("18 :00") == time(18, 0)

    def test_parse_time_special_characters(self):
        """Test special characters in time string."""
        # Newlines are stripped by int()
        assert parse_time("18:00\n") == time(18, 0)
        # Semicolon breaks parsing
        assert parse_time("18:00;") is None

    def test_empty_username_handling(self, db_session, games, time_range):
        """Username should never be empty (handler should use first_name as fallback)."""
        # This is handled at handler level, not service level
        # Service accepts whatever username is passed
        pass


class TestWeekBoundaries:
    """Tests for week boundary handling."""

    async def test_different_weeks_different_sessions(self, db_session, games, time_range):
        """Test that different weeks have different sessions."""
        service = BookingService(db_session)

        # Create session for week 1
        session1 = await service.create_session(
            games["pubg"],
            123456789,
            "saturday",
            week_start=date(2024, 2, 5),
        )

        # Create session for week 2
        session2 = await service.create_session(
            games["pubg"],
            123456789,
            "saturday",
            week_start=date(2024, 2, 12),
        )

        assert session1.id != session2.id

    async def test_same_week_same_session(self, db_session, games, time_range):
        """Test that same week returns same session."""
        service = BookingService(db_session)

        week_start = date(2024, 2, 5)

        session1 = await service.create_session(
            games["pubg"], 123456789, "saturday", week_start=week_start
        )

        session2 = await service.create_session(
            games["pubg"], 123456789, "saturday", week_start=week_start
        )

        assert session1.id == session2.id
