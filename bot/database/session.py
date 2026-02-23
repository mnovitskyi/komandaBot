from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import config
from bot.database.models import Base, Game

# Create async engine
engine = create_async_engine(
    config.database_url, 
    echo=False
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Add columns introduced after initial deployment (PostgreSQL only).
        # create_all skips existing tables so new columns must be added manually.
        if engine.dialect.name == "postgresql":
            migrations = [
                "ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS swear_count INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS mom_insult_count INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS fire_reactions INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS heart_reactions INTEGER NOT NULL DEFAULT 0",
            ]
            for sql in migrations:
                await conn.execute(text(sql))

    # Seed default games
    async with async_session() as session:
        from sqlalchemy import select

        result = await session.execute(select(Game))
        if not result.scalars().first():
            session.add(Game(name="PUBG", max_slots=4))
            await session.commit()


async def get_session() -> AsyncSession:
    """Get a new database session."""
    async with async_session() as session:
        yield session
