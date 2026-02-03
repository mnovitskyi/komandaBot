from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from bot.config import config
from bot.database.session import async_session
from bot.database.repositories import GameRepository
from bot.services.booking import BookingService
from bot.services.notifications import send_session_message, send_reminder
from bot.utils.time_utils import get_week_start, get_timezone, calculate_optimal_time


scheduler = AsyncIOScheduler(timezone=get_timezone())


async def open_booking_sessions(bot: Bot):
    """Open booking sessions for the weekend (runs on Thursday 18:00)."""
    if not config.chat_id:
        return

    async with async_session() as db:
        game_repo = GameRepository(db)
        service = BookingService(db)

        games = await game_repo.get_all()
        week_start = get_week_start()

        # Send announcement
        await bot.send_message(
            chat_id=config.chat_id,
            text="🎮 Бронювання на вихідні відкрито! Обирайте гру та час:",
        )

        for game in games:
            for day in ["saturday", "sunday"]:
                session = await service.create_session(
                    game=game,
                    chat_id=config.chat_id,
                    day=day,
                    week_start=week_start,
                )
                await send_session_message(bot, db, session)


async def close_booking_sessions(bot: Bot):
    """Close all booking sessions (runs on Sunday 23:00)."""
    if not config.chat_id:
        return

    async with async_session() as db:
        service = BookingService(db)
        await service.close_all_sessions(config.chat_id)

        await bot.send_message(
            chat_id=config.chat_id,
            text="🔒 Бронювання на цей тиждень закрито. Дякуємо всім за гру!",
        )


async def schedule_game_reminders(bot: Bot):
    """Schedule reminders for games based on optimal time."""
    async with async_session() as db:
        service = BookingService(db)
        sessions = await service.get_all_open_sessions()

        tz = get_timezone()
        now = datetime.now(tz)

        for session in sessions:
            confirmed = [b for b in session.bookings if b.status == "confirmed"]
            if not confirmed:
                continue

            optimal = calculate_optimal_time(confirmed)
            if not optimal:
                continue

            start_time, _ = optimal

            # Calculate reminder time (1 hour before)
            from bot.utils.time_utils import get_day_date

            game_date = get_day_date(session.day, session.week_start)
            game_datetime = datetime.combine(
                game_date,
                start_time,
                tzinfo=tz,
            )

            reminder_time = game_datetime - timedelta(hours=1)

            # Only schedule if in the future
            if reminder_time > now:
                scheduler.add_job(
                    send_reminder,
                    "date",
                    run_date=reminder_time,
                    args=[bot, session],
                    id=f"reminder_{session.id}",
                    replace_existing=True,
                )


def setup_scheduler(bot: Bot):
    """Setup scheduled tasks."""
    tz = get_timezone()

    # Open booking on Thursday 18:00
    scheduler.add_job(
        open_booking_sessions,
        CronTrigger(day_of_week="thu", hour=18, minute=0, timezone=tz),
        args=[bot],
        id="open_booking",
        replace_existing=True,
    )

    # Close booking on Sunday 23:00
    scheduler.add_job(
        close_booking_sessions,
        CronTrigger(day_of_week="sun", hour=23, minute=0, timezone=tz),
        args=[bot],
        id="close_booking",
        replace_existing=True,
    )

    # Check for reminders every hour
    scheduler.add_job(
        schedule_game_reminders,
        CronTrigger(hour="*", minute=0, timezone=tz),
        args=[bot],
        id="check_reminders",
        replace_existing=True,
    )

    scheduler.start()


def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
