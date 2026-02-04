"""Middleware to restrict bot to specific chat only."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.config import config
import logging

logger = logging.getLogger(__name__)


class ChatFilterMiddleware(BaseMiddleware):
    """Only allow bot to work in configured chat."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get chat_id from event
        chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
        
        # If CHAT_ID is not configured, allow all chats (for initial setup)
        if config.chat_id is None:
            return await handler(event, data)
        
        # Only allow configured chat
        if chat_id != config.chat_id:
            logger.warning(f"Blocked request from unauthorized chat: {chat_id}")
            return None
        
        return await handler(event, data)
