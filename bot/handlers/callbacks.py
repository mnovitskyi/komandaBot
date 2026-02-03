from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.database.session import async_session
from bot.services.booking import BookingService
from bot.keyboards.inline import (
    game_selection_keyboard,
    day_selection_keyboard,
    time_start_keyboard,
    time_end_keyboard,
    confirm_cancel_keyboard,
)
from bot.utils.time_utils import parse_time, get_day_name, is_valid_time_range
from bot.services.notifications import send_session_message, notify_promoted_user

router = Router()


@router.callback_query(F.data.startswith("book:game:"))
async def callback_select_game(callback: CallbackQuery):
    """Handle game selection."""
    game = callback.data.split(":")[-1]

    await callback.message.edit_text(
        "📅 Оберіть день:",
        reply_markup=day_selection_keyboard(game),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("book:day:"))
async def callback_select_day(callback: CallbackQuery):
    """Handle day selection."""
    parts = callback.data.split(":")
    game_name = parts[2]
    day = parts[3]

    # Check if session exists (booking is open)
    async with async_session() as db:
        service = BookingService(db)
        game = await service.get_game(game_name)
        if not game:
            await callback.answer("Гру не знайдено", show_alert=True)
            return

        session = await service.get_session(
            game=game,
            chat_id=callback.message.chat.id,
            day=day,
        )
        if not session:
            await callback.answer(
                "Бронювання на цей день ще не відкрито",
                show_alert=True,
            )
            return

    await callback.message.edit_text(
        "🕐 Оберіть час початку:",
        reply_markup=time_start_keyboard(game_name, day),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("book:start:"))
async def callback_select_start(callback: CallbackQuery):
    """Handle start time selection."""
    parts = callback.data.split(":")
    game = parts[2]
    day = parts[3]
    start = f"{parts[4]}:{parts[5]}"

    await callback.message.edit_text(
        f"🕐 Початок: {start}\nОберіть час закінчення:",
        reply_markup=time_end_keyboard(game, day, start),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("book:end:"))
async def callback_select_end(callback: CallbackQuery):
    """Handle end time selection - complete booking."""
    parts = callback.data.split(":")
    game_name = parts[2].upper()
    day = parts[3]
    start = f"{parts[4]}:{parts[5]}"
    end = f"{parts[6]}:{parts[7]}"

    time_from = parse_time(start)
    time_to = parse_time(end)

    if not time_from or not time_to or not is_valid_time_range(time_from, time_to):
        await callback.message.edit_text("❌ Невірний діапазон часу.")
        await callback.answer()
        return

    async with async_session() as db:
        service = BookingService(db)
        game = await service.get_game(game_name)

        if not game:
            await callback.answer("Гру не знайдено", show_alert=True)
            return

        session = await service.get_session(
            game=game,
            chat_id=callback.message.chat.id,
            day=day,
        )
        if not session:
            await callback.message.edit_text(
                "❌ Бронювання ще не відкрито.\n"
                "Бронювання відкривається щочетверга о 18:00."
            )
            await callback.answer()
            return

        username = callback.from_user.username or callback.from_user.first_name
        result = await service.book(
            session=session,
            user_id=callback.from_user.id,
            username=username,
            time_from=time_from,
            time_to=time_to,
        )

        if result.success:
            await callback.message.edit_text(f"✅ {result.message}")
            await send_session_message(callback.bot, db, result.session)
        else:
            await callback.message.edit_text(f"❌ {result.message}")

    await callback.answer()


@router.callback_query(F.data.startswith("book:quick:"))
async def callback_quick_book(callback: CallbackQuery):
    """Handle quick book button from session message."""
    parts = callback.data.split(":")
    game_name = parts[2].upper()
    day = parts[3]

    # Check if user already has a booking
    async with async_session() as db:
        service = BookingService(db)
        game = await service.get_game(game_name)

        if not game:
            await callback.answer("Гру не знайдено", show_alert=True)
            return

        session = await service.get_session(
            game=game,
            chat_id=callback.message.chat.id,
            day=day,
        )
        if not session:
            await callback.answer("Бронювання ще не відкрито", show_alert=True)
            return

        from bot.database.repositories import BookingRepository
        booking_repo = BookingRepository(db)
        existing = await booking_repo.get_user_booking(session.id, callback.from_user.id)

        if existing:
            await callback.answer("Ви вже маєте бронювання на цю сесію", show_alert=True)
            return

    await callback.message.reply(
        "🕐 Оберіть час початку:",
        reply_markup=time_start_keyboard(game_name.lower(), day),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("book:back:"))
