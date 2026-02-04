from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.database.session import async_session
from bot.services.booking import BookingService

router = Router()


async def _try_delete_message(message: Message):
    """Try to delete a message, ignore if no permission."""
    try:
        await message.delete()
    except Exception:
        pass


def _escape_markdown(text: str) -> str:
    """Escape underscores for Markdown parsing."""
    return text.replace("_", "\\_")


@router.message(Command("mystats"))
async def cmd_mystats(message: Message):
    """Handle /mystats command - show personal statistics."""
    await _try_delete_message(message)

    async with async_session() as db:
        service = BookingService(db)
        stats = await service.get_user_stats(message.from_user.id)

        if stats["total_bookings"] == 0:
            await message.answer("📊 У вас ще немає статистики. Забронюйте свою першу гру!")
            return

        display_name = _escape_markdown(
            message.from_user.username or message.from_user.first_name
        )
        lines = [
            f"📊 *Статистика @{display_name}*",
            "",
            f"🎮 Всього бронювань: {stats['total_bookings']}",
            f"✅ Зіграно: {stats['total_played']}",
            f"❌ Скасовано: {stats['total_cancellations']}",
            "",
            "*По іграх:*",
        ]

        for game, game_stats in stats["by_game"].items():
            lines.append(
                f"• {game}: {game_stats['played']} зіграно, "
                f"{game_stats['cancelled']} скасовано"
            )

        # Calculate reliability score
        if stats["total_bookings"] > 0:
            reliability = (
                (stats["total_played"] / stats["total_bookings"]) * 100
            )
            lines.append("")
            lines.append(f"🎯 Надійність: {reliability:.0f}%")

        await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command - show group statistics."""
    await _try_delete_message(message)

    async with async_session() as db:
        service = BookingService(db)
        stats = await service.get_group_stats()

        if not stats:
            await message.answer("📊 Ще немає статистики групи.")
            return

        lines = [
            "📊 *Статистика групи*",
            "",
            "🏆 *Топ гравців:*",
        ]

        for i, player in enumerate(stats[:10], start=1):
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "

            username = _escape_markdown(player['username'])
            lines.append(
                f"{medal}{i}. @{username}: {player['played']} ігор"
            )

        # Most cancellations (shame list)
        cancellers = sorted(stats, key=lambda x: x["cancelled"], reverse=True)
        top_cancellers = [p for p in cancellers if p["cancelled"] > 0][:3]

        if top_cancellers:
            lines.append("")
            lines.append("😅 *Найбільше скасувань:*")
            for player in top_cancellers:
                username = _escape_markdown(player['username'])
                lines.append(
                    f"• @{username}: {player['cancelled']} скасувань"
                )

        await message.answer("\n".join(lines), parse_mode="Markdown")
