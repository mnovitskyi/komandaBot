from aiogram import Bot
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Session
from bot.database.session import async_session
from bot.services.booking import BookingService, escape_markdown
from bot.keyboards.inline import session_keyboard, weekly_keyboard


async def send_session_message(
    bot: Bot, db_session: AsyncSession, session: Session
) -> int | None:
    """Send or update weekly combined message. Returns message_id."""
    # Use a fresh db session to ensure we get the latest data
    async with async_session() as fresh_db:
        service = BookingService(fresh_db)

        # Get both Saturday and Sunday sessions for this game/chat
        game = session.game
        chat_id = session.chat_id
        week_start = session.week_start

        sat_session = await service.get_session(game, chat_id, "saturday", week_start)
        sun_session = await service.get_session(game, chat_id, "sunday", week_start)

        if not sat_session and not sun_session:
            return None

        # Refresh to get latest bookings
        if sat_session:
            sat_session = await service.get_session_by_id(sat_session.id)
        if sun_session:
            sun_session = await service.get_session_by_id(sun_session.id)

        # Format combined message
        text = service.format_weekly_message(sat_session, sun_session)
        keyboard = weekly_keyboard(sat_session, sun_session)

        # Use Saturday session's message_id as the primary (or Sunday if no Saturday)
        primary_session = sat_session or sun_session
        message_id = primary_session.message_id

        if message_id:
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                )
                return message_id
            except Exception:
                # Message might be too old or deleted, send new one
                pass

        # Send new message (silent)
        message = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
            disable_notification=True,
        )

        # Store message_id on the primary session
        await service.update_message_id(primary_session.id, message.message_id)

        # Also store on the other session if it exists (for refresh lookups)
        if sat_session and sun_session:
            other_session = sun_session if primary_session == sat_session else sat_session
            await service.update_message_id(other_session.id, message.message_id)

        return message.message_id


async def notify_promoted_user(bot: Bot, chat_id: int, user_id: int, username: str):
    """Notify user that they've been promoted from waitlist."""
    escaped_username = escape_markdown(username)
    await bot.send_message(
        chat_id=chat_id,
        text=f"🎉 @{escaped_username}, пацан, ти в грі! Хтось злився і тепер ти єбашиш з нами!",
        disable_notification=True,
    )


async def send_reminder(bot: Bot, session: Session, minutes_before: int = 60):
    """Send reminder to all confirmed participants."""
    confirmed = [b for b in session.bookings if b.status == "confirmed"]
    if not confirmed:
        return

    mentions = " ".join(f"@{escape_markdown(b.username)}" for b in confirmed)

    await bot.send_message(
        chat_id=session.chat_id,
        text=f"⏰ Пацанюри, через {minutes_before} хвилин єбашимо {session.game.name}! Готуйтесь!\n\n{mentions}",
    )
