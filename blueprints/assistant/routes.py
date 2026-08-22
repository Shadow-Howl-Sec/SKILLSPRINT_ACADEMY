"""AI Personal Teacher (plan §5.10).

  /assistant         full-page chat (also rendered as floating widget elsewhere)
  /api/assistant/chat (POST) JSON {message, context_topic_id?} → {reply}
"""
from __future__ import annotations

import uuid

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models import ChatMessage, Topic

from services.ai_tutor_service import answer

assistant_bp = Blueprint("assistant", __name__)


def _session_id() -> str:
    sid = request.cookies.get("assistant_sid")
    return sid or str(uuid.uuid4())


@assistant_bp.route("/assistant")
@login_required
def chat():
    sid = _session_id()
    history = (ChatMessage.query
               .filter_by(user_id=current_user.id, session_id=sid)
               .order_by(ChatMessage.created_at)
               .limit(50).all())
    topics = Topic.query.filter_by(is_active=True).order_by(Topic.title).all()
    return render_template("assistant/chat.html", history=history, topics=topics)


@assistant_bp.route("/api/assistant/chat", methods=["POST"])
@login_required
def chat_api():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    topic_id = data.get("context_topic_id")
    if not message:
        return jsonify({"error": "empty message"}), 400

    sid = _session_id()
    user_msg = ChatMessage(
        user_id=current_user.id, session_id=sid,
        role="user", content=message,
        related_topic_id=topic_id,
    )
    db.session.add(user_msg)
    db.session.flush()

    reply = answer(message, topic_id)
    ai_msg = ChatMessage(
        user_id=current_user.id, session_id=sid,
        role="assistant", content=reply,
        related_topic_id=topic_id,
    )
    db.session.add(ai_msg)
    db.session.commit()
    return jsonify({"reply": reply, "session_id": sid})
