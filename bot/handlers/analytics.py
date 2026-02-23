import logging
import re
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, MessageReactionUpdated

from bot.database.session import async_session
from bot.database.repositories import UserActivityRepository
from bot.middlewares.activity_tracker import _message_authors
from bot.services.analytics import analytics_service, _format_stats
from bot.services.ai_chat import ai_service

logger = logging.getLogger(__name__)

router = Router()

_RELEASE_NOTE = """🆕 <b>Що нового в боті</b>
<i>Оновлення від 23 лютого 2026</i>

<b>📊 Аналітика чату</b>
Бот тепер непомітно рахує активність кожного учасника. Текст повідомлень <b>ніколи не зберігається</b> — тільки цифри.

Що рахується:
• кількість і довжина повідомлень
• медіа (фото, відео, стікери)
• питання (є "?" в тексті)
• мати 🤬
• звернення до бота (теги та відповіді)
• активні години
• реакції 🔥❤️ (хто їх <b>отримав</b>)

---

<b>Нові команди:</b>

/vibe
Перевірка настрою чату прямо зараз. AI читає останні 30 повідомлень і описує що відбувається.

/stat
Твоя статистика за останні 7 днів + рівень і XP за весь час.

/stat @vasya
Те саме, але для іншого учасника.

/top
Лідерборд тижня: хто найактивніший, скільки питань задавав. AI додає смішний коментар до рейтингу.

/role @vasya
AI аналізує поведінкові метрики Васі і призначає йому соціальну роль:
🧠 Стратег · 🔥 Провокатор · 😂 Мемолог · 💤 Спостерігач
💬 Балакун · 💼 Бізнес-мозок · 👻 Привид
🤖 Улюбленець бота · 🗣️ Провокатор бота · 💞 Найкращий друг бота

---

<b>⚡ Система XP і рівнів</b>
Кожне повідомлення, реакція і образа бота дають XP. Рівні:
🥚 Не вилупився → 🐣 Курча → 🎮 Диванний стратег → 🍺 Пивний аналітик
→ 🔫 Збройний мудак → 🏕 Кемпер-підар → 💀 Ходячий труп
→ 🤬 Гроза маминих ботів → 👑 Король хаосу → 🍗 Трахнув маму бота

XP джерела: +1 за повідомлення, +1 за 100 символів, +3 за тег/відповідь боту,
+5 за образу мами бота, +2 за 🔥 реакцію, +1 за ❤️ реакцію.

---

<b>🗓 Авто-звіт щонеділі о 21:00</b>
Бот сам публікує тижневий підсумок: герой тижня, хто пропав, загальний вайб, мотивація на наступний тиждень.

---

<b>📦 Оновлення від 23 лютого 2026 (v2)</b>
• Додано трекінг матів 🤬
• Додано трекінг "трахнув маму бота" 👩
• Команди перейменовані на англійські: /vibe, /stat, /top, /role
• /stat повертає чисті дані з БД без AI

<b>📦 Оновлення від 23 лютого 2026 (v3)</b>
• Система XP і рівнів ⚡
• Трекінг реакцій 🔥❤️"""


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
