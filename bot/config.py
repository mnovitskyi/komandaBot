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

    @classmethod
    def from_env(cls) -> "Config":
        chat_id_str = os.getenv("CHAT_ID")
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            database_url=os.getenv(
                "DATABASE_URL", "sqlite+aiosqlite:///./bot.db"
            ),
            chat_id=int(chat_id_str) if chat_id_str else None,
            timezone=os.getenv("TIMEZONE", "Europe/Warsaw"),
        )


config = Config.from_env()
