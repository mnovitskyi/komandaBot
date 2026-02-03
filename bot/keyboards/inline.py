from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import Game, Session


def game_selection_keyboard(
    games: list[Game], slots_info: dict[str, tuple[int, int]]
) -> InlineKeyboardMarkup:
    """
    Create keyboard for game selection.
    slots_info: {game_name: (current_slots, max_slots)}
    """
    builder = InlineKeyboardBuilder()

    for game in games:
        current, max_slots = slots_info.get(game.name, (0, game.max_slots))
        text = f"{game.name} ({current}/{max_slots})"
        builder.button(
            text=text,
            callback_data=f"book:game:{game.name.lower()}",
        )

    builder.adjust(2)
    return builder.as_markup()


def day_selection_keyboard(game: str) -> InlineKeyboardMarkup:
    """Create keyboard for day selection."""
    builder = InlineKeyboardBuilder()

    builder.button(text="Субота", callback_data=f"book:day:{game}:saturday")
    builder.button(text="Неділя", callback_data=f"book:day:{game}:sunday")
    builder.button(text="« Назад", callback_data="book:back:game")

    builder.adjust(2, 1)
    return builder.as_markup()


def time_start_keyboard(game: str, day: str) -> InlineKeyboardMarkup:
    """Create keyboard for start time selection."""
    builder = InlineKeyboardBuilder()

    times = [
        "10:00", "11:00", "12:00", "13:00",
        "14:00", "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00", "21:00", "22:00",
    ]
    for t in times:
        builder.button(
            text=t,
            callback_data=f"book:start:{game}:{day}:{t}",
        )

    builder.button(text="« Назад", callback_data=f"book:back:day:{game}")

    builder.adjust(4, 4, 4, 1, 1)
    return builder.as_markup()


def time_end_keyboard(game: str, day: str, start: str) -> InlineKeyboardMarkup:
    """Create keyboard for end time selection."""
    builder = InlineKeyboardBuilder()

    start_hour = int(start.split(":")[0])

    # Generate end times: from start+1 to 00:00
    times = []
    for h in range(start_hour + 1, 24):
        times.append(f"{h:02d}:00")
    times.append("00:00")  # Midnight

    for t in times:
        builder.button(
            text=t,
            callback_data=f"book:end:{game}:{day}:{start}:{t}",
        )

    builder.button(text="« Назад", callback_data=f"book:back:start:{game}:{day}")

    # Adjust layout based on number of buttons
    builder.adjust(4)
    return builder.as_markup()


def session_keyboard(session: Session) -> InlineKeyboardMarkup:
    """Create keyboard for session message."""
    builder = InlineKeyboardBuilder()

    game_name = session.game.name.lower()
    day = session.day

    builder.button(
        text="📝 Забронювати",
        callback_data=f"book:quick:{game_name}:{day}",
    )
    builder.button(
        text="❌ Скасувати",
        callback_data=f"cancel:quick:{game_name}:{day}",
    )
    builder.button(
        text="🔄 Оновити",
        callback_data=f"refresh:{session.id}",
    )

    builder.adjust(2, 1)
    return builder.as_markup()


def cancel_selection_keyboard(
    user_bookings: list[tuple[Session, str]]
) -> InlineKeyboardMarkup:
    """
    Create keyboard for cancel selection.
    user_bookings: [(session, game_name), ...]
    """
    builder = InlineKeyboardBuilder()

    from bot.utils.time_utils import get_day_name

    for session, game_name in user_bookings:
        text = f"{game_name} — {get_day_name(session.day)}"
        builder.button(
            text=text,
            callback_data=f"cancel:confirm:{session.id}",
        )

    builder.adjust(1)
    return builder.as_markup()


def confirm_cancel_keyboard(session_id: int) -> InlineKeyboardMarkup:
    """Create confirmation keyboard for cancellation."""
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Так, скасувати", callback_data=f"cancel:yes:{session_id}")
    builder.button(text="❌ Ні", callback_data="cancel:no")

    builder.adjust(2)
    return builder.as_markup()
