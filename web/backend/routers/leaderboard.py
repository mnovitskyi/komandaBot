from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import UserActivity
from web.backend.database import get_db
from web.backend.xp import calculate_xp, get_level

router = APIRouter()


@router.get("/leaderboard")
async def get_leaderboard(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    result = await db.execute(select(UserActivity))
    rows = result.scalars().all()

    aggregated: dict[int, dict[str, Any]] = defaultdict(lambda: {
        "user_id": 0,
        "username": "",
        "message_count": 0,
        "total_chars": 0,
        "bot_mentions": 0,
        "bot_replies": 0,
        "mom_insult_count": 0,
        "fire_reactions": 0,
        "heart_reactions": 0,
        "swear_count": 0,
    })

    for row in rows:
        uid = row.user_id
        agg = aggregated[uid]
        agg["user_id"] = uid
        if row.username:
            agg["username"] = row.username
        agg["message_count"] += row.message_count
        agg["total_chars"] += row.total_chars
        agg["bot_mentions"] += row.bot_mentions
        agg["bot_replies"] += row.bot_replies
        agg["mom_insult_count"] += row.mom_insult_count
        agg["fire_reactions"] += row.fire_reactions
        agg["heart_reactions"] += row.heart_reactions
        agg["swear_count"] += row.swear_count

    leaderboard_data = []
    for uid, stats in aggregated.items():
        xp = calculate_xp(stats)
        level_info = get_level(xp)
        leaderboard_data.append({
            **stats,
            "xp": xp,
            "level_num": level_info["level_num"],
            "level_name": level_info["level_name"],
            "level_emoji": level_info["level_emoji"],
            "xp_to_next": level_info["xp_to_next"],
            "progress": level_info["progress"],
            "is_max": level_info["is_max"],
        })

    leaderboard_data.sort(key=lambda x: x["xp"], reverse=True)
    return leaderboard_data
