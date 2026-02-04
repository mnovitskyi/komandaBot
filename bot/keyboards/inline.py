from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import Game, Session


def game_selection_keyboard(
    games: list[Game], slots_info: dict[str, tuple[int, int]], user_id: int
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
            callback_data=f"book:game:{game.name.lower()}:{user_id}",
        )

    builder.adjust(2)
    return builder.as_markup()


def day_selection_keyboard(game: str, user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for day selection."""
    builder = InlineKeyboardBuilder()

    builder.button(text="Субота", callback_data=f"book:day:{game}:saturday:{user_id}")
    builder.button(text="Неділя", callback_data=f"book:day:{game}:sunday:{user_id}")
    builder.button(text="❌ Скасувати", callback_data=f"book:close:{user_id}")

    builder.adjust(2, 1)
    return builder.as_markup()


def time_start_keyboard(game: str, day: str, user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for start time selection."""
    builder = InlineKeyboardBuilder()

    # Generate times from 10:00 to 22:30 with 30-min intervals
    for h in range(10, 23):
        builder.button(
            text=f"{h:02d}:00",
            callback_data=f"book:start:{game}:{day}:{h:02d}:00:{user_id}",
        )
        builder.button(
            text=f"{h:02d}:30",
            callback_data=f"book:start:{game}:{day}:{h:02d}:30:{user_id}",
        )

    builder.button(text="« Назад", callback_data=f"book:back:day:{game}:{user_id}")

    builder.adjust(4)
    return builder.as_markup()


def time_end_keyboard(game: str, day: str, start: str, user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for end time selection."""
    builder = InlineKeyboardBuilder()

    start_parts = start.split(":")
    start_hour = int(start_parts[0])
    start_min = int(start_parts[1])

    # Generate end times with 30-min intervals, starting from at least 30 min after start
    for h in range(start_hour, 24):
        for m in [0, 30]:
            # Skip times that are not after the start time
            if h == start_hour and m <= start_min:
                continue
            builder.button(
                text=f"{h:02d}:{m:02d}",
                callback_data=f"book:end:{game}:{day}:{start}:{h:02d}:{m:02d}:{user_id}",
            )

    # Add midnight option
    builder.button(
        text="00:00",
        callback_data=f"book:end:{game}:{day}:{start}:00:00:{user_id}",
    )

    builder.button(text="« Назад", callback_data=f"book:back:start:{game}:{day}:{user_id}")

    builder.adjust(4)
    return builder.as_markup()


def session_keyboard(session: Session) -> InlineKeyboardMarkup:
    """Create keyboard for session message (single day)."""
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


def weekly_keyboard(
    sat_session: Session | None, sun_session: Session | None
) -> InlineKeyboardMarkup:
    """Create keyboard for combined weekly message."""
    builder = InlineKeyboardBuilder()

    game_name = (sat_session or sun_session).game.name.lower()

    # Saturday buttons
    if sat_session:
        builder.button(
            text="📝 Субота",
            callback_data=f"book:quick:{game_name}:saturday",
        )
        builder.button(
            text="❌ Скасувати Сб",
            callback_data=f"cancel:quick:{game_name}:saturday",
        )

    # Sunday buttons
    if sun_session:
        builder.button(
            text="📝 Неділя",
            callback_data=f"book:quick:{game_name}:sunday",
        )
        builder.button(
            text="❌ Скасувати Нд",
            callback_data=f"cancel:quick:{game_name}:sunday",
        )

    # Refresh button - use saturday session id as primary
    primary_session = sat_session or sun_session
    builder.button(
        text="🔄 Оновити",
        callback_data=f"refresh:weekly:{primary_session.id}",
    )

    builder.adjust(2, 2, 1)
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
