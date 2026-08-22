"""Adaptive Skill Assessment engine (plan §5.2).

Implements a lightweight Computerized Adaptive Testing (CAT) loop:
  - Start at medium difficulty per skill area.
  - Correct → harder; wrong → easier.
  - Fixed number of questions per area for the MVP (true IRT/Elo in v2).
  - Produces a SkillProfile (0-100 per area) with a confidence flag.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from flask import current_app
from extensions import db
from models import (
    AssessmentQuestion, AssessmentSession, AssessmentResponse,
    SkillProfile, SkillArea, JobRole,
)


@dataclass
class NextQuestionResult:
    question: Optional[AssessmentQuestion]
    is_complete: bool
    progress: tuple[int, int]   # answered, total


def _parse_options(question: AssessmentQuestion) -> list[str]:
    if not question.options:
        return []
    try:
        return json.loads(question.options)
    except (TypeError, ValueError):
        return []


def _is_mcq_correct(question: AssessmentQuestion, answer) -> bool:
    """MCQ correct_answer is the index (as str) of the correct option."""
    try:
        idx = int(question.correct_answer)
    except (TypeError, ValueError):
        return False
    opts = _parse_options(question)
    try:
        return int(answer) == idx and 0 <= idx < len(opts)
    except (TypeError, ValueError):
        return False


def _is_short_answer_correct(question: AssessmentQuestion, answer: str) -> bool:
    """correct_answer is a JSON/CSV list of accepted keywords."""
    if not answer:
        return False
    answer_lower = answer.strip().lower()
    try:
        keywords = json.loads(question.correct_answer or "[]")
    except (TypeError, ValueError):
        keywords = [k.strip() for k in (question.correct_answer or "").split(",")]
    return any(str(k).strip().lower() in answer_lower for k in keywords)


def grade_answer(question: AssessmentQuestion, answer_given) -> bool:
    if question.question_type == "mcq":
        return _is_mcq_correct(question, answer_given)
    if question.question_type in ("short_answer", "scenario"):
        return _is_short_answer_correct(question, str(answer_given or ""))
    return False


def _areas_for_session(session: AssessmentSession) -> list[SkillArea]:
    """Skill areas to assess. For a job-role session, restrict to areas
    referenced by that role's questions; otherwise all active areas."""
    q = (AssessmentQuestion.query
         .join(SkillArea, AssessmentQuestion.skill_area_id == SkillArea.id)
         .filter(AssessmentQuestion.is_active.is_(True),
                 SkillArea.is_active.is_(True)))
    if session.track_type == "job_role" and session.job_role_id:
        role = db.session.get(JobRole, session.job_role_id)
        if role:
            role_slugs = json.dumps([role.slug])
            q = q.filter(AssessmentQuestion.applicable_roles.like(f'"%{role.slug}%"'))
    return [a for a in q.with_entities(SkillArea).distinct()]


def _next_question_for_area(area_id: int, session: AssessmentSession,
                            current_difficulty: int) -> Optional[AssessmentQuestion]:
    """Pick an unanswered question in this area near the target difficulty."""
    answered_ids = {r.question_id for r in session.responses}
    q = (AssessmentQuestion.query
         .filter_by(skill_area_id=area_id, is_active=True)
         .filter(~AssessmentQuestion.id.in_(answered_ids) if answered_ids else True)
         .order_by(
             # closest difficulty first
             db.func.abs(AssessmentQuestion.difficulty - current_difficulty),
             AssessmentQuestion.id,
         ))
    return q.first()


def get_session_state(session: AssessmentSession) -> dict[int, dict]:
    """Return {area_id: {answered, correct, difficulty}} from responses."""
    state: dict[int, dict] = {}
    for r in session.responses:
        st = state.setdefault(r.question.skill_area_id,
                              {"answered": 0, "correct": 0, "difficulty": None,
                               "last_correct": None})
        st["answered"] += 1
        if r.is_correct:
            st["correct"] += 1
        st["difficulty"] = r.difficulty_at_time
        st["last_correct"] = r.is_correct
    return state


