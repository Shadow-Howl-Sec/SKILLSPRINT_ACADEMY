"""Checkpoint Quiz and Assessment Blueprint.

Routes:
  GET/POST /topic/<int:topic_id>/quiz     - Take topic-specific checkpoint quiz
  POST     /topic/<int:topic_id>/quiz/submit - Submit and grade topic quiz
  GET      /assessment/start               - Start adaptive assessment
"""
from __future__ import annotations

import json
from datetime import datetime, date, timezone

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, g
from extensions import db
from models import Topic, AssessmentQuestion, RoadmapItem, Roadmap
from services.xp_service import award_xp, touch_streak

assessment_bp = Blueprint("assessment", __name__)


@assessment_bp.route("/topic/<int:topic_id>/quiz", methods=["GET", "POST"])
def topic_quiz(topic_id: int):
    """Render and evaluate checkpoint quiz for a specific topic."""
    topic = Topic.query.get_or_404(topic_id)
    questions = AssessmentQuestion.query.filter_by(topic_id=topic.id, is_active=True).all()
    
    # Fallback to skill area questions if no topic questions exist
    if not questions:
        questions = AssessmentQuestion.query.filter_by(skill_area_id=topic.skill_area_id, is_active=True).limit(3).all()
        
    if not questions:
        flash(f"No checkpoint questions available for {topic.title} yet.", "info")
        return redirect(url_for("roadmap.view"))

    if request.method == "POST":
        score = 0
        total = len(questions)
        results = []

        for q in questions:
            user_ans = request.form.get(f"q_{q.id}", "").strip()
            is_correct = False
            
            # MCQ indexing check
            if q.question_type == "mcq":
                is_correct = (user_ans == str(q.correct_answer).strip())
            else:
                is_correct = (user_ans.lower() in str(q.correct_answer).lower())

            if is_correct:
                score += 1

            opts = json.loads(q.options) if q.options else []
            correct_opt = opts[int(q.correct_answer)] if q.question_type == "mcq" and opts and q.correct_answer.isdigit() and int(q.correct_answer) < len(opts) else q.correct_answer

            results.append({
                "question": q.question_text,
                "user_answer": opts[int(user_ans)] if q.question_type == "mcq" and opts and user_ans.isdigit() and int(user_ans) < len(opts) else user_ans,
                "correct_answer": correct_opt,
                "is_correct": is_correct,
                "explanation": q.explanation
            })

        percent = int((score / total) * 100) if total > 0 else 0
        passed = percent >= 60

        # Mark RoadmapItem checkpoint_quiz for this topic as done
        active_roadmap = Roadmap.query.filter_by(user_id=g.user.id, status="active").first()
        if active_roadmap:
            quiz_items = RoadmapItem.query.filter_by(
                roadmap_id=active_roadmap.id,
                topic_id=topic.id,
                item_type="checkpoint_quiz"
            ).all()
            for item in quiz_items:
                item.status = "done"
                item.completed_at = datetime.now(timezone.utc)
                
        if passed:
            xp = award_xp(g.user.id, "checkpoint_quiz", topic.id, xp_amount=25,
                          description=f"Passed Checkpoint Quiz: {topic.title}")
            touch_streak(g.user.id, date.today())
            db.session.commit()
            flash(f"Congratulations! You passed the {topic.title} Checkpoint Quiz with {percent}% (+25 XP).", "success")
        else:
            db.session.commit()
            flash(f"You scored {percent}%. Review the material and try again to pass (60% required).", "warning")

        return render_template("assessment/checkpoint_result.html",
                               topic=topic,
                               score=score,
                               total=total,
                               percent=percent,
                               passed=passed,
                               results=results)

    return render_template("assessment/checkpoint_quiz.html", topic=topic, questions=questions)


@assessment_bp.route("/assessment/start")
def start():
    """Start assessment (redirect to roadmap view)."""
    return redirect(url_for("roadmap.view"))
