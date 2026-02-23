import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.database.session import async_session
from bot.services.booking import BookingService
from bot.keyboards.inline import (
    day_selection_keyboard,
    cancel_selection_keyboard,
)
from bot.utils.time_utils import parse_time, get_week_start, is_valid_time_range
from bot.services.notifications import send_session_message, notify_promoted_user
from bot.config import config

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await _try_delete_message(message)
    await message.answer(
        "👋 Пацанчики, я тут для того, щоб ви могли бронювати слоти на PUBG і не їбали один одному мозок в чаті.\n\n"
        "🎮 *Як це працює:*\n"
        "• Щочетверга о 18:00 (по пл часі) я відкриваю бронювання на вихідні\n"
        "• Ви тицяєте /book, обираєте день і час\n"
        "• Максимум 4 пацани на гру, решта йде в чергу\n"
        "• За годину до гри я нагадаю шоб не проїбали\n\n"
        "🔥 *Нахуя це потрібно:*\n"
        "• Не треба писати в чат \"хто грає?\"\n"
        "• Видно хто коли може\n"
        "• Автоматично рахує оптимальний час для всіх\n\n"
        "/book — забронювати\n"
        "/help — всі команди\n"
        f"/myid — твій ID ({message.from_user.id})",
        parse_mode="Markdown",
        disable_notification=True,
    )


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Show user's Telegram ID."""
    await _try_delete_message(message)
    await message.answer(
        f"🆔 Твій Telegram ID: `{message.from_user.id}`\n"
        f"Username: @{message.from_user.username or 'не вказано'}",
        parse_mode="Markdown",
        disable_notification=True,
    )


async def _try_delete_message(message: Message):
    """Try to delete a message, ignore if no permission."""
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("book"))
async def cmd_book(message: Message):
    """Handle /book command - show game selection or quick book."""
    args = message.text.split()[1:] if message.text else []

    async with async_session() as db:
        service = BookingService(db)

        # Quick booking: /book sat 18:00-22:00
        if len(args) >= 2:
            day_arg = args[0].lower()
            time_arg = args[1]

            # Parse day
            day_map = {"sat": "saturday", "sun": "sunday", "субота": "saturday", "неділя": "sunday"}
            day = day_map.get(day_arg)
            if not day:
                reply = await message.reply("❌ Невірний день. Використовуйте: sat/sun або субота/неділя")
                await _try_delete_message(message)
                return

            # Parse time
            time_match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", time_arg)
            if not time_match:
                reply = await message.reply("❌ Невірний формат часу. Використовуйте: HH:MM-HH:MM")
                await _try_delete_message(message)
                return

            time_from = parse_time(time_match.group(1))
            time_to = parse_time(time_match.group(2))

            if not time_from or not time_to:
                reply = await message.reply("❌ Невірний формат часу.")
                await _try_delete_message(message)
                return

            if not is_valid_time_range(time_from, time_to):
                reply = await message.reply("❌ Час закінчення має бути після часу початку.")
                await _try_delete_message(message)
                return

            # Get PUBG (only game)
            game = await service.get_game("PUBG")

            # Get existing session (booking must be open)
            session = await service.get_session(
                game=game,
                chat_id=message.chat.id,
                day=day,
            )
            if not session:
                reply = await message.reply(
                    "❌ Бронювання ще не відкрито.\n"
                    "Бронювання відкривається щочетверга о 18:00 (по пл часі)."
                )
                await _try_delete_message(message)
                return

            # Create booking
            username = message.from_user.username or message.from_user.first_name
            result = await service.book(
                session=session,
                user_id=message.from_user.id,
                username=username,
                time_from=time_from,
                time_to=time_to,
            )

            # Delete command message first
            await _try_delete_message(message)

            if result.success:
                # Just update the session message, user sees the result there
                await send_session_message(message.bot, db, result.session)
            else:
                # Show error briefly
                await message.answer(f"❌ {result.message}")

            return

        # Check if any sessions are open
        open_sessions = await service.get_open_sessions(message.chat.id)
        if not open_sessions:
            reply = await message.reply(
                "❌ Бронювання ще не відкрито.\n"
                "Бронювання відкривається щочетверга о 18:00 (по пл часі)."
            )
            await _try_delete_message(message)
            return

        # Delete command message
        await _try_delete_message(message)

        # Skip game selection since we only have PUBG
        await message.answer(
            "📅 Оберіть день:",
            reply_markup=day_selection_keyboard("pubg", message.from_user.id),
            disable_notification=True,
        )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    """Handle /cancel command - show bookings to cancel or quick cancel."""
    args = message.text.split()[1:] if message.text else []

    async with async_session() as db:
        service = BookingService(db)

        # Quick cancel: /cancel sat
        if len(args) >= 1:
            day_arg = args[0].lower()

            day_map = {"sat": "saturday", "sun": "sunday", "субота": "saturday", "неділя": "sunday"}
            day = day_map.get(day_arg)

            if not day:
                await message.reply("❌ Невірний день.")
                await _try_delete_message(message)
                return

            # Get PUBG (only game)
            game = await service.get_game("PUBG")

            session = await service.get_session(
                game=game,
                chat_id=message.chat.id,
                day=day,
            )
            if not session:
                await message.reply("❌ Немає активних сесій для скасування.")
                await _try_delete_message(message)
                return

            username = message.from_user.username or message.from_user.first_name
            result = await service.cancel(
                session=session,
                user_id=message.from_user.id,
                username=username,
            )

            # Delete command message
            await _try_delete_message(message)

            if result.success:
                # Just update the session message
                await send_session_message(message.bot, db, result.session)

                if result.promoted_user:
                    user_id, promoted_username = result.promoted_user
                    await notify_promoted_user(
                        message.bot, message.chat.id, user_id, promoted_username
                    )
            else:
                await message.answer(f"❌ {result.message}")

            return

        # Show user's bookings
        user_bookings = await service.get_user_bookings(
            message.chat.id, message.from_user.id
        )

        if not user_bookings:
            await message.reply("❌ У вас немає активних бронювань.")
            await _try_delete_message(message)
            return

        # Delete command message
        await _try_delete_message(message)

        await message.answer(
            "Оберіть бронювання для скасування:",
            reply_markup=cancel_selection_keyboard(user_bookings),
            disable_notification=True,
        )


