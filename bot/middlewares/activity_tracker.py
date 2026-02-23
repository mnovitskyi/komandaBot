"""Middleware to track user activity metrics. Raw text is never stored."""
import logging
import re
from datetime import date, datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.database.session import async_session
from bot.database.repositories import UserActivityRepository
from bot.utils.time_utils import get_timezone

logger = logging.getLogger(__name__)

# Ukrainian profanity word list. Only the count is stored — raw text is never persisted.
_SWEAR_WORDS = frozenset({
    "бля", "блядей", "блядина", "блядота", "блядство", "блядська", "блядь",
    "блядів", "блять",
    "найобувати", "найобують", "найобує", "найобщик", "найобщиця",
    "найопувати", "найопують", "найопує", "найопщик", "найопщиця",
    "напзиділи", "напиздів", "напизділа", "напіздив", "напіздила", "напіздили",
    "нах", "нахуй", "нахуя", "нахєр", "нахєра",
    "наєбав", "наєбала", "наєбали", "наєбати",
    "наїбав", "наїбала", "наїбали", "наїбати",
    "пизд", "пизда", "пиздато", "пиздець", "пизди", "пиздолиз",
    "пиздолизить", "пиздолизня", "пиздоти", "пиздуємо",
    "пососав", "пососати", "пососи",
    "похуй", "похую", "похуям", "поєбать", "пройоб", "проєбали",
    "пізда", "піздата", "піздати", "піздато", "піздаті", "піздец", "піздець",
    "піздиш", "піздолиз", "піздолизня", "піздота", "піздотой", "піздотою",
    "піздти", "пізду", "піздує", "піздуємо", "піздуєте",
    "піздюк", "піздюки", "піздюків",
    "пісюн", "пісюна", "пісюни", "пісюнів", "піхуй",
    "соси", "сук", "сука", "суки", "сукою",
    "сучара", "сучарами", "сучарою", "сучий", "сучка", "сучок", "сучці",
    "уйоб", "уйобина", "уйобище", "уйобок", "уйобство",
    "уїбати", "уїбатись", "уїбатися", "уїбаться",
    "хер", "херовий", "херово", "хером",
    "хуй", "хуйло", "хуйлопан", "хуйовий", "хуйово", "хуйом", "хуя",
    "хуяльник", "хуяльнік", "хуями",
    "хуєвий", "хуєм", "хуєсос", "хуєсосити", "хуєсосний", "хуї", "хуїв", "хєр",
    "підар", "підор", "підарас", "підараси", "підарів", "підори", "підорас",
    "єбобо", "єбучий",
    "їбав", "їбала", "їбали", "їбальний", "їбальник", "їбальнику",
    "їбана", "їбанат", "їбанута", "їбанути", "їбанутий", "їбанутись", "їбанько",
    "їбати", "їбатись", "їбатися", "їбе", "їбеш", "їблана", "їблани",
    # Latin transliterations
    "khuy", "huy", "xuy", "khuyna", "khuilo",
    "pizda", "pyzda", "pizdec", "pizdets",
    "yibaty", "yibat", "yiban", "yibana",
    "yebat", "yebaty", "yeban",
    "blyad", "bliad",
    "suka",
    "pidar", "pidor", "pidaras",
    "mudak",
    "zalupa",
    "nakhuy", "nahuy",
})


class ActivityTrackerMiddleware(BaseMiddleware):
    """Extract behavioral metrics from each message and persist to DB. No text stored."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            await self._track(event)
        return await handler(event, data)

    async def _track(self, message: Message):
        if not message.from_user or message.from_user.is_bot:
            return
        if message.text and message.text.startswith("/"):
            return

        try:
            bot_info = await message.bot.me()
            bot_username = bot_info.username or ""
            bot_id = bot_info.id

            text = message.text or message.caption or ""
            length = len(text)
            has_media = bool(message.photo or message.video or message.sticker)
            has_question = "?" in text
            hour = datetime.now(get_timezone()).hour
            bot_mention = bool(bot_username and f"@{bot_username}" in text)
            bot_reply = bool(
                message.reply_to_message
                and message.reply_to_message.from_user
                and message.reply_to_message.from_user.id == bot_id
            )
            words = set(re.split(r"\W+", text.lower()))
            has_swear = bool(words & _SWEAR_WORDS)

            async with async_session() as db:
                repo = UserActivityRepository(db)
                await repo.upsert_message(
                    user_id=message.from_user.id,
                    username=message.from_user.username,
                    msg_date=date.today(),
                    length=length,
                    has_media=has_media,
                    has_question=has_question,
                    hour=hour,
                    bot_mention=bot_mention,
                    bot_reply=bot_reply,
                    has_swear=has_swear,
                )
        except Exception as e:
            logger.error(f"Activity tracker error: {e}")
