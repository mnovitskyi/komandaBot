from typing import TypedDict

LEVELS = [
    (0,    "Не вилупився"),
    (50,   "Курча"),
    (150,  "Диванний стратег"),
    (350,  "Пивний аналітик"),
    (700,  "Збройний мудак"),
    (1200, "Кемпер-підар"),
    (2000, "Ходячий труп"),
    (3000, "Гроза маминих ботів"),
    (5000, "Король хаосу"),
    (8000, "Трахнув маму бота"),
]

LEVEL_EMOJIS = [
    "🥚", "🐣", "🎮", "🍺", "🔫", "🏕", "💀", "🤬", "👑", "🍗"
]


def calculate_xp(stats: dict) -> int:
    xp = 0
    xp += stats.get("message_count", 0)
    xp += stats.get("total_chars", 0) // 100
    xp += (stats.get("bot_mentions", 0) + stats.get("bot_replies", 0)) * 3
    xp += stats.get("mom_insult_count", 0) * 5
    xp += stats.get("fire_reactions", 0) * 2
    xp += stats.get("heart_reactions", 0)
    return xp


class LevelInfo(TypedDict):
    level_num: int
    level_name: str
    level_emoji: str
    xp_to_next: int
    progress: int
    is_max: bool


def get_level(xp: int) -> LevelInfo:
    current_level_num = 0
    current_threshold = 0
    current_name = LEVELS[0][1]

    for i, (threshold, name) in enumerate(LEVELS):
        if xp >= threshold:
            current_level_num = i
            current_threshold = threshold
            current_name = name
        else:
            break

    is_max = current_level_num == len(LEVELS) - 1

    if is_max:
        xp_to_next = 0
        progress = 100
    else:
        next_threshold = LEVELS[current_level_num + 1][0]
        xp_in_level = xp - current_threshold
        level_range = next_threshold - current_threshold
        xp_to_next = next_threshold - xp
        progress = min(100, int((xp_in_level / level_range) * 100))

    return LevelInfo(
        level_num=current_level_num,
        level_name=f"{LEVEL_EMOJIS[current_level_num]} {current_name}",
        level_emoji=LEVEL_EMOJIS[current_level_num],
        xp_to_next=xp_to_next,
        progress=progress,
        is_max=is_max,
    )
