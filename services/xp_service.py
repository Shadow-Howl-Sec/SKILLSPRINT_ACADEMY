"""XP & gamification service (plan §5.11).

Awards XP for completed roadmap items, labs, quizzes, and streak bonuses,
and maintains the per-user StreakRecord.
"""
from __future__ import annotations

from datetime import datetime, timedelta, date

from flask import current_app
from extensions import db
from models import XPLog, StreakRecord, User


# Source-type → config key for base XP award
_XP_CONFIG_KEY = {
    "roadmap_item": "XP_PER_CONTENT_ITEM",
    "lab": "XP_PER_LAB",
    "checkpoint_quiz": "XP_PER_QUIZ",
    "assessment": "XP_PER_QUIZ",  # reuse quiz XP for assessment completion
    "badge": None,                # XP is explicit in this case
    "streak_bonus": "XP_STREAK_BONUS",
}


def award_xp(user_id: int, source_type: str, source_id: int | None,
             xp_amount: int | None = None, description: str = "") -> int:
    """Record an XP award. Returns the amount awarded."""
    if xp_amount is None:
        config_key = _XP_CONFIG_KEY.get(source_type)
        if config_key is None:
            xp_amount = 0
        else:
            xp_amount = int(current_app.config.get(config_key, 0))

    if xp_amount == 0 and source_type != "badge":
        return 0

    log = XPLog(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        xp_amount=xp_amount,
        description=description,
    )
    db.session.add(log)
    db.session.flush()  # make available without full commit
    return xp_amount


def _get_or_create_streak(user_id: int) -> StreakRecord:
    rec = StreakRecord.query.filter_by(user_id=user_id).first()
    if rec is None:
        rec = StreakRecord(
            user_id=user_id,
            current_streak=0,
            longest_streak=0,
            last_active_date=None,
            freezes_available=int(current_app.config.get("STREAK_FREEZES_PER_WEEK", 1)),
        )
        db.session.add(rec)
        db.session.flush()
    return rec


def touch_streak(user_id: int, when: date | None = None) -> StreakRecord:
    """Mark the user active on `when` (default today). Updates streak counter.

    Rules (Duolingo-style):
      - Same day as last_active → no change.
      - Yesterday → +1 streak.
      - Gap of 1 day with freezes available → consume a freeze, +1 streak.
      - Larger gap → reset streak to 1 (today), refill weekly freezes if a new
        ISO week has started since last_active.
    """
    when = when or date.today()
    rec = _get_or_create_streak(user_id)
    last = rec.last_active_date.date() if rec.last_active_date else None

    if last == when:
        return rec

    # Refill freezes if a new ISO week started since the last active date.
    if last is not None and when.isocalendar()[1] != last.isocalendar()[1]:
        rec.freezes_available = int(current_app.config.get("STREAK_FREEZES_PER_WEEK", 1))

    if last is None:
        rec.current_streak = 1
    else:
        gap = (when - last).days
        if gap == 1:
            rec.current_streak += 1
        elif gap == 2 and rec.freezes_available > 0:
            rec.freezes_available -= 1
            rec.current_streak += 1
        else:
            rec.current_streak = 1

    if rec.current_streak > rec.longest_streak:
        rec.longest_streak = rec.current_streak
    rec.last_active_date = datetime.combine(when, datetime.min.time())
    db.session.flush()
    return rec
