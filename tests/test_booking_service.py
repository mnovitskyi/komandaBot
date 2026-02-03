"""Tests for booking service."""
import pytest
from datetime import time, date

from bot.services.booking import BookingService
from bot.database.models import Game, Session, Booking
from bot.database.repositories import BookingRepository


pytestmark = pytest.mark.asyncio


class TestBookingCreation:
    """Tests for creating bookings."""

    async def test_create_booking_success(self, db_session, games, open_session, user_data, time_range):
        """Test successful booking creation."""
        service = BookingService(db_session)

        result = await service.book(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is True
        assert result.booking is not None
        assert result.booking.position == 1
        assert result.booking.status == "confirmed"
        assert result.is_waitlist is False

    async def test_create_booking_duplicate_user(self, db_session, games, open_session, user_data, time_range):
        """Test that user cannot book twice on same session."""
        service = BookingService(db_session)

        # First booking
        await service.book(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        # Second booking attempt
        result = await service.book(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is False
        assert "вже маєте бронювання" in result.message

    async def test_booking_positions_increment(self, db_session, games, open_session, time_range):
        """Test that booking positions increment correctly."""
        service = BookingService(db_session)

        # Create multiple bookings
        for i in range(3):
            result = await service.book(
                session=open_session,
                user_id=1000 + i,
                username=f"user{i}",
                time_from=time_range["time_from"],
                time_to=time_range["time_to"],
            )
            assert result.booking.position == i + 1


class TestWaitlist:
    """Tests for waitlist functionality."""

    async def test_booking_goes_to_waitlist_when_full(self, db_session, games, full_session, time_range):
        """Test that booking goes to waitlist when slots are full."""
        service = BookingService(db_session)

        result = await service.book(
            session=full_session,
            user_id=9999,
            username="waitlist_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is True
        assert result.is_waitlist is True
        assert result.booking.status == "waitlist"
        assert result.booking.position == 5  # 4 slots + 1

    async def test_multiple_waitlist_positions(self, db_session, games, full_session, time_range):
        """Test multiple users in waitlist."""
        service = BookingService(db_session)

        # Add 3 users to waitlist
        for i in range(3):
            result = await service.book(
                session=full_session,
                user_id=9000 + i,
                username=f"waitlist{i}",
                time_from=time_range["time_from"],
                time_to=time_range["time_to"],
            )
            assert result.is_waitlist is True
            assert result.booking.position == 5 + i  # Positions 5, 6, 7

    async def test_waitlist_promotion_on_cancel(self, db_session, games, full_session, time_range):
        """Test that first waitlist user is promoted when slot opens."""
        service = BookingService(db_session)

        # Add user to waitlist
        await service.book(
            session=full_session,
            user_id=9999,
            username="waitlist_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        # Reload session to get fresh data
        full_session = await service.get_session_by_id(full_session.id)

        # Cancel first confirmed user (user_id=1001)
        result = await service.cancel(
            session=full_session,
            user_id=1001,
            username="user1",
        )

        assert result.success is True
        assert result.promoted_user is not None
        assert result.promoted_user[0] == 9999  # user_id
        assert result.promoted_user[1] == "waitlist_user"  # username

    async def test_waitlist_positions_shift_on_promotion(self, db_session, games, full_session, time_range):
        """Test that waitlist positions shift correctly after promotion."""
        service = BookingService(db_session)

        # Add 3 users to waitlist
        for i in range(3):
            await service.book(
                session=full_session,
                user_id=9000 + i,
                username=f"waitlist{i}",
                time_from=time_range["time_from"],
                time_to=time_range["time_to"],
            )

        # Reload session
        full_session = await service.get_session_by_id(full_session.id)

        # Cancel first confirmed user
        await service.cancel(
            session=full_session,
            user_id=1001,
            username="user1",
        )

        # Check that waitlist positions shifted
        booking_repo = BookingRepository(db_session)

        # First waitlist user should now be confirmed
        booking1 = await booking_repo.get_user_booking(full_session.id, 9000)
        assert booking1.status == "confirmed"

        # Other waitlist users should have shifted positions
        booking2 = await booking_repo.get_user_booking(full_session.id, 9001)
        assert booking2.status == "waitlist"
        assert booking2.position == 5  # Was 6, now 5

        booking3 = await booking_repo.get_user_booking(full_session.id, 9002)
        assert booking3.status == "waitlist"
        assert booking3.position == 6  # Was 7, now 6


class TestCancellation:
    """Tests for booking cancellation."""

    async def test_cancel_booking_success(self, db_session, games, open_session, user_data, time_range):
        """Test successful booking cancellation."""
        service = BookingService(db_session)

        # Create booking
        await service.book(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        # Reload session
        open_session = await service.get_session_by_id(open_session.id)

        # Cancel booking
        result = await service.cancel(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
        )

        assert result.success is True
        assert "скасовано" in result.message

    async def test_cancel_nonexistent_booking(self, db_session, games, open_session, user_data):
        """Test cancelling when no booking exists."""
        service = BookingService(db_session)

        result = await service.cancel(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
        )

        assert result.success is False
        assert "немає бронювання" in result.message

    async def test_cancel_waitlist_no_promotion(self, db_session, games, full_session, time_range):
        """Test that cancelling waitlist booking doesn't trigger promotion."""
        service = BookingService(db_session)

        # Add user to waitlist
        await service.book(
            session=full_session,
            user_id=9999,
            username="waitlist_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        # Reload session
        full_session = await service.get_session_by_id(full_session.id)

        # Cancel waitlist user
        result = await service.cancel(
            session=full_session,
            user_id=9999,
            username="waitlist_user",
        )

        assert result.success is True
        assert result.promoted_user is None  # No one promoted


class TestSessionManagement:
    """Tests for session management."""

    async def test_get_session_existing(self, db_session, games):
        """Test getting existing session."""
        service = BookingService(db_session)

        # Create session first
        created_session = await service.create_session(
            game=games["pubg"],
            chat_id=123456789,
            day="saturday",
        )

        # Now get it
        session = await service.get_session(
            game=games["pubg"],
            chat_id=123456789,
            day="saturday",
        )

        assert session is not None
        assert session.id == created_session.id

    async def test_get_session_nonexistent(self, db_session, games):
        """Test getting non-existent session returns None."""
        service = BookingService(db_session)

        session = await service.get_session(
            game=games["pubg"],
            chat_id=123456789,
            day="saturday",
        )

        assert session is None

    async def test_create_session(self, db_session, games):
        """Test creating a new session."""
        service = BookingService(db_session)

        session = await service.create_session(
            game=games["pubg"],
            chat_id=123456789,
            day="saturday",
        )

        assert session is not None
        assert session.status == "open"
        assert session.day == "saturday"

    async def test_create_session_idempotent(self, db_session, games):
        """Test that creating session twice returns same session."""
        service = BookingService(db_session)

        session1 = await service.create_session(
            game=games["pubg"],
            chat_id=123456789,
            day="saturday",
        )

        session2 = await service.create_session(
            game=games["pubg"],
            chat_id=123456789,
            day="saturday",
        )

        assert session1.id == session2.id

    async def test_close_sessions(self, db_session, games):
        """Test closing all sessions."""
        service = BookingService(db_session)

        # Create sessions
        await service.create_session(games["pubg"], 123456789, "saturday")
        await service.create_session(games["pubg"], 123456789, "sunday")

        # Close all
        await service.close_all_sessions(123456789)

        # Verify closed
        sessions = await service.get_open_sessions(123456789)
        assert len(sessions) == 0


class TestUserBookings:
    """Tests for user booking queries."""

    async def test_get_user_bookings_multiple_sessions(self, db_session, games, time_range):
        """Test getting user bookings across multiple sessions."""
        service = BookingService(db_session)

        # Create sessions for both days
        sat_session = await service.create_session(games["pubg"], 123456789, "saturday")

        # Book saturday
        await service.book(sat_session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        # Create and book sunday (fresh session object)
        sun_session = await service.create_session(games["pubg"], 123456789, "sunday")
        await service.book(sun_session, 9999, "testuser", time_range["time_from"], time_range["time_to"])

        # Get user bookings
        bookings = await service.get_user_bookings(123456789, 9999)

        assert len(bookings) == 2

    async def test_get_user_bookings_different_games(self, db_session, time_range):
        """Test user can book different games on same day."""
        # Seed games in this test's session
        from bot.database.models import Game
        game1 = Game(name="GameA", max_slots=4)
        game2 = Game(name="GameB", max_slots=5)
        db_session.add_all([game1, game2])
        await db_session.commit()

        # Store IDs before they can get expired
        game1_id = game1.id
        game2_id = game2.id

        service = BookingService(db_session)

        # Create and book game 1
        g1 = await service.get_game("GameA")
        session1 = await service.create_session(g1, 555555555, "saturday")
        result1 = await service.book(session1, 8888, "testuser", time_range["time_from"], time_range["time_to"])
        assert result1.success

        # Get fresh game 2 reference after expire_all() from booking
        g2 = await service.get_game("GameB")
        session2 = await service.create_session(g2, 555555555, "saturday")
        result2 = await service.book(session2, 8888, "testuser", time_range["time_from"], time_range["time_to"])
        assert result2.success

        # Verify both bookings exist
        from bot.database.repositories import BookingRepository
        booking_repo = BookingRepository(db_session)

        # Get fresh session IDs
        s1 = await service.get_session(g1, 555555555, "saturday")
        s2 = await service.get_session(g2, 555555555, "saturday")

        booking1 = await booking_repo.get_user_booking(s1.id, 8888)
        booking2 = await booking_repo.get_user_booking(s2.id, 8888)

        assert booking1 is not None
        assert booking2 is not None
