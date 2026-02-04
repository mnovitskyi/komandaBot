from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import config
from bot.database.models import Base, Game

engine = create_async_engine(config.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
