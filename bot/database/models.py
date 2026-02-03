from datetime import datetime, date, time
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    max_slots: Mapped[int] = mapped_column(Integer, nullable=False)

    sessions: Mapped[list["Session"]] = relationship(back_populates="game")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    day: Mapped[str] = mapped_column(String(10), nullable=False)  # "saturday" / "sunday"
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False
    )  # "open" / "closed"
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    game: Mapped["Game"] = relationship(back_populates="sessions")
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    time_from: Mapped[time] = mapped_column(Time, nullable=False)
    time_to: Mapped[time] = mapped_column(Time, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", nullable=False
    )  # "confirmed" / "waitlist" / "cancelled"
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="bookings")


class BookingHistory(Base):
    __tablename__ = "booking_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    game: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "booked" / "cancelled" / "played"
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
