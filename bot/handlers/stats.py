from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.database.session import async_session
from bot.services.booking import BookingService

router = Router()


@router.message(Command("mystats"))
async def cmd_mystats(message: Message):
    """Handle /mystats command - show personal statistics."""
    async with async_session() as db:
        service = BookingService(db)
        stats = await service.get_user_stats(message.from_user.id)

        if stats["total_bookings"] == 0:
            await message.reply("📊 У вас ще немає статистики. Забронюйте свою першу гру!")
            return

        lines = [
            f"📊 *Статистика @{message.from_user.username or message.from_user.first_name}*",
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

        await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command - show group statistics."""
    async with async_session() as db:
        service = BookingService(db)
        stats = await service.get_group_stats()

        if not stats:
            await message.reply("📊 Ще немає статистики групи.")
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

            lines.append(
                f"{medal}{i}. @{player['username']}: {player['played']} ігор"
            )

        # Most cancellations (shame list)
        cancellers = sorted(stats, key=lambda x: x["cancelled"], reverse=True)
        top_cancellers = [p for p in cancellers if p["cancelled"] > 0][:3]

        if top_cancellers:
            lines.append("")
            lines.append("😅 *Найбільше скасувань:*")
            for player in top_cancellers:
                lines.append(
                    f"• @{player['username']}: {player['cancelled']} скасувань"
                )

        await message.reply("\n".join(lines), parse_mode="Markdown")