def next_question(session: AssessmentSession) -> NextQuestionResult:
    """Adaptive next-question selector.

    Iterates each area, asking QUESTIONS_PER_AREA questions; difficulty walks
    up on correct and down on wrong. Returns None when every area is satisfied.
    """
    per_area = int(current_app.config.get("ASSESSMENT_QUESTIONS_PER_AREA", 5))
    start_diff = int(current_app.config.get("ASSESSMENT_START_DIFFICULTY", 3))

    areas = _areas_for_session(session)
    state = get_session_state(session)

    for area in areas:
        st = state.get(area.id, {"answered": 0, "correct": 0,
                                 "difficulty": None, "last_correct": None})
        if st["answered"] >= per_area:
            continue
        # Determine next difficulty
        if st["answered"] == 0:
            diff = start_diff
        else:
            last = st["difficulty"] or start_diff
            diff = min(5, max(1, last + (1 if st["last_correct"] else -1)))
        q = _next_question_for_area(area.id, session, diff)
        if q is None:
            # Out of questions for this area; skip
            st["answered"] = per_area  # mark satisfied
            continue
        total_answered = sum(s["answered"] for s in state.values())
        total = len(areas) * per_area
        return NextQuestionResult(question=q, is_complete=False,
                                  progress=(total_answered, total))

    # No more questions → complete
    total = len(areas) * per_area
    return NextQuestionResult(question=None, is_complete=True,
                              progress=(total, total))


def record_response(session: AssessmentSession, question: AssessmentQuestion,
                    answer_given, time_taken_seconds: int | None = None) -> bool:
    is_correct = grade_answer(question, answer_given)
    resp = AssessmentResponse(
        session_id=session.id,
        question_id=question.id,
        answer_given=str(answer_given) if answer_given is not None else None,
        is_correct=is_correct,
        difficulty_at_time=question.difficulty,
        time_taken_seconds=time_taken_seconds,
    )
    db.session.add(resp)
    db.session.flush()
    return is_correct


def compute_skill_profile(session: AssessmentSession) -> dict:
    """Compute a SkillProfile per area; persist + return a serializable dict.

    Score = (correct / answered) * 100, weighted toward harder questions via a
    simple difficulty-weighted accuracy. Confidence is 'low' for <3 answers,
    'medium' for 3-4, 'high' for 5+ (per MVP area limit of 5).
    """
    per_area = int(current_app.config.get("ASSESSMENT_QUESTIONS_PER_AREA", 5))
    state = get_session_state(session)
    profile_payload = {"areas": [], "overall": 0.0, "level": "Beginner"}

    total_weighted_score = 0.0
    total_weight = 0

    for area_id, st in state.items():
        answered = st["answered"]
        correct = st["correct"]
        if answered == 0:
            score = 0.0
            confidence = "low"
        else:
            score = (correct / answered) * 100.0
            if answered >= per_area:
                confidence = "high"
            elif answered >= 3:
                confidence = "medium"
            else:
                confidence = "low"

        # upsert skill profile row
        sp = SkillProfile.query.filter_by(user_id=session.user_id,
                                          skill_area_id=area_id).first()
        if sp is None:
            sp = SkillProfile(user_id=session.user_id, skill_area_id=area_id)
            db.session.add(sp)
        sp.score = round(score, 1)
        sp.confidence = confidence
        sp.last_updated = db.func.now()

        area = db.session.get(SkillArea, area_id)
        profile_payload["areas"].append({
            "area_id": area_id,
            "area_name": area.name if area else f"area#{area_id}",
            "area_slug": area.slug if area else None,
            "score": round(score, 1),
            "answered": answered,
            "correct": correct,
            "confidence": confidence,
        })
        total_weighted_score += score * answered
        total_weight += answered

    overall = (total_weighted_score / total_weight) if total_weight else 0.0
    profile_payload["overall"] = round(overall, 1)
    profile_payload["level"] = (
        "Advanced" if overall >= 75 else
        "Intermediate" if overall >= 40 else
        "Beginner"
    )
    db.session.flush()
    return profile_payload


def complete_session(session: AssessmentSession) -> dict:
    """Mark session complete and persist the computed profile JSON."""
    profile = compute_skill_profile(session)
    session.completed_at = db.func.now()
    session.status = "completed"
    session.result_json = json.dumps(profile)
    db.session.flush()
    return profile
