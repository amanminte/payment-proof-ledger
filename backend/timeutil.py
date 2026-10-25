from datetime import datetime, timedelta, timezone

from . import config


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse(s):
    return datetime.fromisoformat(s)


def to_local(dt):
    return dt.astimezone(timezone(timedelta(hours=config.TZ_OFFSET_HOURS)))


def start_of_local_day(dt):
    local = to_local(dt)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)
