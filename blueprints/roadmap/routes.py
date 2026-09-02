"""Roadmap viewing, timetable calendar & schedule block customization.

Routes:
  /roadmap                      full roadmap (phases/topics, progress)
  /roadmap/calendar             interactive 14-day timetable/calendar view
  /roadmap/availability         edit daily 2-3hr schedule time blocks
  /roadmap/replan (POST)        re-run the roadmap engine
  /roadmap/item/<id>/move (POST) move item to new date and time slot
"""
from __future__ import annotations

import json
from collections import OrderedDict
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, g, jsonify
from extensions import db
from models import Roadmap, RoadmapItem, Topic, WeeklyAvailability

from services.roadmap_engine import replan_roadmap, generate_roadmap
from services.scheduler_service import DEFAULT_TIME_BLOCKS, blocks_for_user_day

roadmap_bp = Blueprint("roadmap", __name__)


def _active_roadmap():
    return Roadmap.query.filter_by(
        user_id=g.user.id, status="active").first()


@roadmap_bp.route("/roadmap")
def view():
    roadmap = _active_roadmap()
    if roadmap is None:
        flash("Generate a roadmap to get started.", "info")
        return redirect(url_for("job_roles.browse"))

    # Group items by topic
    groups: OrderedDict[int, dict] = OrderedDict()
    for it in sorted(roadmap.items, key=lambda i: (i.scheduled_date or date.min,
                                                   i.order_index)):
        tid = it.topic_id or 0
        g_item = groups.setdefault(tid, {
            "topic": Topic.query.get(tid) if tid else None,
            "items": [],
            "total": 0, "done": 0,
        })
        g_item["items"].append(it)
        g_item["total"] += 1
        if it.status == "done":
            g_item["done"] += 1

    return render_template("roadmap/view.html", roadmap=roadmap, groups=groups)


@roadmap_bp.route("/roadmap/calendar")
def calendar():
    roadmap = _active_roadmap()
    if roadmap is None:
        return redirect(url_for("job_roles.browse"))

    # 14-day forward calendar view with time blocks
    start = date.today()
    day_buckets = []
    
    for d in range(14):
        day = start + timedelta(days=d)
        day_idx = day.weekday()
        user_blocks = blocks_for_user_day(g.user.id, day_idx, WeeklyAvailability)
        
        tasks = [i for i in roadmap.items if i.scheduled_date and
                 i.scheduled_date.date() == day]
        
        day_buckets.append({
            "date": day,
            "day_idx": day_idx,
            "blocks": user_blocks,
            "tasks": tasks
        })

    # Available time slots for select dropdown
    preset_slots = [
        "09:00-11:30 (Morning Block - 2.5h)",
        "14:00-16:30 (Afternoon Block - 2.5h)",
        "19:00-21:30 (Evening Block - 2.5h)"
    ]

    return render_template("roadmap/calendar.html",
                           days=day_buckets,
                           roadmap=roadmap,
                           preset_slots=preset_slots)


@roadmap_bp.route("/roadmap/availability", methods=["GET", "POST"])
def availability():
    """Configure modifiable daily schedule with 2-3hr blocks."""
    if request.method == "POST":
        for day_idx in range(7):
            block1_start = request.form.get(f"day_{day_idx}_b1_start", "09:00")
            block1_end = request.form.get(f"day_{day_idx}_b1_end", "11:30")
            block2_start = request.form.get(f"day_{day_idx}_b2_start", "14:00")
            block2_end = request.form.get(f"day_{day_idx}_b2_end", "16:30")
            
            blocks = [
                {"name": "Morning Block", "start": block1_start, "end": block1_end, "duration_minutes": 150},
                {"name": "Afternoon Block", "start": block2_start, "end": block2_end, "duration_minutes": 150},
            ]
            
            row = WeeklyAvailability.query.filter_by(user_id=g.user.id, day_of_week=day_idx).first()
            if not row:
                row = WeeklyAvailability(user_id=g.user.id, day_of_week=day_idx)
                db.session.add(row)
            
            row.available_minutes = 300
            row.time_blocks = json.dumps(blocks)
        
        db.session.commit()
        
        # Trigger replan to apply new timetable
        roadmap = _active_roadmap()
        if roadmap:
            replan_roadmap(roadmap)
            db.session.commit()
            
        flash("Your daily schedule blocks have been updated!", "success")
        return redirect(url_for("roadmap.calendar"))

    # GET request
    user_availability = {}
    for day_idx in range(7):
        blocks = blocks_for_user_day(g.user.id, day_idx, WeeklyAvailability)
        user_availability[day_idx] = blocks

    days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return render_template("onboarding/availability.html",
                           availability=user_availability,
                           days_names=days_names)


@roadmap_bp.route("/roadmap/replan", methods=["POST"])
def replan():
    roadmap = _active_roadmap()
    if roadmap is None:
        return redirect(url_for("job_roles.browse"))
    replan_roadmap(roadmap)
    db.session.commit()
    flash("Your roadmap has been recalculated.", "success")
    return redirect(url_for("roadmap.view"))


@roadmap_bp.route("/roadmap/item/<int:item_id>/move", methods=["POST"])
def move_item(item_id: int):
    item = RoadmapItem.query.get_or_404(item_id)
    if item.roadmap.user_id != g.user.id:
        abort(403)
        
    new_date = request.form.get("new_date")
    time_slot = request.form.get("time_slot")
    
    if new_date:
        try:
            item.scheduled_date = datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("roadmap.calendar"))
            
    if time_slot:
        item.time_slot = time_slot
        
    db.session.commit()
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "item_id": item.id, "new_date": new_date, "time_slot": item.time_slot})
        
    flash("Task rescheduled successfully.", "success")
    return redirect(url_for("roadmap.calendar"))
