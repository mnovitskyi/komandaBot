import logging

from aiogram import Router, F
from aiogram.types import Message

from bot.services.ai_chat import ai_service

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text, ~F.text.startswith("/"))
async def handle_ai_message(message: Message):
    """Handle regular text messages with AI replies."""
    if not ai_service or not message.text:
        return

    # Determine if this is a direct interaction (reply to bot or mention)
    is_direct = False
    bot_info = await message.bot.me()

    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot_info.id:
            is_direct = True

    if bot_info.username and f"@{bot_info.username}" in message.text:
        is_direct = True

    if not ai_service.should_reply(is_direct):
        return

    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    reply = await ai_service.generate_reply(
        message_text=message.text,
        username=username,
        first_name=first_name,
    )

    if reply:
        await message.reply(reply, disable_notification=True)
