"""Scheduler service for modifiable daily schedules with 2-3hr blocks.

Greedy bin-packing of roadmap items into the user's daily time blocks (2-3 hours each),
respecting topic DAG order. Reserves a configurable buffer for review / catch-up.
"""
from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timedelta, date

_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Default 2-3 hour schedule blocks per day (e.g. 2.5 hr Morning block, 2.5 hr Afternoon block)
DEFAULT_TIME_BLOCKS = [
    {"name": "Morning Block", "start": "09:00", "end": "11:30", "duration_minutes": 150},
    {"name": "Afternoon Block", "start": "14:00", "end": "16:30", "duration_minutes": 150},
]


def _iso_weekday_to_index(d: int) -> int:
    return d


def availability_for_user(user_id: int, model_cls) -> dict[int, int]:
    """Return {day_index: available_minutes} for the user."""
    rows = model_cls.query.filter_by(user_id=user_id).all()
    if rows:
        result = {}
        for r in rows:
            if r.time_blocks:
                try:
                    blocks = json.loads(r.time_blocks)
                    total_min = sum(int(b.get("duration_minutes", 120)) for b in blocks)
                    result[r.day_of_week] = total_min if total_min > 0 else r.available_minutes
                except (json.JSONDecodeError, TypeError):
                    result[r.day_of_week] = r.available_minutes
            else:
                result[r.day_of_week] = r.available_minutes
        return result
    # Default: 300 minutes per day (two 2.5-hour blocks)
    return {d: 300 for d in range(7)}


def blocks_for_user_day(user_id: int, day_of_week: int, model_cls) -> list[dict]:
    """Return configured time blocks for a user on a given day (0=Mon ... 6=Sun)."""
    row = model_cls.query.filter_by(user_id=user_id, day_of_week=day_of_week).first()
    if row and row.time_blocks:
        try:
            blocks = json.loads(row.time_blocks)
            if blocks:
                return blocks
        except (json.JSONDecodeError, TypeError):
            pass
    return DEFAULT_TIME_BLOCKS


def schedule_items(items: list[dict], availability: dict[int, int],
                   user_id: int | None = None, model_cls=None,
                   start_date: date | None = None,
                   buffer_percent: float = 0.15) -> list[dict]:
    """Bin-pack items into daily 2-3hr time blocks.

    `items` is an ordered list (already DAG-sorted) of dicts.
    Each item is annotated with `scheduled_date` and `time_slot`.
    """
    start = start_date or date.today()
    items = list(items)
    queue = deque(items)
    scheduled: list[dict] = []

    if not queue:
        return scheduled

    usable_fraction = max(0.0, 1.0 - buffer_percent)
    max_iterations = max(1000, len(items) * 50)
    iters = 0

    current = start
    while queue and iters < max_iterations:
        iters += 1
        day_idx = _iso_weekday_to_index(current.weekday())
        
        # Get blocks for this day
        blocks = DEFAULT_TIME_BLOCKS
        if user_id and model_cls:
            blocks = blocks_for_user_day(user_id, day_idx, model_cls)
        
        total_day_budget = int(availability.get(day_idx, 300) * usable_fraction)
        if total_day_budget <= 0:
            current += timedelta(days=1)
            continue

        # Pack into blocks for the current day
        block_idx = 0
        block_minutes_remaining = int(blocks[0].get("duration_minutes", 150) * usable_fraction) if blocks else total_day_budget
        current_block = blocks[0] if blocks else {"name": "Default Block", "start": "09:00", "end": "12:00"}

        while total_day_budget > 0 and queue:
            item = queue[0]
            est = int(item.get("estimated_minutes", 30) or 30)

            if est > block_minutes_remaining:
                # Move to next time block if available today
                block_idx += 1
                if block_idx < len(blocks):
                    current_block = blocks[block_idx]
                    block_minutes_remaining = int(current_block.get("duration_minutes", 150) * usable_fraction)
                    continue
                else:
                    # No more blocks today
                    if len(queue) == 1:
                        # Place last item today
                        slot_str = f"{current_block.get('start', '09:00')}-{current_block.get('end', '12:00')} ({current_block.get('name', 'Block')})"
                        item["scheduled_date"] = datetime.combine(current, datetime.min.time())
                        item["time_slot"] = slot_str
                        item["order_index"] = len(scheduled)
                        scheduled.append(item)
                        queue.popleft()
                    break

            slot_str = f"{current_block.get('start', '09:00')}-{current_block.get('end', '12:00')} ({current_block.get('name', 'Block')})"
            item["scheduled_date"] = datetime.combine(current, datetime.min.time())
            item["time_slot"] = slot_str
            item["order_index"] = len(scheduled)
            scheduled.append(item)
            queue.popleft()

            block_minutes_remaining -= est
            total_day_budget -= est

        current += timedelta(days=1)

    # Fallback for remaining items
    if queue:
        fallback_day = start
        for item in queue:
            item["scheduled_date"] = datetime.combine(fallback_day, datetime.min.time())
            item["time_slot"] = "09:00-11:30 (Morning Block)"
            item["order_index"] = len(scheduled)
            scheduled.append(item)
            fallback_day += timedelta(days=1)

    scheduled.sort(key=lambda x: (x["scheduled_date"], x["order_index"]))
    return scheduled
