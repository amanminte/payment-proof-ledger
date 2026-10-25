"""Daily / weekly / monthly totals (FR-06, FR-07, BRU-04)."""
from datetime import timedelta

from . import db
from .timeutil import now_utc, parse, to_local


def _blank():
    return {"count": 0, "total": 0.0, "profit": 0.0, "with_cost": 0}


def summary(now=None):
    now = now or now_utc()
    today = to_local(now).date()
    out = {"today": _blank(), "week": _blank(), "month": _blank()}
    daily = {today - timedelta(days=i): _blank() for i in range(7)}
    for s in db.query("SELECT amount, cost, verified_at FROM sales WHERE status='verified'"):
        d = to_local(parse(s["verified_at"])).date()
        buckets = []
        if d == today:
            buckets.append(out["today"])
        if today - timedelta(days=6) <= d <= today:
            buckets.append(out["week"])
            buckets.append(daily[d])
        if (d.year, d.month) == (today.year, today.month):
            buckets.append(out["month"])
        for b in buckets:
            b["count"] += 1
            b["total"] += s["amount"]
            if s["cost"] is not None:
                b["with_cost"] += 1
                b["profit"] += s["amount"] - s["cost"]
    return {"periods": out, "daily": sorted(daily.items(), reverse=True)}
