"""Onboarding flow (plan §5.1).

Step 1 — /onboarding/domain        : pick domain  (MVP only "Cybersecurity")
Step 2 — /onboarding/goal           : general vs job-role (lists JobRole rows)
Step 3 — /onboarding/availability  : weekly available minutes per day
On submit → redirect to the assessment for the chosen track.
"""
from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import JobRole, WeeklyAvailability

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


_DAYS = [("Mon", 0), ("Tue", 1), ("Wed", 2), ("Thu", 3),
         ("Fri", 4), ("Sat", 5), ("Sun", 6)]


@onboarding_bp.route("/domain")
@login_required
def domain():
    return render_template("onboarding/domain.html")


@onboarding_bp.route("/goal")
@login_required
def goal():
    roles = JobRole.query.filter_by(is_active=True).order_by(JobRole.id).all()
    return render_template("onboarding/goal.html", roles=roles)


@onboarding_bp.route("/availability", methods=["GET", "POST"])
@login_required
def availability():
    if request.method == "POST":
        weekly = {int(k[len("day_"):]): int(v)
                  for k, v in request.form.items()
                  if k.startswith("day_") and v}
        # Persist: replace existing rows for this user
        WeeklyAvailability.query.filter_by(user_id=current_user.id).delete()
        for day_idx, minutes in weekly.items():
            if minutes and minutes > 0:
                db.session.add(WeeklyAvailability(
                    user_id=current_user.id,
                    day_of_week=day_idx,
                    available_minutes=min(max(minutes, 0), 12 * 60),
                ))
        db.session.commit()
        flash("Weekly availability saved.", "success")

        # Choose where to send the user next
        goal_choice = request.form.get("goal_choice", "general")
        if goal_choice == "job_role" and request.form.get("job_role_id"):
            return redirect(url_for("assessment.start",
                                   track_type="job_role",
                                   job_role_id=request.form["job_role_id"]))
        return redirect(url_for("assessment.start", track_type="general"))

    # Pre-populate any existing availability
    existing = {wa.day_of_week: wa.available_minutes
                for wa in current_user.weekly_availability}
    rows = [(name, idx, existing.get(idx, 60)) for name, idx in _DAYS]
    return render_template("onboarding/availability.html", days=rows)
