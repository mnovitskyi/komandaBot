from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Session
from bot.database.session import async_session
from bot.services.booking import BookingService
from bot.keyboards.inline import session_keyboard


async def send_session_message(
    bot: Bot, db_session: AsyncSession, session: Session
) -> int | None:
    """Send or update session message. Returns message_id."""
    # Use a fresh db session to ensure we get the latest data
    async with async_session() as fresh_db:
        service = BookingService(fresh_db)

        # Fetch fresh session data to ensure bookings are up to date
        fresh_session = await service.get_session_by_id(session.id)
        if not fresh_session:
            return None

        text = service.format_session_message(fresh_session)
        keyboard = session_keyboard(fresh_session)

        if fresh_session.message_id:
            try:
                await bot.edit_message_text(
                    chat_id=fresh_session.chat_id,
                    message_id=fresh_session.message_id,
                    text=text,
                    reply_markup=keyboard,
                )
                return fresh_session.message_id
            except Exception:
                # Message might be too old or deleted, send new one
                pass

        # Send new message
        message = await bot.send_message(
            chat_id=fresh_session.chat_id,
            text=text,
            reply_markup=keyboard,
        )

        await service.update_message_id(fresh_session.id, message.message_id)
        return message.message_id


async def notify_promoted_user(bot: Bot, chat_id: int, user_id: int, username: str):
    """Notify user that they've been promoted from waitlist."""
    await bot.send_message(
        chat_id=chat_id,
        text=f"🎉 @{username}, ви тепер у грі! Місце звільнилось і вас було автоматично додано.",
    )


async def send_reminder(bot: Bot, session: Session, minutes_before: int = 60):
    """Send reminder to all confirmed participants."""
    confirmed = [b for b in session.bookings if b.status == "confirmed"]
    if not confirmed:
        return

    mentions = " ".join(f"@{b.username}" for b in confirmed)

    await bot.send_message(
        chat_id=session.chat_id,
        text=f"⏰ Нагадування! Гра {session.game.name} починається через {minutes_before} хвилин!\n\n{mentions}",
    )
