import logging

from groq import AsyncGroq

from bot.config import config
from bot.database.repositories import UserActivityRepository

logger = logging.getLogger(__name__)

_MODEL = "moonshotai/kimi-k2-instruct"


def _format_stats(user_id: int, username: str | None, stats: dict) -> str:
    name = f"@{username}" if username else f"user {user_id}"

    if stats["message_count"] == 0:
        return f"{name}: немає повідомлень за останні 7 днів. Дані збираються з моменту запуску бота."

    avg_len = stats["total_chars"] // stats["message_count"] if stats["message_count"] else 0
    hours_str = (
        ", ".join(f"{h}:00" for h in stats["active_hours"])
        if stats["active_hours"]
        else "—"
    )

    return (
        f"📊 {name} — останні 7 днів\n"
        f"\n"
        f"💬 Повідомлень: {stats['message_count']}\n"
        f"📝 Середня довжина: {avg_len} симв.\n"
        f"  └ Коротких (&lt;50): {stats['short_count']}\n"
        f"  └ Середніх (50-200): {stats['medium_count']}\n"
        f"  └ Довгих (&gt;200): {stats['long_count']}\n"
        f"🖼 Медіа: {stats['media_count']}\n"
        f"❓ Питань: {stats['question_count']}\n"
        f"🤬 Матів: {stats['swear_count']}\n"
        f"👩 Мам трахнуто: {stats['mom_insult_count']}\n"
        f"⏰ Активні години: {hours_str}\n"
        f"📅 Активних днів: {stats['active_days']}/7\n"
        f"🤖 Звернень до бота: {stats['bot_mentions'] + stats['bot_replies']}"
    )


