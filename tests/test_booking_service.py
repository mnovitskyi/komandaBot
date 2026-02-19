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


class TestSlotsInfo:
    """Tests for slots info functionality."""

    async def test_get_slots_info_for_day(self, db_session, games, time_range):
        """Test getting slots info for a specific day."""
        service = BookingService(db_session)

        # Create session and add bookings
        session = await service.create_session(games["pubg"], 123456789, "saturday")
        await service.book(session, 1001, "user1", time_range["time_from"], time_range["time_to"])

        session = await service.get_session_by_id(session.id)
        await service.book(session, 1002, "user2", time_range["time_from"], time_range["time_to"])

        # Get slots info for saturday
        slots_info = await service.get_slots_info(123456789, "saturday")

        assert "PUBG" in slots_info
        assert slots_info["PUBG"] == (2, 4)  # 2 booked, 4 max

    async def test_get_slots_info_no_session(self, db_session, games):
        """Test getting slots info when no session exists."""
        service = BookingService(db_session)

        slots_info = await service.get_slots_info(123456789, "saturday")

        assert "PUBG" in slots_info
        assert slots_info["PUBG"] == (0, 4)  # 0 booked, 4 max

    async def test_get_slots_info_combined_days(self, db_session, games, time_range):
        """Test getting combined slots info across both days."""
        service = BookingService(db_session)

        # Create sessions for both days
        sat_session = await service.create_session(games["pubg"], 123456789, "saturday")
        await service.book(sat_session, 1001, "user1", time_range["time_from"], time_range["time_to"])

        sun_session = await service.create_session(games["pubg"], 123456789, "sunday")
        await service.book(sun_session, 1002, "user2", time_range["time_from"], time_range["time_to"])
        sun_session = await service.get_session_by_id(sun_session.id)
        await service.book(sun_session, 1003, "user3", time_range["time_from"], time_range["time_to"])

        # Get combined slots info (no day specified)
        slots_info = await service.get_slots_info(123456789)

        assert "PUBG" in slots_info
        assert slots_info["PUBG"] == (3, 4)  # 3 total booked across both days


