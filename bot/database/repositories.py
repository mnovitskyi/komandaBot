from datetime import date, time, datetime, timedelta
from sqlalchemy import select, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Game, Session, Booking, BookingHistory, UserActivity


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


class UserActivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_message(
        self,
        user_id: int,
        username: str | None,
        msg_date: date,
        length: int,
        has_media: bool,
        has_question: bool,
        hour: int,
        bot_mention: bool = False,
        bot_reply: bool = False,
        has_swear: bool = False,
        has_mom_insult: bool = False,
    ):
        result = await self.session.execute(
            select(UserActivity).where(
                and_(UserActivity.user_id == user_id, UserActivity.date == msg_date)
            )
        )
        activity = result.scalar_one_or_none()

        if activity is None:
            activity = UserActivity(
                user_id=user_id,
                username=username,
                date=msg_date,
                message_count=0,
                total_chars=0,
                short_count=0,
                medium_count=0,
                long_count=0,
                media_count=0,
                question_count=0,
                reactions_received=0,
                active_hours="",
                bot_mentions=0,
                bot_replies=0,
                swear_count=0,
                mom_insult_count=0,
            )
            self.session.add(activity)

        activity.message_count += 1
        activity.total_chars += length
        if length < 50:
            activity.short_count += 1
        elif length <= 200:
            activity.medium_count += 1
        else:
            activity.long_count += 1
        if has_media:
            activity.media_count += 1
        if has_question:
            activity.question_count += 1
        if bot_mention:
            activity.bot_mentions += 1
        if bot_reply:
            activity.bot_replies += 1
        if has_swear:
            activity.swear_count += 1
        if has_mom_insult:
            activity.mom_insult_count += 1

        hours = set(activity.active_hours.split(",")) if activity.active_hours else set()
        hours.discard("")
        hours.add(str(hour))
        activity.active_hours = ",".join(sorted(hours, key=int))

        if username:
            activity.username = username

        await self.session.commit()

    async def get_user_week_stats(self, user_id: int) -> dict:
        since = date.today() - timedelta(days=7)
        result = await self.session.execute(
            select(UserActivity).where(
                and_(UserActivity.user_id == user_id, UserActivity.date >= since)
            )
        )
        rows = list(result.scalars().all())

        all_hours: set[int] = set()
        for r in rows:
            if r.active_hours:
                for h in r.active_hours.split(","):
                    if h:
                        all_hours.add(int(h))

        return {
            "user_id": user_id,
            "username": rows[-1].username if rows else None,
            "message_count": sum(r.message_count for r in rows),
            "total_chars": sum(r.total_chars for r in rows),
            "short_count": sum(r.short_count for r in rows),
            "medium_count": sum(r.medium_count for r in rows),
            "long_count": sum(r.long_count for r in rows),
            "media_count": sum(r.media_count for r in rows),
            "question_count": sum(r.question_count for r in rows),
            "reactions_received": sum(r.reactions_received for r in rows),
            "bot_mentions": sum(r.bot_mentions for r in rows),
            "bot_replies": sum(r.bot_replies for r in rows),
            "swear_count": sum(r.swear_count for r in rows),
            "mom_insult_count": sum(r.mom_insult_count for r in rows),
            "active_days": len(rows),
            "active_hours": sorted(all_hours),
        }

    async def get_top_users(self, days: int = 7, limit: int = 10) -> list[dict]:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(UserActivity).where(UserActivity.date >= since)
        )
        rows = list(result.scalars().all())

        user_map: dict[int, dict] = {}
        for r in rows:
            if r.user_id not in user_map:
                user_map[r.user_id] = {
                    "user_id": r.user_id,
                    "username": r.username,
                    "message_count": 0,
                    "reactions_received": 0,
                    "question_count": 0,
                    "mom_insult_count": 0,
                }
            user_map[r.user_id]["message_count"] += r.message_count
            user_map[r.user_id]["reactions_received"] += r.reactions_received
            user_map[r.user_id]["question_count"] += r.question_count
            user_map[r.user_id]["mom_insult_count"] += r.mom_insult_count
            if r.username:
                user_map[r.user_id]["username"] = r.username

        return sorted(user_map.values(), key=lambda x: x["message_count"], reverse=True)[:limit]

    async def get_all_week_stats(self, days: int = 7) -> list[dict]:
        since = date.today() - timedelta(days=days)
        result = await self.session.execute(
            select(UserActivity).where(UserActivity.date >= since)
        )
        rows = list(result.scalars().all())

        user_map: dict[int, dict] = {}
        for r in rows:
            if r.user_id not in user_map:
                user_map[r.user_id] = {
                    "user_id": r.user_id,
                    "username": r.username,
                    "message_count": 0,
                    "total_chars": 0,
                    "short_count": 0,
                    "medium_count": 0,
                    "long_count": 0,
                    "media_count": 0,
                    "question_count": 0,
                    "reactions_received": 0,
                    "bot_mentions": 0,
                    "bot_replies": 0,
                    "swear_count": 0,
                    "mom_insult_count": 0,
                    "active_days": 0,
                }
            user_map[r.user_id]["message_count"] += r.message_count
            user_map[r.user_id]["total_chars"] += r.total_chars
            user_map[r.user_id]["short_count"] += r.short_count
            user_map[r.user_id]["medium_count"] += r.medium_count
            user_map[r.user_id]["long_count"] += r.long_count
            user_map[r.user_id]["media_count"] += r.media_count
            user_map[r.user_id]["question_count"] += r.question_count
            user_map[r.user_id]["reactions_received"] += r.reactions_received
            user_map[r.user_id]["bot_mentions"] += r.bot_mentions
            user_map[r.user_id]["bot_replies"] += r.bot_replies
            user_map[r.user_id]["swear_count"] += r.swear_count
            user_map[r.user_id]["mom_insult_count"] += r.mom_insult_count
            user_map[r.user_id]["active_days"] += 1
            if r.username:
                user_map[r.user_id]["username"] = r.username

        return sorted(user_map.values(), key=lambda x: x["message_count"], reverse=True)

    async def add_reaction(self, user_id: int, reaction_date: date):
        result = await self.session.execute(
            select(UserActivity).where(
                and_(UserActivity.user_id == user_id, UserActivity.date == reaction_date)
            )
        )
        activity = result.scalar_one_or_none()
        if activity:
            activity.reactions_received += 1
            await self.session.commit()