class AnalyticsService:
    def __init__(self):
        self._client = AsyncGroq(api_key=config.groq_api_key)

    async def analyze_vibe(self, messages: list[dict]) -> str:
        """Analyze the vibe of recent chat messages (in-memory buffer only, text never saved)."""
        if not messages:
            return "Чат мертвий 💀"

        try:
            history = "\n".join(m["content"] for m in messages[-30:])
            response = await self._client.chat.completions.create(
                model=_MODEL,
                max_tokens=200,
                messages=[
                    {
                        "role": "system",
                        "content": "Ти аналітик чату PUBG-команди. Відповідай коротко, по-українськи, з гумором.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Ось останні повідомлення з чату:\n{history}\n\n"
                            "Опиши вайб цього чату в 2-3 реченнях. Що відбувається? Який настрій? Будь чесним і смішним."
                        ),
                    },
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Vibe analysis error: {e}")
            return "Не вдалося зчитати вайб 🤷"

    async def get_user_stats_text(self, user_id: int, username: str | None, db) -> str:
        """Return formatted activity stats from DB — no AI involved."""
        repo = UserActivityRepository(db)
        stats = await repo.get_user_week_stats(user_id)
        return _format_stats(user_id, username, stats)

    async def get_top_text(self, db) -> str:
        """Return formatted leaderboard with AI one-liner comment."""
        repo = UserActivityRepository(db)
        top = await repo.get_top_users(days=7, limit=10)

        if not top:
            return "Ніхто не писав цього тижня 👻"

        medals = ["🥇", "🥈", "🥉"]
        lines = ["🏆 Топ чату за 7 днів:\n"]
        for i, user in enumerate(top):
            medal = medals[i] if i < 3 else f"{i + 1}."
            name = f"@{user['username']}" if user.get("username") else f"user {user['user_id']}"
            lines.append(
                f"{medal} {name} — {user['message_count']} повідомлень, {user['question_count']} питань"
            )

        board_text = "\n".join(lines)

        # Mom insult king
        mom_king = max(top, key=lambda u: u.get("mom_insult_count", 0), default=None)
        if mom_king and mom_king.get("mom_insult_count", 0) > 0:
            mom_name = f"@{mom_king['username']}" if mom_king.get("username") else f"user {mom_king['user_id']}"
            board_text += f"\n\n👩 Найбільше трахнув маму бота: {mom_name} ({mom_king['mom_insult_count']} раз)"

        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                max_tokens=150,
                messages=[
                    {
                        "role": "system",
                        "content": "Ти коментатор PUBG-команди. Коротко, по-українськи, з гумором.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Ось топ активності:\n{board_text}\n\n"
                            "Додай короткий смішний коментар до всього рейтингу (1-2 речення)."
                        ),
                    },
                ],
            )
            return f"{board_text}\n\n{response.choices[0].message.content}"
        except Exception as e:
            logger.error(f"Top text AI error: {e}")
            return board_text

    async def get_role(self, user_id: int, username: str | None, stats: dict) -> str:
        """AI assigns a social role based on aggregated behavioral metrics."""
        name = f"@{username}" if username else f"user {user_id}"
        avg_len = stats["total_chars"] // stats["message_count"] if stats["message_count"] else 0

        metrics = (
            f"Користувач: {name}\n"
            f"Повідомлень за тиждень: {stats['message_count']}\n"
            f"Середня довжина: {avg_len} символів\n"
            f"Коротких (<50): {stats['short_count']}\n"
            f"Середніх (50-200): {stats['medium_count']}\n"
            f"Довгих (>200): {stats['long_count']}\n"
            f"Медіа: {stats['media_count']}\n"
            f"Питань: {stats['question_count']}\n"
            f"Активних днів: {stats['active_days']}\n"
            f"Тегів бота: {stats['bot_mentions']}\n"
            f"Відповідей боту: {stats['bot_replies']}\n"
            f"Матів: {stats['swear_count']}"
        )

        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                max_tokens=150,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ти визначаєш соціальні ролі в PUBG-чаті на основі метрик поведінки. "
                            "Можливі ролі: 🧠 Стратег, 🔥 Провокатор, 😂 Мемолог, 💤 Спостерігач, "
                            "💬 Балакун, 💼 Бізнес-мозок, 👻 Привид, 🤖 Улюбленець бота, "
                            "🗣️ Провокатор бота, 💞 Найкращий друг бота. "
                            "Відповідай: [РОЛЬ] — [пояснення 1-2 речення по-українськи]."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Визнач роль для цього учасника:\n{metrics}",
                    },
                ],
            )
            return f"🎭 Роль {name}:\n{response.choices[0].message.content}"
        except Exception as e:
            logger.error(f"Role AI error: {e}")
            return f"Не вдалося визначити роль для {name} 🤷"

    async def generate_weekly_report(self, all_stats: list[dict], booking_stats: list[dict]) -> str:
        """Generate full Sunday weekly AI report."""
        if not all_stats:
            return "📊 Тижневий звіт: цього тижня чат мовчав 💀"

        top3 = all_stats[:3]
        top_names = ", ".join(
            f"@{u['username']}" if u.get("username") else f"user {u['user_id']}"
            for u in top3
        )
        total_messages = sum(u["message_count"] for u in all_stats)
        total_questions = sum(u["question_count"] for u in all_stats)
        total_media = sum(u["media_count"] for u in all_stats)

        stats_summary = (
            f"Учасників активних: {len(all_stats)}\n"
            f"Загалом повідомлень: {total_messages}\n"
            f"Питань поставлено: {total_questions}\n"
            f"Медіа надіслано: {total_media}\n"
            f"Топ-3 активних: {top_names}\n"
        )

        if booking_stats:
            top_players = booking_stats[:3]
            players_str = ", ".join(
                f"@{p['username']} ({p['played']} ігор)" for p in top_players
            )
            stats_summary += f"Топ гравці тижня: {players_str}\n"

        try:
            response = await self._client.chat.completions.create(
                model=_MODEL,
                max_tokens=350,
                messages=[
                    {
                        "role": "system",
                        "content": "Ти ведучий тижневого підсумку PUBG-команди. Пиши по-українськи, з гумором та драмою.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Зроби тижневий підсумок чату на основі цих даних:\n{stats_summary}\n"
                            "Формат: вітання, хто герой тижня і чому, кого треба більше бачити в чаті, "
                            "загальний вайб тижня, мотивація на наступний тиждень. Будь смішним і трохи драматичним."
                        ),
                    },
                ],
            )
            return f"📊 Тижневий звіт команди:\n\n{response.choices[0].message.content}"
        except Exception as e:
            logger.error(f"Weekly report AI error: {e}")
            return f"📊 Тижневий звіт:\n\n{stats_summary}"


analytics_service: AnalyticsService | None = None
if config.ai_enabled and config.groq_api_key:
    analytics_service = AnalyticsService()
