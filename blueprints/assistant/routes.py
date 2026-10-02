"""AI Personal Teacher (plan §5.10).

  /assistant         full-page chat (also rendered as floating widget elsewhere)
  /api/assistant/chat (POST) JSON {message, context_topic_id?} → {reply}
"""
from __future__ import annotations

import uuid

import markdown
from flask import Blueprint, render_template, request, jsonify, g
from extensions import db, limiter
from models import ChatMessage, Topic

from services.ai_tutor_service import answer

assistant_bp = Blueprint("assistant", __name__)


def _render_markdown(text: str) -> str:
    if not text:
        return ""
    try:
        rendered = markdown.markdown(text, extensions=['fenced_code', 'tables', 'codehilite'])
        import bleach
        return bleach.clean(
            rendered,
            tags={'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'del', 'em',
                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'li', 'ol',
                  'p', 'pre', 'strong', 'table', 'tbody', 'td', 'th', 'thead',
                  'tr', 'ul'},
            attributes={'a': ['href', 'title', 'rel']},
            protocols=['http', 'https', 'mailto'],
            strip=True,
        )
    except Exception:
        from markupsafe import escape
        return str(escape(text)).replace('\n', '<br>\n')


def _session_id() -> str:
    sid = request.cookies.get("assistant_sid")
    return sid or str(uuid.uuid4())


@assistant_bp.route("/assistant")
def chat():
    sid = _session_id()
    history = (ChatMessage.query
               .filter_by(user_id=g.user.id, session_id=sid)
               .order_by(ChatMessage.created_at)
               .limit(50).all())
    topics = Topic.query.filter_by(is_active=True).order_by(Topic.title).all()
    return render_template("assistant/chat.html", history=history, topics=topics)


@assistant_bp.route("/api/assistant/chat", methods=["POST"])
@limiter.limit("30 per minute")  # Rate limit to prevent Ollama resource exhaustion
def chat_api():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    topic_id = data.get("context_topic_id")
    if not message:
        return jsonify({"error": "empty message"}), 400
    
    # Limit message size to prevent memory exhaustion
    if len(message) > 4000:
        return jsonify({"error": "message too long (max 4000 chars)"}), 400

    if topic_id not in (None, ""):
        try:
            topic_id = int(topic_id)
        except (TypeError, ValueError):
            return jsonify({"error": "invalid topic"}), 400
        if db.session.get(Topic, topic_id) is None:
            return jsonify({"error": "topic not found"}), 404

    sid = _session_id()
    user_msg = ChatMessage(
        user_id=g.user.id, session_id=sid,
        role="user", content=message,
        related_topic_id=topic_id,
    )
    db.session.add(user_msg)
    db.session.flush()

    reply = answer(message, topic_id, g.user.id)
    reply_html = _render_markdown(reply)
    ai_msg = ChatMessage(
        user_id=g.user.id, session_id=sid,
        role="assistant", content=reply,
        related_topic_id=topic_id,
    )
    db.session.add(ai_msg)
    db.session.commit()
    return jsonify({"reply": reply, "reply_html": reply_html, "session_id": sid})