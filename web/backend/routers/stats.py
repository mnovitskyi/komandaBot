from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import UserActivity
from web.backend.database import get_db

router = APIRouter()


@router.get("/stats/week")
async def get_week_stats(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    seven_days_ago = date.today() - timedelta(days=7)
    result = await db.execute(
        select(UserActivity).where(UserActivity.date >= seven_days_ago)
    )
    rows = result.scalars().all()

    aggregated: dict[int, dict[str, Any]] = defaultdict(lambda: {
        "user_id": 0,
        "username": "",
        "message_count": 0,
        "swear_count": 0,
        "mom_insult_count": 0,
        "fire_reactions": 0,
        "heart_reactions": 0,
        "bot_mentions": 0,
        "bot_replies": 0,
        "active_days": 0,
    })

    for row in rows:
        uid = row.user_id
        agg = aggregated[uid]
        agg["user_id"] = uid
        if row.username:
            agg["username"] = row.username
        agg["message_count"] += row.message_count
        agg["swear_count"] += row.swear_count
        agg["mom_insult_count"] += row.mom_insult_count
        agg["fire_reactions"] += row.fire_reactions
        agg["heart_reactions"] += row.heart_reactions
        agg["bot_mentions"] += row.bot_mentions
        agg["bot_replies"] += row.bot_replies
        if row.message_count > 0:
            agg["active_days"] += 1

    result_list = list(aggregated.values())
    result_list.sort(key=lambda x: x["message_count"], reverse=True)
    return result_list


@router.get("/stats/cursed")
async def get_cursed_stats(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    result = await db.execute(select(UserActivity))
    rows = result.scalars().all()

    agg_swears: dict[int, dict[str, Any]] = defaultdict(lambda: {"user_id": 0, "username": "", "count": 0})
    agg_mom: dict[int, dict[str, Any]] = defaultdict(lambda: {"user_id": 0, "username": "", "count": 0})
    agg_bot: dict[int, dict[str, Any]] = defaultdict(lambda: {"user_id": 0, "username": "", "count": 0})
    agg_night: dict[int, dict[str, Any]] = defaultdict(lambda: {"user_id": 0, "username": "", "count": 0})
    agg_total_msgs: dict[int, dict[str, Any]] = defaultdict(lambda: {"user_id": 0, "username": "", "count": 0})

    for row in rows:
        uid = row.user_id
        username = row.username or f"user_{uid}"

        agg_swears[uid]["user_id"] = uid
        agg_swears[uid]["username"] = username
        agg_swears[uid]["count"] += row.swear_count

        agg_mom[uid]["user_id"] = uid
        agg_mom[uid]["username"] = username
        agg_mom[uid]["count"] += row.mom_insult_count

        agg_bot[uid]["user_id"] = uid
        agg_bot[uid]["username"] = username
        agg_bot[uid]["count"] += row.bot_mentions + row.bot_replies

        agg_total_msgs[uid]["user_id"] = uid
        agg_total_msgs[uid]["username"] = username
        agg_total_msgs[uid]["count"] += row.message_count

        # Night owl: count days where active hours contain 0-5
        if row.active_hours:
            hours = [h.strip() for h in row.active_hours.split(",") if h.strip()]
            night_hours = {"0", "1", "2", "3", "4", "5"}
            if any(h in night_hours for h in hours):
                agg_night[uid]["user_id"] = uid
                agg_night[uid]["username"] = username
                agg_night[uid]["count"] += 1

    def top_user(agg: dict) -> dict[str, Any]:
        if not agg:
            return {"username": "???", "count": 0}
        best = max(agg.values(), key=lambda x: x["count"])
        return {"username": best["username"] or f"user_{best['user_id']}", "count": best["count"]}

    top_chatters_raw = sorted(agg_total_msgs.values(), key=lambda x: x["count"], reverse=True)[:5]
    top_chatters = [
        {"username": u["username"] or f"user_{u['user_id']}", "count": u["count"]}
        for u in top_chatters_raw
    ]

    return {
        "swear_king": top_user(agg_swears),
        "mom_insulter": top_user(agg_mom),
        "bot_stalker": top_user(agg_bot),
        "night_owl": top_user(agg_night),
        "top_chatters": top_chatters,
    }
