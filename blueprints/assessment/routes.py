"""Adaptive Skill Assessment routes (plan §5.2, §9 API sketch).

Provides:
  /assessment/start                 → create a session, redirect to take
  /assessment/<int:session_id>      → take page (renders current question)
  /assessment/<int:session_id>/answer  (POST) → record & advance
  /assessment/<int:session_id>/result   → skill profile + Generate Roadmap
  /assessment/<int:session_id>/generate (POST) → build a Roadmap & go to dashboard
"""
from __future__ import annotations

import json

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, jsonify, abort)
from flask_login import login_required, current_user
from extensions import db
from models import AssessmentQuestion, AssessmentSession, JobRole, SkillArea

from services import assessment_engine
from services.roadmap_engine import generate_roadmap

assessment_bp = Blueprint("assessment", __name__, url_prefix="/assessment")


@assessment_bp.route("/start")
@login_required
def start():
    track_type = request.args.get("track_type", "general")
    job_role_id = request.args.get("job_role_id", type=int)

    if track_type not in ("general", "job_role"):
        track_type = "general"
    if track_type == "job_role" and job_role_id is None:
        flash("Pick a job role first.", "error")
        return redirect(url_for("onboarding.goal"))

    # Cancel any in-progress session for this user so we start fresh
    stale = AssessmentSession.query.filter_by(
        user_id=current_user.id, status="in_progress").all()
    for s in stale:
        s.status = "abandoned"

    session = AssessmentSession(
        user_id=current_user.id,
        track_type=track_type,
        job_role_id=job_role_id if track_type == "job_role" else None,
        status="in_progress",
    )
    db.session.add(session)
    db.session.commit()
    return redirect(url_for("assessment.take", session_id=session.id))


@assessment_bp.route("/<int:session_id>")
@login_required
def take(session_id: int):
    session = AssessmentSession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        abort(403)
    if session.status == "completed":
        return redirect(url_for("assessment.result", session_id=session.id))

    nxt = assessment_engine.next_question(session)
    if nxt.is_complete:
        # Auto-complete when the bank is exhausted
        assessment_engine.complete_session(session)
        db.session.commit()
        return redirect(url_for("assessment.result", session_id=session.id))

    answered, total = nxt.progress
    return render_template("assessment/take.html", session=session,
                           question=nxt.question,
                           progress=(answered, total))


@assessment_bp.route("/<int:session_id>/answer", methods=["POST"])
@login_required
def answer(session_id: int):
    session = AssessmentSession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        abort(403)
    if session.status != "in_progress":
        return redirect(url_for("assessment.result", session_id=session.id))

    question_id = request.form.get("question_id", type=int)
    answer_value = request.form.get("answer")
    if question_id is None or answer_value is None:
        flash("Please answer the question.", "error")
        return redirect(url_for("assessment.take", session_id=session.id))

    question = db.session.get(AssessmentQuestion, question_id)
    if question is None:
        flash("Question not found.", "error")
        return redirect(url_for("assessment.take", session_id=session.id))

    assessment_engine.record_response(session, question, answer_value)
    db.session.commit()
    return redirect(url_for("assessment.take", session_id=session.id))


@assessment_bp.route("/<int:session_id>/result")
@login_required
def result(session_id: int):
    session = AssessmentSession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        abort(403)
    if session.status != "completed":
        assessment_engine.complete_session(session)
        db.session.commit()

    profile = json.loads(session.result_json or "{}")
    return render_template("assessment/result.html", session=session,
                           profile=profile)


@assessment_bp.route("/<int:session_id>/generate", methods=["POST"])
@login_required
def generate(session_id: int):
    session = AssessmentSession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        abort(403)
    if session.status != "completed":
        assessment_engine.complete_session(session)
        db.session.commit()

    roadmap = generate_roadmap(
        current_user.id,
        job_role_id=session.job_role_id if session.track_type == "job_role" else None,
    )
    db.session.commit()
    flash("Your personalized roadmap is ready!", "success")
    return redirect(url_for("dashboard.today"))
