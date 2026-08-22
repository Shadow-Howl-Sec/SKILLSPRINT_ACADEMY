"""Personal library — "add your own course" feature (plan §5.7).

  /library           list user's added external resources
  /library/add        add a resource (URL + metadata auto-fetch)
  /library/<id>/schedule (POST) slot an external resource into today / a date
"""
from __future__ import annotations

from datetime import datetime, date

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, abort)
from flask_login import login_required, current_user
from extensions import db
from models import (UserResource, SkillArea, Roadmap, RoadmapItem)

from services.link_metadata_service import fetch_metadata

library_bp = Blueprint("library", __name__)


@library_bp.route("/library")
@login_required
def list():
    resources = (UserResource.query
                 .filter_by(user_id=current_user.id)
                 .order_by(UserResource.added_at.desc()).all())
    return render_template("library/list.html", resources=resources)


@library_bp.route("/library/add", methods=["GET", "POST"])
@login_required
def add():
    areas = SkillArea.query.filter_by(is_active=True).order_by(SkillArea.order_index).all()
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url or not url.startswith(("http://", "https://")):
            flash("Enter a valid URL (http/https).", "error")
            return redirect(url_for("library.add"))
        meta = fetch_metadata(url)
        title = request.form.get("title") or meta["title"]
        resource = UserResource(
            user_id=current_user.id,
            title=title[:300],
            url=url[:500],
            resource_type=request.form.get("resource_type") or meta["resource_type"],
            thumbnail_url=meta["thumbnail_url"],
            estimated_minutes=int(request.form.get("estimated_minutes") or 30),
            skill_area_id=request.form.get("skill_area_id", type=int),
            notes=request.form.get("notes"),
        )
        db.session.add(resource)
        db.session.commit()
        flash("Resource added to your library.", "success")
        return redirect(url_for("library.list"))
    return render_template("library/add.html", areas=areas)


@library_bp.route("/library/<int:resource_id>/schedule", methods=["POST"])
@login_required
def schedule(resource_id: int):
    resource = UserResource.query.get_or_404(resource_id)
    if resource.user_id != current_user.id:
        abort(403)

    roadmap = Roadmap.query.filter_by(
        user_id=current_user.id, status="active").first()
    if roadmap is None:
        flash("Generate a roadmap first.", "info")
        return redirect(url_for("onboarding.domain"))

    when = request.form.get("date") or date.today().isoformat()
    try:
        scheduled_date = datetime.strptime(when, "%Y-%m-%d")
    except ValueError:
        scheduled_date = datetime.utcnow()

    item = RoadmapItem(
        roadmap_id=roadmap.id,
        item_type="external_resource",
        user_resource_id=resource.id,
        scheduled_date=scheduled_date,
        order_index=max((i.order_index for i in roadmap.items), default=0) + 1,
        estimated_minutes=resource.estimated_minutes or 30,
        status="pending",
    )
    db.session.add(item)
    db.session.commit()
    flash("Resource slotted into your schedule.", "success")
    return redirect(url_for("library.list"))