@router.message(Command("edit"))
async def cmd_edit(message: Message):
    """Handle /edit command - quick edit booking times.
    Usage: /edit sat 19:00-23:00
    """
    args = message.text.split()[1:] if message.text else []

    if len(args) < 2:
        await _try_delete_message(message)
        await message.answer(
            "❌ Використовуйте: /edit sat 19:00-23:00",
            disable_notification=True,
        )
        return

    day_arg = args[0].lower()
    time_arg = args[1]

    day_map = {"sat": "saturday", "sun": "sunday", "субота": "saturday", "неділя": "sunday"}
    day = day_map.get(day_arg)
    if not day:
        await _try_delete_message(message)
        await message.answer("❌ Невірний день. Використовуйте: sat/sun або субота/неділя")
        return

    time_match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", time_arg)
    if not time_match:
        await _try_delete_message(message)
        await message.answer("❌ Невірний формат часу. Використовуйте: HH:MM-HH:MM")
        return

    time_from = parse_time(time_match.group(1))
    time_to = parse_time(time_match.group(2))

    if not time_from or not time_to or not is_valid_time_range(time_from, time_to):
        await _try_delete_message(message)
        await message.answer("❌ Невірний діапазон часу.")
        return

    async with async_session() as db:
        service = BookingService(db)
        game = await service.get_game("PUBG")
        session = await service.get_session(game=game, chat_id=message.chat.id, day=day)

        if not session:
            await _try_delete_message(message)
            await message.answer("❌ Немає активних сесій.")
            return

        username = message.from_user.username or message.from_user.first_name
        result = await service.edit_booking(
            session=session,
            user_id=message.from_user.id,
            username=username,
            time_from=time_from,
            time_to=time_to,
        )

        await _try_delete_message(message)

        if result.success:
            await send_session_message(message.bot, db, result.session)
        else:
            await message.answer(f"❌ {result.message}")


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show all open sessions."""
    # Delete command message
    await _try_delete_message(message)

    async with async_session() as db:
        service = BookingService(db)
        sessions = await service.get_open_sessions(message.chat.id)

        if not sessions:
            await message.answer(
                "Немає активних сесій бронювання.\n"
                "Бронювання відкривається щочетверга о 18:00 (по пл часі)."
            )
            return

        # Group by game and send one combined message per game
        seen_games = set()
        for session in sessions:
            if session.game.id not in seen_games:
                seen_games.add(session.game.id)
                await send_session_message(message.bot, db, session)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    # Delete command message
    await _try_delete_message(message)

    help_text = """
🎮 *Бот, щоб пацанчики могли бронювати слоти на вихідні для PUBG*

