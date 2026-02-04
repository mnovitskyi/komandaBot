import pytest
import pytest_asyncio
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.database.models import Base, Game, Session, Booking


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def games(db_session: AsyncSession):
    """Create test games."""
    pubg = Game(name="PUBG", max_slots=4)
    db_session.add(pubg)
    await db_session.commit()
    await db_session.refresh(pubg)
    return {"pubg": pubg}


@pytest_asyncio.fixture
async def open_session(db_session: AsyncSession, games):
    """Create an open session for PUBG on Saturday."""
    session = Session(
        game_id=games["pubg"].id,
        chat_id=123456789,
        day="saturday",
        week_start=date(2024, 2, 5),
        status="open",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest_asyncio.fixture
async def full_session(db_session: AsyncSession, games):
    """Create a session with all slots filled (for waitlist testing)."""
    session = Session(
        game_id=games["pubg"].id,
        chat_id=123456789,
        day="sunday",
        week_start=date(2024, 2, 5),
        status="open",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Fill all 4 slots
    for i in range(1, 5):
        booking = Booking(
            session_id=session.id,
            user_id=1000 + i,
            username=f"user{i}",
            time_from=time(18, 0),
            time_to=time(22, 0),
            position=i,
            status="confirmed",
        )
        db_session.add(booking)

    await db_session.commit()
    return session


# Test data fixtures
@pytest.fixture
def user_data():
    """Sample user data."""
    return {
        "user_id": 999999,
        "username": "testuser",
    }


@pytest.fixture
def time_range():
    """Sample time range."""
    return {
        "time_from": time(18, 0),
        "time_to": time(22, 0),
    }
