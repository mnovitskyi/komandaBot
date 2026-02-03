import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.database.session import async_session
from bot.services.booking import BookingService
from bot.keyboards.inline import (
    game_selection_keyboard,
    cancel_selection_keyboard,
)
from bot.utils.time_utils import parse_time, get_week_start, is_valid_time_range
from bot.services.notifications import send_session_message, notify_promoted_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.reply(
        "👋 Привіт! Я бот для бронювання ігрових слотів.\n\n"
        "🎮 Доступні ігри: PUBG (4 слоти), CS (5 слотів)\n\n"
        "Використовуйте /help для перегляду всіх команд.\n"
        "Або /book щоб забронювати слот."
    )


@router.message(Command("book"))
async def cmd_book(message: Message):
    """Handle /book command - show game selection or quick book."""
    args = message.text.split()[1:] if message.text else []

    async with async_session() as db:
        service = BookingService(db)

        # Quick booking: /book pubg sat 18:00-22:00
        if len(args) >= 3:
            game_name = args[0].upper()
            day_arg = args[1].lower()
            time_arg = args[2]

            # Parse day
            day_map = {"sat": "saturday", "sun": "sunday", "субота": "saturday", "неділя": "sunday"}
            day = day_map.get(day_arg)
            if not day:
                await message.reply("❌ Невірний день. Використовуйте: sat/sun або субота/неділя")
                return

            # Parse time
            time_match = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", time_arg)
            if not time_match:
                await message.reply("❌ Невірний формат часу. Використовуйте: HH:MM-HH:MM")
                return

            time_from = parse_time(time_match.group(1))
            time_to = parse_time(time_match.group(2))

            if not time_from or not time_to:
                await message.reply("❌ Невірний формат часу.")
                return

            if not is_valid_time_range(time_from, time_to):
                await message.reply("❌ Час закінчення має бути після часу початку.")
                return

            # Get game
            game = await service.get_game(game_name)
            if not game:
                await message.reply(f"❌ Гру '{game_name}' не знайдено.")
                return

            # Get existing session (booking must be open)
            session = await service.get_session(
                game=game,
                chat_id=message.chat.id,
                day=day,
            )
            if not session:
                await message.reply(
                    "❌ Бронювання ще не відкрито.\n"
                    "Бронювання відкривається щочетверга о 18:00."
                )
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

            if result.success:
                await message.reply(f"✅ {result.message}")
                await send_session_message(message.bot, db, result.session)
            else:
                await message.reply(f"❌ {result.message}")

            return

        # Check if any sessions are open
        open_sessions = await service.get_open_sessions(message.chat.id)
        if not open_sessions:
            await message.reply(
                "❌ Бронювання ще не відкрито.\n"
                "Бронювання відкривається щочетверга о 18:00."
            )
            return

        # Show game selection menu
        games = await service.get_games()
        slots_info = await service.get_slots_info(message.chat.id)

        await message.reply(
            "🎮 Оберіть гру:",
            reply_markup=game_selection_keyboard(games, slots_info),
        )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    """Handle /cancel command - show bookings to cancel or quick cancel."""
    args = message.text.split()[1:] if message.text else []

    async with async_session() as db:
        service = BookingService(db)

        # Quick cancel: /cancel pubg sat
        if len(args) >= 2:
            game_name = args[0].upper()
            day_arg = args[1].lower()

            day_map = {"sat": "saturday", "sun": "sunday", "субота": "saturday", "неділя": "sunday"}
            day = day_map.get(day_arg)

            if not day:
                await message.reply("❌ Невірний день.")
                return

            game = await service.get_game(game_name)
            if not game:
                await message.reply(f"❌ Гру '{game_name}' не знайдено.")
                return

            session = await service.get_session(
                game=game,
                chat_id=message.chat.id,
                day=day,
            )
            if not session:
                await message.reply("❌ Немає активних сесій для скасування.")
                return

            username = message.from_user.username or message.from_user.first_name
            result = await service.cancel(
                session=session,
                user_id=message.from_user.id,
                username=username,
            )

            if result.success:
                await message.reply(f"✅ {result.message}")
                await send_session_message(message.bot, db, result.session)

                if result.promoted_user:
                    user_id, promoted_username = result.promoted_user
                    await notify_promoted_user(
                        message.bot, message.chat.id, user_id, promoted_username
                    )
            else:
                await message.reply(f"❌ {result.message}")

            return

        # Show user's bookings
        user_bookings = await service.get_user_bookings(
            message.chat.id, message.from_user.id
        )

        if not user_bookings:
            await message.reply("У вас немає активних бронювань.")
            return

        await message.reply(
            "Оберіть бронювання для скасування:",
            reply_markup=cancel_selection_keyboard(user_bookings),
        )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show all open sessions."""
    async with async_session() as db:
        service = BookingService(db)
        sessions = await service.get_open_sessions(message.chat.id)

        if not sessions:
            await message.reply(
                "Немає активних сесій бронювання.\n"
                "Бронювання відкривається щочетверга о 18:00."
            )
            return

        for session in sessions:
            await send_session_message(message.bot, db, session)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """
🎮 *Команда Лайна — Бот для бронювання*

*Команди:*
• `/book` — Інтерактивне меню бронювання
• `/book pubg sat 18:00-22:00` — Швидке бронювання
• `/cancel` — Скасувати бронювання (меню)
• `/cancel pubg sat` — Швидке скасування
• `/status` — Показати поточні бронювання
• `/mystats` — Ваша статистика
• `/stats` — Статистика групи
• `/help` — Ця довідка

*Адмін команди:*
• `/open` — Відкрити бронювання вручну
• `/close` — Закрити всі сесії

*Ігри:*
• PUBG — 4 слоти
• CS — 5 слотів

*Дні:*
• sat / субота — Субота
• sun / неділя — Неділя

*Формат часу:*
• HH:MM-HH:MM (наприклад, 18:00-22:00)

*Автоматичні події:*
• Четвер 18:00 — Відкриття бронювання
• Неділя 23:00 — Закриття бронювання
• За 1 годину до гри — Нагадування
"""
    await message.reply(help_text, parse_mode="Markdown")


@router.message(Command("chatid"))
async def cmd_chatid(message: Message):
    """Handle /chatid command - show current chat ID."""
    await message.reply(f"Chat ID: `{message.chat.id}`", parse_mode="Markdown")


@router.message(Command("open"))
async def cmd_open(message: Message):
    """Admin command to manually open booking sessions."""
    async with async_session() as db:
        service = BookingService(db)
        games = await service.get_games()

        await message.reply("🎮 Відкриваю бронювання на вихідні...")

        for game in games:
            for day in ["saturday", "sunday"]:
                session = await service.create_session(
                    game=game,
                    chat_id=message.chat.id,
                    day=day,
                )
                await send_session_message(message.bot, db, session)

        await message.reply("✅ Бронювання відкрито!")


@router.message(Command("close"))
async def cmd_close(message: Message):
    """Admin command to manually close all booking sessions."""
    async with async_session() as db:
        service = BookingService(db)
        await service.close_all_sessions(message.chat.id)

        await message.reply("🔒 Всі сесії бронювання закрито.")
