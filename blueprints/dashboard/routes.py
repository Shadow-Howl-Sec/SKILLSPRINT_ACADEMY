"""Dashboard (post-login "Today" home) — plan §5.9.

Provides:
  /dashboard      today view (header strip, today's schedule, continue,
                  week strip, roadmap snapshot, quick links)
  /progress       analytics: skill radar, history, streak
"""
from __future__ import annotations

from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Roadmap, RoadmapItem, StreakRecord, XPLog, SkillProfile, SkillArea

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def today():
    # If the user has no active roadmap yet, send them to onboarding.
    roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, status="active").first()
    if roadmap is None:
        flash("Let's set up your learning plan first.", "info")
        return redirect(url_for("onboarding.domain"))

    today_date = date.today()
    today_items = sorted(
        [i for i in roadmap.items if i.scheduled_date and
         i.scheduled_date.date() == today_date and i.status != "done"],
        key=lambda i: i.order_index)
    done_today = [i for i in roadmap.items if i.scheduled_date and
                  i.scheduled_date.date() == today_date and i.status == "done"]

    # Continue where you left off: first pending item overall
    next_pending = next((i for i in roadmap.items if i.status == "pending"), None)

    # Week-at-a-glance: counts of scheduled vs done per day for the next 7 days
    week = []
    for d in range(7):
        day = today_date + timedelta(days=d)
        day_items = [i for i in roadmap.items if i.scheduled_date and
                     i.scheduled_date.date() == day]
        week.append({
            "date": day,
            "label": day.strftime("%a"),
            "total": len(day_items),
            "done": sum(1 for x in day_items if x.status == "done"),
        })

    # Roadmap snapshot: % progress across phases (group by topic for now)
    total_items = len(roadmap.items) or 1
    completed = sum(1 for i in roadmap.items if i.status == "done")
    percent = int((completed / total_items) * 100)

    streak = current_user.streak_record
    xp = current_user.total_xp
    level = max(1, xp // 100 + 1)

    return render_template("dashboard/today.html",
                            roadmap=roadmap,
                            today_items=today_items,
                            done_today=done_today,
                            next_pending=next_pending,
                            week=week,
                            percent=percent,
                            streak=streak,
                            xp=xp,
                            level=level)


@dashboard_bp.route("/progress")
@login_required
def progress():
    profiles = (SkillProfile.query
                .filter_by(user_id=current_user.id)
                .join(SkillArea, SkillProfile.skill_area_id == SkillArea.id)
                .order_by(SkillArea.order_index)
                .all())
    radar = [{"label": p.skill_area.name if p.skill_area else f"area#{p.skill_area_id}",
              "score": p.score, "confidence": p.confidence}
             for p in profiles]

    streak = current_user.streak_record
    xp = current_user.total_xp
    xp_history = (XPLog.query
                  .filter_by(user_id=current_user.id)
                  .order_by(XPLog.created_at.desc())
                  .limit(20).all())

    return render_template("dashboard/progress.html", radar=radar,
                            streak=streak, xp=xp,
                            xp_history=xp_history)


@dashboard_bp.route("/roadmap-item/<int:item_id>/complete", methods=["POST"])
@login_required
def complete_item(item_id: int):
    from services.xp_service import award_xp, touch_streak
    item = RoadmapItem.query.get_or_404(item_id)
    if item.roadmap.user_id != current_user.id:
        abort(403)
    if item.status == "done":
        return redirect(url_for("dashboard.today"))

    item.status = "done"
    item.completed_at = datetime.utcnow()
    db.session.flush()

    source_type = "lab" if item.item_type == "lab" else \
                   "checkpoint_quiz" if item.item_type == "checkpoint_quiz" else \
                   "roadmap_item"
    xp = award_xp(current_user.id, source_type, item.id,
                  description=f"Completed: {item.item_type}")
    touch_streak(current_user.id, date.today())
    if current_user.current_streak and current_user.current_streak % 7 == 0:
        award_xp(current_user.id, "streak_bonus", None)
    db.session.commit()
    flash(f"+{xp} XP — nice work!", "success")
    return redirect(url_for("dashboard.today"))
