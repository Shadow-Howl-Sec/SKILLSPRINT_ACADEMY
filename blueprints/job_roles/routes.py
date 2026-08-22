"""Job-role tracks (plan §5.4, §13).

  /job-roles            browse roles
  /job-roles/<id>       role detail + "Start this track" (→ assessment)

We also expose a REST-ish listing for the admin/about pages:
  /api/job-roles        JSON list of active roles
"""
from __future__ import annotations

import json

from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required
from models import JobRole, Topic

job_roles_bp = Blueprint("job_roles", __name__)


@job_roles_bp.route("/job-roles")
@login_required
def browse():
    roles = JobRole.query.filter_by(is_active=True).order_by(JobRole.id).all()
    return render_template("job_roles/browse.html", roles=roles)


@job_roles_bp.route("/job-roles/<int:role_id>")
@login_required
def detail(role_id: int):
    role = JobRole.query.get_or_404(role_id)
    role_topics = [rt.topic for rt in role.role_topics if rt.topic and rt.topic.is_active]
    certs = []
    if role.recommended_certs:
        try:
            certs = json.loads(role.recommended_certs)
        except (TypeError, ValueError):
            certs = [c.strip() for c in role.recommended_certs.split(",")]
    return render_template("job_roles/detail.html", role=role,
                           topics=role_topics, certs=certs)


@job_roles_bp.route("/job-roles/<int:role_id>/start")
@login_required
def start(role_id: int):
    JobRole.query.get_or_404(role_id)
    return redirect(url_for("assessment.start", track_type="job_role",
                            job_role_id=role_id))


@job_roles_bp.route("/api/job-roles")
def api_list():
    roles = JobRole.query.filter_by(is_active=True).all()
    return jsonify([{
        "id": r.id, "slug": r.slug, "name": r.name,
        "icon_emoji": r.icon_emoji, "difficulty_label": r.difficulty_label,
    } for r in roles])
