"""Scheduler service (plan §5.8, §5.3 step 4).

Greedy bin-packing of roadmap items into the user's weekly availability,
respecting topic DAG order. Reserves a configurable buffer per week for
spaced-repetition review / catch-up.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, date


_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _iso_weekday_to_index(d: int) -> int:
    """Python's date.weekday(): Mon=0..Sun=6 (already our convention)."""
    return d


def availability_for_user(user_id: int, model_cls) -> dict[int, int]:
    """Return {day_index: available_minutes} for the user."""
    rows = model_cls.query.filter_by(user_id=user_id).all()
    if rows:
        return {r.day_of_week: r.available_minutes for r in rows}
    # default: 60 min/day every day if none set
    return {d: 60 for d in range(7)}


def schedule_items(items: list[dict], availability: dict[int, int],
                   start_date: date | None = None,
                   buffer_percent: float = 0.20) -> list[dict]:
    """Bin-pack items into the weekly availability.

    `items` is an ordered list (already DAG-sorted) of dicts like:
        {"id":..., "estimated_minutes":int, "topic_id":..., "item_type":...}
    Each item is annotated in-place with `scheduled_date` (a datetime) and
    returned.

    20% of each day's budget is reserved for review/catch-up by default.
    """
    start = start_date or date.today()
    # Build a rolling queue of (date, minutes_left) starting from start_date,
    # skipping days with zero availability.
    items = list(items)  # don't mutate caller's list reference content order
    queue = deque(items)
    scheduled: list[dict] = []

    if not queue:
        return scheduled

    usable_fraction = max(0.0, 1.0 - buffer_percent)
    # Safety cap so a runaway loop doesn't hang the process
    max_iterations = max(1000, len(items) * 50)
    iters = 0

    current = start
    while queue and iters < max_iterations:
        iters += 1
        day_idx = _iso_weekday_to_index(current.weekday())
        budget = int(availability.get(day_idx, 0) * usable_fraction)
        if budget <= 0:
            current += timedelta(days=1)
            continue

        while budget > 0 and queue:
            item = queue[0]
            est = int(item.get("estimated_minutes", 30) or 30)
            if est > budget:
                # Big item: split across days? For MVP, carry forward to a
                # future day that has enough budget; but allow placing on
                # this day if queue would otherwise stall (single big item).
                # Simple heuristic: place it today only if this is the only
                # remaining item AND no smaller items follow.
                # Otherwise leave for next day.
                if len(queue) == 1:
                    item["scheduled_date"] = datetime.combine(
                        current, datetime.min.time())
                    item["order_index"] = len(scheduled)
                    scheduled.append(item)
                    queue.popleft()
                break
            item["scheduled_date"] = datetime.combine(current, datetime.min.time())
            item["order_index"] = len(scheduled)
            scheduled.append(item)
            queue.popleft()
            budget -= est
        current += timedelta(days=1)

    # Fallback: if any items couldn't be packed (e.g. all-zero availability),
    # drop them on consecutive days starting from `start`.
    if queue:
        fallback_day = start
        for item in queue:
            item["scheduled_date"] = datetime.combine(
                fallback_day, datetime.min.time())
            item["order_index"] = len(scheduled)
            scheduled.append(item)
            fallback_day += timedelta(days=1)

    scheduled.sort(key=lambda x: (x["scheduled_date"], x["order_index"]))
    return scheduled
