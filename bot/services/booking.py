from datetime import time, date
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Session, Booking, Game
from bot.database.repositories import (
    GameRepository,
    SessionRepository,
    BookingRepository,
    BookingHistoryRepository,
)
from bot.utils.time_utils import (
    get_week_start,
    get_day_name,
    get_day_date,
    format_date,
    format_time_range,
    calculate_optimal_time,
    format_time,
)


@dataclass
class BookingResult:
    success: bool
    message: str
    session: Session | None = None
    booking: Booking | None = None
    is_waitlist: bool = False
    promoted_user: tuple[int, str] | None = None  # (user_id, username)


class BookingService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.game_repo = GameRepository(db_session)
        self.session_repo = SessionRepository(db_session)
        self.booking_repo = BookingRepository(db_session)
        self.history_repo = BookingHistoryRepository(db_session)

    async def get_games(self) -> list[Game]:
        """Get all available games."""
        return await self.game_repo.get_all()

    async def get_game(self, name: str) -> Game | None:
        """Get game by name."""
        return await self.game_repo.get_by_name(name)

    async def get_session(
        self, game: Game, chat_id: int, day: str, week_start: date | None = None
    ) -> Session | None:
        """Get existing open session (does not create new one)."""
        if week_start is None:
            week_start = get_week_start()

        return await self.session_repo.get_current_session(
            game.id, chat_id, day, week_start
        )

    async def create_session(
        self, game: Game, chat_id: int, day: str, week_start: date | None = None
    ) -> Session:
        """Create a new session (used by scheduler only)."""
        if week_start is None:
            week_start = get_week_start()

        # Check if already exists
        existing = await self.session_repo.get_current_session(
            game.id, chat_id, day, week_start
        )
        if existing:
            return existing

        session = await self.session_repo.create(
            game_id=game.id,
            chat_id=chat_id,
            day=day,
            week_start=week_start,
        )
        # Reload with relationships
        return await self.session_repo.get_by_id(session.id)

    async def get_open_sessions(self, chat_id: int) -> list[Session]:
        """Get all open sessions for a chat."""
        return await self.session_repo.get_open_sessions(chat_id)

    async def get_session_by_id(self, session_id: int) -> Session | None:
        """Get session by ID."""
        return await self.session_repo.get_by_id(session_id)

    async def book(
        self,
        session: Session,
        user_id: int,
        username: str,
        time_from: time,
        time_to: time,
    ) -> BookingResult:
        """Create a booking for a session."""
        # Check if user already booked
        existing = await self.booking_repo.get_user_booking(session.id, user_id)
        if existing:
            return BookingResult(
                success=False,
                message="Ви вже маєте бронювання на цю сесію.",
                session=session,
            )

        # Get next position
        position = await self.booking_repo.get_next_position(session.id)

        # Determine status based on position
        max_slots = session.game.max_slots
        is_waitlist = position > max_slots
        status = "waitlist" if is_waitlist else "confirmed"

        # Create booking
        booking = await self.booking_repo.create(
            session_id=session.id,
            user_id=user_id,
            username=username,
            time_from=time_from,
            time_to=time_to,
            position=position,
            status=status,
        )

        # Add to history
        await self.history_repo.add(
            user_id=user_id,
            username=username,
            game=session.game.name,
            action="booked",
        )

        # Reload session (send_session_message uses fresh db session for latest data)
        session = await self.session_repo.get_by_id(session.id)

        if is_waitlist:
            return BookingResult(
                success=True,
                message=f"Ви додані в чергу на позицію {position - max_slots}.",
                session=session,
                booking=booking,
                is_waitlist=True,
            )

        return BookingResult(
            success=True,
            message=f"Ви успішно забронювали слот {position}!",
            session=session,
            booking=booking,
        )

    async def cancel(
        self, session: Session, user_id: int, username: str
    ) -> BookingResult:
        """Cancel a booking and promote from waitlist if needed."""
        booking = await self.booking_repo.get_user_booking(session.id, user_id)
        if not booking:
            return BookingResult(
                success=False,
                message="У вас немає бронювання на цю сесію.",
                session=session,
            )

        was_confirmed = booking.status == "confirmed"
        cancelled_position = booking.position

        # Cancel the booking
        await self.booking_repo.cancel_booking(booking.id)

        # Add to history
        await self.history_repo.add(
            user_id=user_id,
            username=username,
            game=session.game.name,
            action="cancelled",
        )

        promoted_user = None

        # If was confirmed, try to promote from waitlist
        if was_confirmed:
            waitlist = await self.booking_repo.get_waitlist(
                session.id, session.game.max_slots
            )
            if waitlist:
                # Promote first person from waitlist
                promoted = waitlist[0]
                await self.booking_repo.update_position_and_status(
                    promoted.id,
                    cancelled_position,
                    "confirmed",
                )
                promoted_user = (promoted.user_id, promoted.username)

                # Shift other waitlist positions
                for i, wl_booking in enumerate(waitlist[1:], start=1):
                    new_position = session.game.max_slots + i
                    await self.booking_repo.update_position_and_status(
                        wl_booking.id,
                        new_position,
                        "waitlist",
                    )

        # Reload session (send_session_message uses fresh db session for latest data)
        session = await self.session_repo.get_by_id(session.id)

        return BookingResult(
            success=True,
            message="Ваше бронювання скасовано.",
            session=session,
            promoted_user=promoted_user,
        )

    async def get_user_bookings(
        self, chat_id: int, user_id: int
    ) -> list[tuple[Session, str]]:
        """Get all active bookings for a user in a chat."""
        sessions = await self.session_repo.get_open_sessions(chat_id)
        user_bookings = []

        for session in sessions:
            booking = await self.booking_repo.get_user_booking(session.id, user_id)
            if booking:
                user_bookings.append((session, session.game.name))

        return user_bookings

    async def get_slots_info(
        self, chat_id: int, day: str | None = None
    ) -> dict[str, tuple[int, int]]:
        """Get slots info for all games: {game_name: (current, max)}."""
        games = await self.game_repo.get_all()
        week_start = get_week_start()
        result = {}

        for game in games:
            if day:
                session = await self.session_repo.get_current_session(
                    game.id, chat_id, day, week_start
                )
                if session:
                    confirmed = await self.booking_repo.get_confirmed(session.id)
                    result[game.name] = (len(confirmed), game.max_slots)
                else:
                    result[game.name] = (0, game.max_slots)
            else:
                # Combine both days
                total = 0
                for d in ["saturday", "sunday"]:
                    session = await self.session_repo.get_current_session(
                        game.id, chat_id, d, week_start
                    )
                    if session:
                        confirmed = await self.booking_repo.get_confirmed(session.id)
                        total += len(confirmed)
                result[game.name] = (total, game.max_slots)

        return result

    async def update_message_id(self, session_id: int, message_id: int):
        """Update session message ID."""
        await self.session_repo.update_message_id(session_id, message_id)

    def format_session_message(self, session: Session) -> str:
        """Format session message for display."""
        game = session.game
        day_name = get_day_name(session.day)
        day_date = get_day_date(session.day, session.week_start)
        formatted_date = format_date(day_date)

        status_emoji = "🟢" if session.status == "open" else "🔴"
        status_text = "Відкрито" if session.status == "open" else "Закрито"

        lines = [
            f"🎮 {game.name} — {day_name}, {formatted_date}",
            f"Статус: {status_emoji} {status_text}",
            "",
        ]

        # Get confirmed and waitlist bookings
        confirmed = [b for b in session.bookings if b.status == "confirmed"]
        waitlist = [b for b in session.bookings if b.status == "waitlist"]

        # Sort by position
        confirmed.sort(key=lambda b: b.position)
        waitlist.sort(key=lambda b: b.position)

        # Slots section
        lines.append(f"✅ Слоти ({len(confirmed)}/{game.max_slots}):")
        if confirmed:
            for booking in confirmed:
                time_range = format_time_range(booking.time_from, booking.time_to)
                lines.append(f"{booking.position}. @{booking.username} ({time_range})")
        else:
            lines.append("— Поки що немає бронювань")

        # Waitlist section
        if waitlist:
            lines.append("")
            lines.append("⏳ Черга:")
            for i, booking in enumerate(waitlist, start=1):
                time_range = format_time_range(booking.time_from, booking.time_to)
                lines.append(
                    f"{game.max_slots + i}. @{booking.username} ({time_range})"
                )

        # Optimal time
        if confirmed:
            optimal = calculate_optimal_time(confirmed)
            lines.append("")
            if optimal:
                start, end = optimal
                lines.append(f"⏰ Оптимальний час: {format_time(start)}-{format_time(end)} (всі можуть)")
            else:
                lines.append("⚠️ Немає спільного часу для всіх учасників")

        return "\n".join(lines)

    async def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics."""
        return await self.history_repo.get_user_stats(user_id)

    async def get_group_stats(self) -> list[dict]:
        """Get group statistics."""
        return await self.history_repo.get_group_stats()

    async def close_all_sessions(self, chat_id: int):
        """Close all open sessions for a chat."""
        sessions = await self.session_repo.get_open_sessions(chat_id)

        for session in sessions:
            # Mark all confirmed bookings as played
            confirmed = [b for b in session.bookings if b.status == "confirmed"]
            for booking in confirmed:
                await self.history_repo.add(
                    user_id=booking.user_id,
                    username=booking.username,
                    game=session.game.name,
                    action="played",
                )

        await self.session_repo.close_all_sessions(chat_id)

    async def get_all_open_sessions(self) -> list[Session]:
        """Get all open sessions across all chats."""
        return await self.session_repo.get_all_open_sessions()
