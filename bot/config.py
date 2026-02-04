import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    database_url: str
    chat_id: int | None
    timezone: str
    admin_ids: list[int]

    @classmethod
    def from_env(cls) -> "Config":
        chat_id_str = os.getenv("CHAT_ID")
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
        
        # Convert postgresql:// to postgresql+asyncpg:// for Railway
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Parse admin IDs from comma-separated string
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            database_url=database_url,
            chat_id=int(chat_id_str) if chat_id_str else None,
            timezone=os.getenv("TIMEZONE", "Europe/Warsaw"),
            admin_ids=admin_ids,
        )


config = Config.from_env()
