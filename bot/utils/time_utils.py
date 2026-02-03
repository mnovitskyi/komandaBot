from datetime import datetime, date, time, timedelta
import pytz

from bot.config import config


def get_timezone():
    """Get configured timezone."""
    return pytz.timezone(config.timezone)


def now() -> datetime:
    """Get current datetime in configured timezone."""
    return datetime.now(get_timezone())


def get_week_start(dt: datetime | None = None) -> date:
    """Get Monday of the current week."""
    if dt is None:
        dt = now()
    return (dt - timedelta(days=dt.weekday())).date()


def get_day_name(day: str) -> str:
    """Get Ukrainian day name."""
    names = {
        "saturday": "Субота",
        "sunday": "Неділя",
    }
    return names.get(day, day)


def get_day_date(day: str, week_start: date) -> date:
    """Get date for the specified day of the week."""
    days_offset = {
        "saturday": 5,
        "sunday": 6,
    }
    return week_start + timedelta(days=days_offset.get(day, 0))


def format_date(d: date) -> str:
    """Format date as 'day month' in Ukrainian."""
    months = [
        "",
        "січня",
        "лютого",
        "березня",
        "квітня",
        "травня",
        "червня",
        "липня",
        "серпня",
        "вересня",
        "жовтня",
        "листопада",
        "грудня",
    ]
    return f"{d.day} {months[d.month]}"


def parse_time(time_str: str) -> time | None:
    """Parse time string in HH:MM format."""
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0

        # Handle 24:00 as 00:00
        if hour == 24:
            hour = 0

        return time(hour=hour, minute=minute)
    except (ValueError, IndexError):
        return None


def format_time(t: time) -> str:
    """Format time as HH:MM."""
    return t.strftime("%H:%M")


def format_time_range(time_from: time, time_to: time) -> str:
    """Format time range as HH:MM-HH:MM."""
    return f"{format_time(time_from)}-{format_time(time_to)}"


def is_valid_time_range(time_from: time, time_to: time) -> bool:
    """Check if time_to is after time_from (accounting for midnight)."""
    from_minutes = time_from.hour * 60 + time_from.minute
    to_minutes = time_to.hour * 60 + time_to.minute

    # 00:00 means midnight (end of day)
    if to_minutes == 0:
        to_minutes = 1440

    return to_minutes > from_minutes


def calculate_optimal_time(
    bookings: list,
) -> tuple[time, time] | None:
    """Find time window when all booked players can play."""
    if not bookings:
        return None

    # Filter only confirmed bookings
    confirmed = [b for b in bookings if b.status == "confirmed"]
    if not confirmed:
        return None

    # Handle midnight crossing (time_to can be 00:00 meaning midnight)
    def to_minutes(t: time, is_end: bool = False) -> int:
        minutes = t.hour * 60 + t.minute
        # If it's end time and it's 00:00, treat as 24:00 (1440 minutes)
        if is_end and minutes == 0:
            return 1440
        return minutes

    def from_minutes(minutes: int) -> time:
        if minutes >= 1440:
            return time(0, 0)
        return time(minutes // 60, minutes % 60)

    latest_start = max(to_minutes(b.time_from) for b in confirmed)
    earliest_end = min(to_minutes(b.time_to, is_end=True) for b in confirmed)

    if latest_start < earliest_end:
        return (from_minutes(latest_start), from_minutes(earliest_end))

    return None
