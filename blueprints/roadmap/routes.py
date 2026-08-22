"""Roadmap viewing & re-planning (plan §5.3, §5.8, §6).

  /roadmap                full roadmap (phases/topics, progress)
  /roadmap/calendar       week/month calendar with drag-reschedule (MVP: list)
  /roadmap/replan (POST)  re-run the roadmap engine (availability change/drift)
  /roadmap/item/<id>/move (POST)  move an item to a new date
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Roadmap, RoadmapItem, Topic, WeeklyAvailability

from services.roadmap_engine import replan_roadmap, generate_roadmap

roadmap_bp = Blueprint("roadmap", __name__)


def _active_roadmap():
    return Roadmap.query.filter_by(
        user_id=current_user.id, status="active").first()


@roadmap_bp.route("/roadmap")
@login_required
def view():
    roadmap = _active_roadmap()
    if roadmap is None:
        flash("Generate a roadmap from an assessment first.", "info")
        return redirect(url_for("onboarding.domain"))

    # Group items by topic for a phase-style snapshot
    groups: OrderedDict[int, dict] = OrderedDict()
    for it in sorted(roadmap.items, key=lambda i: (i.scheduled_date or date.min,
                                                   i.order_index)):
        tid = it.topic_id or 0
        g = groups.setdefault(tid, {
            "topic": Topic.query.get(tid) if tid else None,
            "items": [],
            "total": 0, "done": 0,
        })
        g["items"].append(it)
        g["total"] += 1
        if it.status == "done":
            g["done"] += 1

    return render_template("roadmap/view.html", roadmap=roadmap, groups=groups)


@roadmap_bp.route("/roadmap/calendar")
@login_required
def calendar():
    roadmap = _active_roadmap()
    if roadmap is None:
        return redirect(url_for("onboarding.domain"))

    # MVP: 14-day forward list grouped by date (full drag-drop is v2/htmx)
    start = date.today()
    end = start + timedelta(days=13)
    day_buckets = []
    for d in range(14):
        day = start + timedelta(days=d)
        tasks = [i for i in roadmap.items if i.scheduled_date and
                 i.scheduled_date.date() == day]
        day_buckets.append({"date": day, "tasks": tasks})
    return render_template("roadmap/calendar.html", days=day_buckets, roadmap=roadmap)


@roadmap_bp.route("/roadmap/replan", methods=["POST"])
@login_required
def replan():
    roadmap = _active_roadmap()
    if roadmap is None:
        return redirect(url_for("onboarding.domain"))
    replan_roadmap(roadmap)
    db.session.commit()
    flash("Your roadmap has been updated.", "success")
    return redirect(url_for("roadmap.view"))


@roadmap_bp.route("/roadmap/item/<int:item_id>/move", methods=["POST"])
@login_required
def move_item(item_id: int):
    item = RoadmapItem.query.get_or_404(item_id)
    if item.roadmap.user_id != current_user.id:
        abort(403)
    new_date = request.form.get("new_date")
    if new_date:
        try:
            item.scheduled_date = datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date.", "error")
            return redirect(url_for("roadmap.calendar"))
    db.session.commit()
    flash("Item rescheduled.", "success")
    return redirect(url_for("roadmap.calendar"))