async def callback_back(callback: CallbackQuery):
    """Handle back navigation."""
    parts = callback.data.split(":")
    target = parts[2]

    if target == "game":
        async with async_session() as db:
            service = BookingService(db)
            games = await service.get_games()
            slots_info = await service.get_slots_info(callback.message.chat.id)

        await callback.message.edit_text(
            "🎮 Оберіть гру:",
            reply_markup=game_selection_keyboard(games, slots_info),
        )
    elif target == "day":
        game = parts[3]
        await callback.message.edit_text(
            "📅 Оберіть день:",
            reply_markup=day_selection_keyboard(game),
        )
    elif target == "start":
        game = parts[3]
        day = parts[4]
        await callback.message.edit_text(
            "🕐 Оберіть час початку:",
            reply_markup=time_start_keyboard(game, day),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("cancel:quick:"))
async def callback_quick_cancel(callback: CallbackQuery):
    """Handle quick cancel button from session message."""
    parts = callback.data.split(":")
    game_name = parts[2].upper()
    day = parts[3]

    async with async_session() as db:
        service = BookingService(db)
        game = await service.get_game(game_name)

        if not game:
            await callback.answer("Гру не знайдено", show_alert=True)
            return

        session = await service.get_session(
            game=game,
            chat_id=callback.message.chat.id,
            day=day,
        )
        if not session:
            await callback.answer("Сесію не знайдено", show_alert=True)
            return

        # Check if user has booking
        from bot.database.repositories import BookingRepository

        booking_repo = BookingRepository(db)
        booking = await booking_repo.get_user_booking(
            session.id, callback.from_user.id
        )

        if not booking:
            await callback.answer("У вас немає бронювання на цю сесію", show_alert=True)
            return

        day_name = get_day_name(day)
        await callback.message.reply(
            f"Скасувати бронювання {game_name} на {day_name}?",
            reply_markup=confirm_cancel_keyboard(session.id),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("cancel:confirm:"))
async def callback_cancel_confirm(callback: CallbackQuery):
    """Show cancellation confirmation."""
    session_id = int(callback.data.split(":")[-1])

    await callback.message.edit_text(
        "Ви впевнені, що хочете скасувати бронювання?",
        reply_markup=confirm_cancel_keyboard(session_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:yes:"))
async def callback_cancel_yes(callback: CallbackQuery):
    """Confirm cancellation."""
    session_id = int(callback.data.split(":")[-1])

    async with async_session() as db:
        service = BookingService(db)
        session = await service.get_session_by_id(session_id)

        if not session:
            await callback.message.edit_text("❌ Сесію не знайдено.")
            await callback.answer()
            return

        username = callback.from_user.username or callback.from_user.first_name
        result = await service.cancel(
            session=session,
            user_id=callback.from_user.id,
            username=username,
        )

        if result.success:
            await callback.message.edit_text(f"✅ {result.message}")
            await send_session_message(callback.bot, db, result.session)

            if result.promoted_user:
                user_id, promoted_username = result.promoted_user
                await notify_promoted_user(
                    callback.bot, callback.message.chat.id, user_id, promoted_username
                )
        else:
            await callback.message.edit_text(f"❌ {result.message}")

    await callback.answer()


@router.callback_query(F.data == "cancel:no")
async def callback_cancel_no(callback: CallbackQuery):
    """Cancel the cancellation."""
    await callback.message.edit_text("Скасування відмінено.")
    await callback.answer()


@router.callback_query(F.data.startswith("refresh:"))
async def callback_refresh(callback: CallbackQuery):
    """Refresh session message."""
    session_id = int(callback.data.split(":")[-1])

    async with async_session() as db:
        service = BookingService(db)
        session = await service.get_session_by_id(session_id)

        if not session:
            await callback.answer("Сесію не знайдено", show_alert=True)
            return

        await send_session_message(callback.bot, db, session)

    await callback.answer("Оновлено!")
