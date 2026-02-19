from datetime import date, time, datetime
from sqlalchemy import select, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Game, Session, Booking, BookingHistory


class GameRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str) -> Game | None:
        result = await self.session.execute(
            select(Game).where(Game.name.ilike(name))
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Game]:
        result = await self.session.execute(select(Game))
        return list(result.scalars().all())


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        game_id: int,
        chat_id: int,
        day: str,
        week_start: date,
    ) -> Session:
        db_session = Session(
            game_id=game_id,
            chat_id=chat_id,
            day=day,
            week_start=week_start,
            status="open",
        )
        self.session.add(db_session)
        await self.session.commit()
        await self.session.refresh(db_session)
        return db_session

    async def get_by_id(self, session_id: int) -> Session | None:
        result = await self.session.execute(
            select(Session)
            .where(Session.id == session_id)
            .options(selectinload(Session.game), selectinload(Session.bookings))
        )
        return result.scalar_one_or_none()

    async def get_current_session(
        self, game_id: int, chat_id: int, day: str, week_start: date
    ) -> Session | None:
        result = await self.session.execute(
            select(Session)
            .where(
                and_(
                    Session.game_id == game_id,
                    Session.chat_id == chat_id,
                    Session.day == day,
                    Session.week_start == week_start,
                    Session.status == "open",
                )
            )
            .options(selectinload(Session.game), selectinload(Session.bookings))
        )
        return result.scalar_one_or_none()

    async def get_open_sessions(self, chat_id: int) -> list[Session]:
        result = await self.session.execute(
            select(Session)
            .where(
                and_(
                    Session.chat_id == chat_id,
                    Session.status == "open",
                )
            )
            .options(selectinload(Session.game), selectinload(Session.bookings))
        )
        return list(result.scalars().all())

    async def get_all_open_sessions(self) -> list[Session]:
        result = await self.session.execute(
            select(Session)
            .where(Session.status == "open")
            .options(selectinload(Session.game), selectinload(Session.bookings))
        )
        return list(result.scalars().all())

    async def update_message_id(self, session_id: int, message_id: int):
        await self.session.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(message_id=message_id)
        )
        await self.session.commit()

    async def close_session(self, session_id: int):
        await self.session.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(status="closed")
        )
        await self.session.commit()

    async def close_all_sessions(self, chat_id: int):
        await self.session.execute(
            update(Session)
            .where(and_(Session.chat_id == chat_id, Session.status == "open"))
            .values(status="closed")
        )
        await self.session.commit()


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        session_id: int,
        user_id: int,
        username: str,
        time_from: time,
        time_to: time,
        position: int,
        status: str = "confirmed",
    ) -> Booking:
        booking = Booking(
            session_id=session_id,
            user_id=user_id,
            username=username,
            time_from=time_from,
            time_to=time_to,
            position=position,
            status=status,
        )
        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def get_by_session(self, session_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                and_(
                    Booking.session_id == session_id,
                    Booking.status != "cancelled",
                )
            )
            .order_by(Booking.position)
        )
        return list(result.scalars().all())

    async def get_user_booking(
        self, session_id: int, user_id: int
    ) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(
                and_(
                    Booking.session_id == session_id,
                    Booking.user_id == user_id,
                    Booking.status != "cancelled",
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_next_position(self, session_id: int) -> int:
        result = await self.session.execute(
            select(Booking)
            .where(
                and_(
                    Booking.session_id == session_id,
                    Booking.status != "cancelled",
                )
            )
            .order_by(Booking.position.desc())
            .limit(1)
        )
        last_booking = result.scalar_one_or_none()
        return (last_booking.position + 1) if last_booking else 1

    async def cancel_booking(self, booking_id: int):
        await self.session.execute(
            update(Booking)
            .where(Booking.id == booking_id)
            .values(status="cancelled")
        )
        await self.session.commit()

    async def update_booking_times(
        self, booking_id: int, time_from: time, time_to: time
    ):
        await self.session.execute(
            update(Booking)
            .where(Booking.id == booking_id)
            .values(time_from=time_from, time_to=time_to)
        )
        await self.session.commit()

    async def update_position_and_status(
        self, booking_id: int, position: int, status: str
    ):
        await self.session.execute(
            update(Booking)
            .where(Booking.id == booking_id)
            .values(position=position, status=status)
        )
        await self.session.commit()

    async def get_waitlist(self, session_id: int, max_slots: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                and_(
                    Booking.session_id == session_id,
                    Booking.status == "waitlist",
                    Booking.position > max_slots,
                )
            )
            .order_by(Booking.position)
        )
        return list(result.scalars().all())

    async def get_confirmed(self, session_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                and_(
                    Booking.session_id == session_id,
                    Booking.status == "confirmed",
                )
            )
            .order_by(Booking.position)
        )
        return list(result.scalars().all())


class BookingHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self, user_id: int, username: str, game: str, action: str
    ) -> BookingHistory:
        history = BookingHistory(
            user_id=user_id,
            username=username,
            game=game,
            action=action,
        )
        self.session.add(history)
        await self.session.commit()
        return history

    async def get_user_stats(self, user_id: int) -> dict:
        result = await self.session.execute(
            select(BookingHistory).where(BookingHistory.user_id == user_id)
        )
        history = list(result.scalars().all())

        stats = {
            "total_bookings": 0,
            "total_cancellations": 0,
            "total_played": 0,
            "by_game": {},
        }

        for entry in history:
            if entry.game not in stats["by_game"]:
                stats["by_game"][entry.game] = {
                    "booked": 0,
                    "cancelled": 0,
                    "played": 0,
                }

            if entry.action == "booked":
                stats["total_bookings"] += 1
                stats["by_game"][entry.game]["booked"] += 1
            elif entry.action == "cancelled":
                stats["total_cancellations"] += 1
                stats["by_game"][entry.game]["cancelled"] += 1
            elif entry.action == "played":
                stats["total_played"] += 1
                stats["by_game"][entry.game]["played"] += 1

        return stats

    async def get_group_stats(self) -> list[dict]:
        result = await self.session.execute(
            select(BookingHistory).order_by(BookingHistory.created_at.desc())
        )
        history = list(result.scalars().all())

        user_stats = {}
        for entry in history:
            if entry.user_id not in user_stats:
                user_stats[entry.user_id] = {
                    "user_id": entry.user_id,
                    "username": entry.username,
                    "played": 0,
                    "cancelled": 0,
                }

            if entry.action == "played":
                user_stats[entry.user_id]["played"] += 1
            elif entry.action == "cancelled":
                user_stats[entry.user_id]["cancelled"] += 1

        return sorted(
            user_stats.values(), key=lambda x: x["played"], reverse=True
        )