*Команди:*
• `/book` — Забронювати слот
• `/book sat 18:00-22:00` — Швидке бронювання
• `/edit sat 19:00-23:00` — Змінити час бронювання
• `/cancel` — Скасувати бронювання
• `/cancel sat` — Швидке скасування
• `/status` — Хто грає
• `/mystats` — Твоя статистика
• `/stats` — Статистика пацанів
• `/help` — Ця довідка

*Аналітика чату:*
• `/вайб` — Настрій чату прямо зараз
• `/стата` — Твоя активність за 7 днів
• `/стата @user` — Активність іншого учасника
• `/топ` — Лідерборд тижня
• `/роль @user` — AI призначає соціальну роль


• `/release_note` — Що нового в боті

*Адмін:*
• `/open` — Відкрити бронювання
• `/close` — Закрити бронювання
• `/remove @username day` — Видалити бронювання

*Дні:*
• sat / субота — Субота
• sun / неділя — Неділя

*Час:*
• HH:MM-HH:MM (напр. 18:00-22:00)
• Часовий пояс: Europe/Warsaw 🇵🇱

*Автоматика (по пл часі):*
• Четвер 18:00 — Відкриття
• Неділя 23:00 — Закриття
• За 1 год до гри — Нагадування

Єбаште і ніколи не здавайтесь!
"""
    await message.answer(help_text, parse_mode="Markdown", disable_notification=True)


@router.message(Command("chatid"))
async def cmd_chatid(message: Message):
    """Handle /chatid command - show current chat ID."""
    await _try_delete_message(message)
    await message.answer(f"Chat ID: `{message.chat.id}`", parse_mode="Markdown")


@router.message(Command("open"))
async def cmd_open(message: Message):
    """Admin command to manually open booking sessions."""
    await _try_delete_message(message)

    async with async_session() as db:
        service = BookingService(db)
        games = await service.get_games()

        for game in games:
            # Create both sessions first
            sat_session = await service.create_session(
                game=game,
                chat_id=message.chat.id,
                day="saturday",
            )
            await service.create_session(
                game=game,
                chat_id=message.chat.id,
                day="sunday",
            )
            # Send one combined message (using saturday session as reference)
            await send_session_message(message.bot, db, sat_session)


@router.message(Command("close"))
async def cmd_close(message: Message):
    """Admin command to manually close all booking sessions."""
    await _try_delete_message(message)

    async with async_session() as db:
        service = BookingService(db)
        await service.close_all_sessions(message.chat.id)

        await message.answer("🔒 Всі сесії бронювання закрито.")


@router.message(Command("remove"))
async def cmd_remove(message: Message):
    """Admin command to remove someone from the queue.
    Usage: /remove @username saturday or /remove @username sunday
    """
    await _try_delete_message(message)
    
    # Check if user is admin
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ Тільки адміни можуть видаляти броні.", disable_notification=True)
        return
    
    # Parse command: /remove @username day
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(
            "❌ Неправильний формат. Використовуй:\n"
            "/remove @username saturday\n"
            "або\n"
            "/remove @username sunday",
            disable_notification=True
        )
        return
    
    username = parts[1].lstrip("@")
    day = parts[2].lower()
    
    if day not in ["saturday", "sunday"]:
        await message.answer("❌ День має бути 'saturday' або 'sunday'", disable_notification=True)
        return
    
    async with async_session() as db:
        service = BookingService(db)
        week_start = get_week_start()
        
        # Get the session for this day
        session = await service.get_or_create_session(
            chat_id=message.chat.id,
            day=day,
            week_start=week_start
        )
        
        if not session:
            await message.answer(f"❌ Сесія для {day} не знайдена.", disable_notification=True)
            return
        
        # Find and cancel the booking
        booking_cancelled = False
        promoted_user = None
        
        for booking in session.bookings:
            if booking.username.lower() == username.lower() and booking.status in ["confirmed", "waitlist"]:
                old_status = booking.status
                booking.status = "cancelled"
                await db.commit()
                booking_cancelled = True
                
                # If it was confirmed, promote someone from waitlist
                if old_status == "confirmed":
                    promoted_user = await service.promote_from_waitlist(session.id)
                
                break
        
        if not booking_cancelled:
            await message.answer(
                f"❌ Активне бронювання для @{username} на {day} не знайдено.",
                disable_notification=True
            )
            return
        
        # Update the session message
        await send_session_message(message.bot, db, session)
        
        # Notify the removed user
        day_name = "суботу" if day == "saturday" else "неділю"
        await message.answer(
            f"✅ Бронювання @{username} на {day_name} видалено адміном.",
            disable_notification=True
        )
        
        # Notify promoted user if any
        if promoted_user:
            await notify_promoted_user(message.bot, promoted_user, session)