class TestMessageFormatting:
    """Tests for session message formatting."""

    async def test_format_session_message_empty(self, db_session, games):
        """Test formatting empty session."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        session = await service.get_session_by_id(session.id)

        message = service.format_session_message(session)

        assert "PUBG" in message
        assert "Субота" in message
        assert "Поки що немає бронювань" in message

    async def test_format_session_message_with_bookings(self, db_session, games, time_range):
        """Test formatting session with bookings."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        session_id = session.id  # Store ID before potential expiry
        await service.book(session, 1001, "user1", time_range["time_from"], time_range["time_to"])

        # Expire cached session to force reload with fresh bookings
        db_session.expire_all()
        session = await service.get_session_by_id(session_id)
        message = service.format_session_message(session)

        assert "[user1](tg://user?id=1001)" in message
        assert "18:00-22:00" in message
        assert "Слоти (1/4)" in message

    async def test_format_session_message_with_waitlist(self, db_session, games, time_range):
        """Test formatting session with waitlist."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        session_id = session.id  # Store ID before potential expiry

        # Fill all slots and add to waitlist
        for i in range(5):
            db_session.expire_all()
            session = await service.get_session_by_id(session_id)
            await service.book(session, 1000 + i, f"user{i}", time_range["time_from"], time_range["time_to"])

        db_session.expire_all()
        session = await service.get_session_by_id(session_id)
        message = service.format_session_message(session)

        assert "Черга:" in message
        assert "[user4](tg://user?id=1004)" in message  # 5th user in waitlist

    async def test_format_session_message_optimal_time(self, db_session, games):
        """Test formatting session shows optimal time."""
        from datetime import time
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        session_id = session.id  # Store ID before potential expiry
        await service.book(session, 1001, "user1", time(18, 0), time(22, 0))

        db_session.expire_all()
        session = await service.get_session_by_id(session_id)
        await service.book(session, 1002, "user2", time(19, 0), time(23, 0))

        db_session.expire_all()
        session = await service.get_session_by_id(session_id)
        message = service.format_session_message(session)

        assert "Оптимальний час:" in message
        assert "19:00-22:00" in message

    async def test_format_session_message_no_common_time(self, db_session, games):
        """Test formatting session when no common time exists."""
        from datetime import time
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        session_id = session.id  # Store ID before potential expiry
        await service.book(session, 1001, "user1", time(18, 0), time(19, 0))

        db_session.expire_all()
        session = await service.get_session_by_id(session_id)
        await service.book(session, 1002, "user2", time(20, 0), time(21, 0))

        db_session.expire_all()
        session = await service.get_session_by_id(session_id)
        message = service.format_session_message(session)

        assert "Немає спільного часу" in message


class TestGameOperations:
    """Tests for game-related operations."""

    async def test_get_games(self, db_session, games):
        """Test getting all games."""
        service = BookingService(db_session)

        all_games = await service.get_games()

        assert len(all_games) == 1
        assert all_games[0].name == "PUBG"


class TestGroupStats:
    """Tests for group statistics."""

    async def test_get_group_stats(self, db_session, games, time_range):
        """Test getting group statistics."""
        service = BookingService(db_session)

        # Create bookings and play history
        session = await service.create_session(games["pubg"], 123456789, "saturday")
        await service.book(session, 1001, "user1", time_range["time_from"], time_range["time_to"])

        session = await service.get_session_by_id(session.id)
        await service.book(session, 1002, "user2", time_range["time_from"], time_range["time_to"])

        # Close session to mark as played
        await service.close_all_sessions(123456789)

        stats = await service.get_group_stats()

        assert len(stats) == 2
        # Stats should be sorted by played count
        assert stats[0]["username"] in ["user1", "user2"]
        assert stats[0]["played"] == 1


class TestAllOpenSessions:
    """Tests for getting all open sessions."""

    async def test_get_all_open_sessions(self, db_session, games):
        """Test getting all open sessions across chats."""
        service = BookingService(db_session)

        # Create sessions in different chats
        await service.create_session(games["pubg"], 111111111, "saturday")
        await service.create_session(games["pubg"], 222222222, "saturday")
        await service.create_session(games["pubg"], 111111111, "sunday")

        sessions = await service.get_all_open_sessions()

        assert len(sessions) == 3


class TestCancelAndRebook:
    """Tests for the bug where cancelled slot stays blocked."""

    async def test_new_booking_confirmed_after_cancel_no_waitlist(self, db_session, games, full_session, time_range):
        """Test that new booking gets confirmed when slot freed by cancel (no waitlist)."""
        service = BookingService(db_session)

        # Cancel one confirmed user (no one on waitlist)
        full_session = await service.get_session_by_id(full_session.id)
        result = await service.cancel(
            session=full_session,
            user_id=1001,
            username="user1",
        )
        assert result.success is True
        assert result.promoted_user is None  # No waitlist to promote

        # New user books - should be confirmed, not waitlisted
        full_session = await service.get_session_by_id(full_session.id)
        result = await service.book(
            session=full_session,
            user_id=8888,
            username="new_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is True
        assert result.is_waitlist is False
        assert result.booking.status == "confirmed"

    async def test_multiple_cancels_then_rebook(self, db_session, games, full_session, time_range):
        """Test booking after multiple cancellations still gets confirmed."""
        service = BookingService(db_session)

        # Cancel 2 confirmed users
        for user_id in [1001, 1002]:
            full_session = await service.get_session_by_id(full_session.id)
            await service.cancel(
                session=full_session,
                user_id=user_id,
                username=f"user{user_id - 1000}",
            )

        # New user books - should be confirmed (only 2/4 slots taken)
        full_session = await service.get_session_by_id(full_session.id)
        result = await service.book(
            session=full_session,
            user_id=8888,
            username="new_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is True
        assert result.is_waitlist is False
        assert result.booking.status == "confirmed"

    async def test_cancel_and_rebook_goes_to_waitlist_when_actually_full(self, db_session, games, full_session, time_range):
        """Test that waitlist still works correctly when all slots are truly full."""
        service = BookingService(db_session)

        # All 4 slots full, no cancel - new booking should be waitlisted
        full_session = await service.get_session_by_id(full_session.id)
        result = await service.book(
            session=full_session,
            user_id=8888,
            username="new_user",
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        assert result.success is True
        assert result.is_waitlist is True
        assert result.booking.status == "waitlist"


class TestEditBooking:
    """Tests for editing booking times."""

    async def test_edit_booking_success(self, db_session, games, open_session, user_data, time_range):
        """Test successful booking edit."""
        service = BookingService(db_session)

        await service.book(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        open_session = await service.get_session_by_id(open_session.id)
        result = await service.edit_booking(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time(19, 0),
            time_to=time(23, 0),
        )

        assert result.success is True
        assert "оновлено" in result.message

        # Verify times were updated
        booking_repo = BookingRepository(db_session)
        booking = await booking_repo.get_user_booking(open_session.id, user_data["user_id"])
        assert booking.time_from == time(19, 0)
        assert booking.time_to == time(23, 0)

    async def test_edit_booking_no_existing(self, db_session, games, open_session, user_data):
        """Test editing when no booking exists."""
        service = BookingService(db_session)

        result = await service.edit_booking(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time(19, 0),
            time_to=time(23, 0),
        )

        assert result.success is False
        assert "немає бронювання" in result.message

    async def test_edit_preserves_position_and_status(self, db_session, games, open_session, time_range):
        """Test that editing preserves position and status."""
        service = BookingService(db_session)

        # Create two bookings
        await service.book(open_session, 1001, "user1", time_range["time_from"], time_range["time_to"])
        open_session = await service.get_session_by_id(open_session.id)
        await service.book(open_session, 1002, "user2", time_range["time_from"], time_range["time_to"])
        open_session = await service.get_session_by_id(open_session.id)

        # Edit user1's times
        await service.edit_booking(open_session, 1001, "user1", time(20, 0), time(23, 0))

        booking_repo = BookingRepository(db_session)
        booking = await booking_repo.get_user_booking(open_session.id, 1001)
        assert booking.position == 1
        assert booking.status == "confirmed"

    async def test_edit_does_not_add_cancelled_history(self, db_session, games, open_session, user_data, time_range):
        """Test that editing does not log 'cancelled' or extra 'booked' actions."""
        service = BookingService(db_session)

        await service.book(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time_range["time_from"],
            time_to=time_range["time_to"],
        )

        open_session = await service.get_session_by_id(open_session.id)

        await service.edit_booking(
            session=open_session,
            user_id=user_data["user_id"],
            username=user_data["username"],
            time_from=time(19, 0),
            time_to=time(23, 0),
        )

        stats = await service.get_user_stats(user_data["user_id"])
        assert stats["total_bookings"] == 1       # only the original booking
        assert stats["total_cancellations"] == 0   # no cancellation logged


class TestMessageIdUpdate:
    """Tests for message ID updates."""

    async def test_update_message_id(self, db_session, games):
        """Test updating session message ID."""
        service = BookingService(db_session)

        session = await service.create_session(games["pubg"], 123456789, "saturday")
        session_id = session.id

        # Update message ID
        await service.update_message_id(session_id, 999888777)

        # Verify the update
        db_session.expire_all()
        updated_session = await service.get_session_by_id(session_id)

        assert updated_session.message_id == 999888777
