import logging
import re
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, MessageReactionUpdated

from bot.database.session import async_session
from bot.database.repositories import UserActivityRepository
from bot.middlewares.activity_tracker import _message_authors
from bot.services.analytics import analytics_service, _format_stats, calculate_xp, get_level, LEVELS
from bot.services.ai_chat import ai_service

logger = logging.getLogger(__name__)

router = Router()

_RELEASE_NOTE = """🆕 <b>Що нового в боті</b> — <i>23 лютого 2026</i>

<b>Команди:</b>
/stat — твоя статистика за 7 днів + рівень і XP
/stat @user — те саме для іншого учасника
/top — лідерборд тижня з AI-коментарем
/role @user — AI призначає соціальну роль
/vibe — AI описує настрій чату прямо зараз

<b>⚡ XP і рівні</b>
+1 за повідомлення · 
+1 за 100 символів · 
+3 за тег/відповідь боту · 
+5 за образу мами бота · 
+2 за 🔥 на твоєму повідомленні · 
+1 за ❤️ на твоєму повідомленні

🥚→🐣→🎮→🍺→🔫→🏕→💀→🤬→👑→🍗

<b>Що рахується:</b> кількість повідомлень, мати 🤬, образи мами бота 👩, реакції 🔥❤️, звернення до бота, активні години.
Текст <b>ніколи не зберігається</b> — тільки цифри.

<b>🗓 Авто-звіт щонеділі о 21:00</b>"""


@router.message(Command("release_note"))
async def handle_release_note(message: Message):
    await message.reply(_RELEASE_NOTE)


@router.message(Command("vibe"))
async def handle_vibe(message: Message):
    if not analytics_service:
        await message.reply("AI вимкнено 🤖")
        return

    context = list(ai_service._context) if ai_service else []
    vibe = await analytics_service.analyze_vibe(context)
    await message.reply(vibe)


@router.message_reaction()
async def handle_reaction(event: MessageReactionUpdated):
    author_id = _message_authors.get(event.message_id)
    if not author_id:
        return

    old_set = {r.emoji for r in (event.old_reaction or []) if hasattr(r, "emoji")}
    new_set = {r.emoji for r in (event.new_reaction or []) if hasattr(r, "emoji")}
    added = new_set - old_set

    fire = 1 if "🔥" in added else 0
    heart = 1 if "❤️" in added else 0

    if fire or heart:
        async with async_session() as db:
            repo = UserActivityRepository(db)
            await repo.add_reaction(author_id, date.today(), fire=fire, heart=heart)


@router.message(Command("stat"))
async def handle_stat(message: Message):
    text = message.text or ""
    mention_match = re.search(r"@(\w+)", text)

    if mention_match:
        target_username = mention_match.group(1)
        target_id = None

        async with async_session() as db:
            repo = UserActivityRepository(db)
            all_users = await repo.get_top_users(days=30, limit=100)
            for u in all_users:
                if (u.get("username") or "").lower() == target_username.lower():
                    target_id = u["user_id"]
                    break

        if target_id is None:
            await message.reply(
                f"Не знайшов @{target_username} в базі. Хай спочатку напише щось! 🤷"
            )
            return

        async with async_session() as db:
            repo = UserActivityRepository(db)
            stats = await repo.get_user_week_stats(target_id)
            total_stats = await repo.get_user_total_stats(target_id)
    else:
        target_id = message.from_user.id
        target_username = message.from_user.username
        async with async_session() as db:
            repo = UserActivityRepository(db)
            stats = await repo.get_user_week_stats(target_id)
            total_stats = await repo.get_user_total_stats(target_id)

    await message.reply(_format_stats(target_id, target_username, stats, total_stats))


@router.message(Command("top"))
async def handle_top(message: Message):
    if not analytics_service:
        await message.reply("AI вимкнено 🤖")
        return

    async with async_session() as db:
        reply = await analytics_service.get_top_text(db)

    await message.reply(reply)


@router.message(Command("role"))
async def handle_role(message: Message):
    if not analytics_service:
        await message.reply("AI вимкнено 🤖")
        return

    text = message.text or ""
    mention_match = re.search(r"@(\w+)", text)

    if not mention_match:
        await message.reply("Вкажи користувача: /role @username")
        return

    target_username = mention_match.group(1)
    target_id = None

    async with async_session() as db:
        repo = UserActivityRepository(db)
        all_users = await repo.get_top_users(days=30, limit=100)
        for u in all_users:
            if (u.get("username") or "").lower() == target_username.lower():
                target_id = u["user_id"]
                break

    if target_id is None:
        await message.reply(
            f"Не знайшов @{target_username} в базі. Хай спочатку напише щось! 🤷"
        )
        return

    async with async_session() as db:
        repo = UserActivityRepository(db)
        stats = await repo.get_user_week_stats(target_id)
        reply = await analytics_service.get_role(target_id, target_username, stats)

    await message.reply(reply)


@router.message(Command("ranking"))
async def handle_ranking(message: Message):
    async with async_session() as db:
        repo = UserActivityRepository(db)
        all_stats = await repo.get_all_users_total_stats()

    if not all_stats:
        await message.reply("Ще ніхто нічого не писав 👻")
        return

    ranked = sorted(
        [
            {
                "user_id": u["user_id"],
                "username": u["username"],
                "xp": calculate_xp(u),
            }
            for u in all_stats
        ],
        key=lambda x: x["xp"],
        reverse=True,
    )

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Рейтинг рівнів</b>\n"]
    for i, u in enumerate(ranked):
        medal = medals[i] if i < 3 else f"{i + 1}."
        name = f"@{u['username']}" if u.get("username") else f"user {u['user_id']}"
        _, level_name, _ = get_level(u["xp"])
        lines.append(f"{medal} {name} — {level_name} ({u['xp']} XP)")

    await message.reply("\n".join(lines))


@router.message(Command("levels"))
async def handle_levels(message: Message):
    lines = ["⚡ <b>Рівні</b>\n"]
    for i, (threshold, name) in enumerate(LEVELS):
        lines.append(f"{i + 1}. {name} — від {threshold} XP")

    lines.append(
        "\n<b>Як заробити XP:</b>\n"
        "+1 за повідомлення · +1 за кожні 100 символів\n"
        "+3 за тег/відповідь боту · +5 за образу мами бота\n"
        "+2 за 🔥 на твоєму повідомленні · +1 за ❤️"
    )

    await message.reply("\n".join(lines))
