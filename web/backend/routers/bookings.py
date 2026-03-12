from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Session as GameSession, Booking, Game
from web.backend.database import get_db

router = APIRouter()


@router.get("/bookings")
async def get_bookings(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(
        select(GameSession)
        .where(GameSession.status == "open")
        .options(
            selectinload(GameSession.game),
            selectinload(GameSession.bookings),
        )
        .order_by(GameSession.created_at.desc())
    )
    sessions = result.scalars().all()

    output = []
    for session in sessions:
        confirmed_bookings = [b for b in session.bookings if b.status == "confirmed"]
        waitlist_bookings = [b for b in session.bookings if b.status == "waitlist"]

        output.append({
            "session_id": session.id,
            "game_name": session.game.name if session.game else "Unknown",
            "max_slots": session.game.max_slots if session.game else 0,
            "day": session.day,
            "week_start": str(session.week_start),
            "status": session.status,
            "confirmed_count": len(confirmed_bookings),
            "confirmed": [
                {
                    "username": b.username,
                    "time_from": str(b.time_from),
                    "time_to": str(b.time_to),
                    "position": b.position,
                }
                for b in sorted(confirmed_bookings, key=lambda x: x.position)
            ],
            "waitlist": [
                {
                    "username": b.username,
                    "time_from": str(b.time_from),
                    "time_to": str(b.time_to),
                    "position": b.position,
                }
                for b in sorted(waitlist_bookings, key=lambda x: x.position)
            ],
        })

    return output
