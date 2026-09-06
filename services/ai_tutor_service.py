"""AI "personal teacher" assistant (plan §5.10, offline plan §7).

Strategy picker (plan §7.1):
  - provider="auto"   → Ollama if reachable, else rules-based fallback.
  - provider="ollama" → POST to localhost:11434 /api/chat (single shot).
  - provider="anthropic" → only used by online users with ANTHROPIC_API_KEY.
  - provider="rules"  → deterministic TopicHint lookup, never empty.

The deterministic rules-based fallback (plan §7.2) reads `TopicHint` rows
keyed to trigger keywords and a 1..3 hint level so the tutor can escalate
without ever leaking a lab flag.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

import requests
from flask import current_app

from models import ContentItem, Topic, TopicHint


# Thread pool for async AI tutor calls (non-blocking)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ai_tutor")


# ---------------------------------------------------------------------------
# Context / prompt assembly (unchanged from the original)
# ---------------------------------------------------------------------------
def _retrieve_context(topic_id: Optional[int], query: str, k: int = 4) -> str:
    """Naive keyword-based retrieval over ContentItem bodies for the topic."""
    if topic_id is None:
        return ""
    items = (ContentItem.query
             .filter_by(topic_id=topic_id, is_active=True)
             .order_by(ContentItem.order_index)
             .limit(k)
             .all())
    chunks: list[str] = []
    for it in items:
        if it.type == "lesson_md" and it.body_markdown:
            chunks.append(f"# {it.title}\n{it.body_markdown}")
        elif it.url:
            chunks.append(f"# {it.title}\n(External resource: {it.url})")
    return "\n\n---\n\n".join(chunks)[:8000]


def _build_system_prompt(topic: Optional[Topic], user_context: Optional[dict] = None) -> str:
    role_line = "You are SkillSprint Academy's AI cybersecurity tutor and personal mentor. "
    if topic is not None:
        role_line += f"The student is currently studying '{topic.title}'. "
    
    # Add user context for personalized mentoring
    if user_context:
        role_line += f"Their current streak is {user_context.get('streak', 0)} days, total XP: {user_context.get('xp', 0)}, level: {user_context.get('level', 1)}. "
        if user_context.get('active_roadmap'):
            role_line += f"They're on the '{user_context['active_roadmap']}' track. "
        if user_context.get('today_tasks'):
            role_line += f"They have {user_context['today_tasks']} tasks scheduled today. "
    
    role_line += (
        "Answer clearly and concisely, like a friendly mentor. If the question "
        "is about a lab, give progressive hints without revealing the flag. "
        "Offer an 'Explain like I'm 5' option when the user asks for depth. "
        "Encourage consistent daily practice. Celebrate progress. Suggest next steps."
    )
    return role_line


def _get_user_context(user_id: int) -> dict:
    """Gather user context for personalized mentoring."""
    from models import User, StreakRecord, Roadmap, RoadmapItem, XPLog
    from datetime import date
    from extensions import db
    
    user = db.session.get(User, user_id)
    if not user:
        return {}
    
    streak_rec = StreakRecord.query.filter_by(user_id=user_id).first()
    active_roadmap = Roadmap.query.filter_by(user_id=user_id, status='active').first()
    today_tasks = 0
    if active_roadmap:
        today_tasks = sum(1 for i in active_roadmap.items 
                         if i.scheduled_date and i.scheduled_date.date() == date.today() 
                         and i.status != 'done')
    
    role_name = active_roadmap.job_role.name if active_roadmap and active_roadmap.job_role else None
    
    level = max(1, user.total_xp // 100 + 1)
    
    return {
        'xp': user.total_xp,
        'level': level,
        'streak': streak_rec.current_streak if streak_rec else 0,
        'active_roadmap': role_name,
        'today_tasks': today_tasks,
    }


def db_get_topic(topic_id: int) -> Optional[Topic]:
    from extensions import db
    return db.session.get(Topic, topic_id)


# ---------------------------------------------------------------------------
# Ollama probes (used by the /settings/ai-tutor page too)
# ---------------------------------------------------------------------------
def ollama_alive() -> bool:
    """Fast 200ms probe of the local Ollama API (plan §7.1)."""
    base = current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    timeout = float(current_app.config.get("OLLAMA_PROBE_TIMEOUT", 0.2))
    try:
        r = requests.get(f"{base}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def list_ollama_models() -> list[str]:
    base = current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    try:
        r = requests.get(f"{base}/api/tags", timeout=3.0)
        r.raise_for_status()
        data = r.json()
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Provider responses
# ---------------------------------------------------------------------------
def _ollama_reply(query: str, system: str, context: str,
                 topic: Optional[Topic]) -> str:
    """Single-shot call to the local Ollama /api/chat endpoint (plan §7.1)."""
    base = current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = current_app.config.get("OLLAMA_MODEL", "llama3.1:8b-instruct")
    user_content = query if not context else (
        f"Reference material:\n{context}\n\nQuestion: {query}")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "options": {"temperature": 0.3},
    }
    try:
        r = requests.post(f"{base}/api/chat", json=payload, timeout=120.0)
        r.raise_for_status()
        data = r.json()
        msg = data.get("message") or {}
        content = msg.get("content", "").strip()
        return content or _stub_reply(query, topic)
    except Exception as exc:
        current_app.logger.warning("Ollama reply error: %s", exc)
        return _stub_reply(query, topic)


def _anthropic_reply(query: str, system: str, context: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(
            api_key=current_app.config.get("ANTHROPIC_API_KEY", ""))
        messages = [{"role": "user", "content": query}]
        if context:
            messages.insert(0, {"role": "system",
                                 "content": f"Reference material:\n{context}"})
        resp = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        parts = [b.text for b in resp.content
                 if getattr(b, "type", "") == "text"]
        return "".join(parts) or ""
    except Exception as exc:
        current_app.logger.warning("Anthropic reply error: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Rules-based fallback (plan §7.2)
# ---------------------------------------------------------------------------
_HINT_TRIGGERS = ("help", "hint", "stuck", "don't know", "dont know",
                  "how do i", "what next", "explain")


def _matching_hints(topic: Optional[Topic]) -> list[TopicHint]:
    if topic is None:
        return []
    return (TopicHint.query
            .filter_by(topic_id=topic.id, is_active=True)
            .order_by(TopicHint.hint_level)
            .all())


def _rules_reply(query: str, topic: Optional[Topic]) -> str:
    """Deterministic tutor: keyword-matched TopicHint, else topic-templated."""
    if topic is None:
        return ("(Local rules tutor — pick a topic on the assistant page and I "
                "can give you topic-specific help. Set up Ollama for live LLM "
                "answers: see `/offline/settings/ai-tutor`.)")

    hints = _matching_hints(topic)
    q = query.lower()

    # Lab-help escalation: increments level every time "help"/"hint"/"stuck"
    # appears in a query. Stored level 1 → reveal level 1, etc.
    is_lab_help = any(t in q for t in _HINT_TRIGGERS)

    # Pick the first hint whose trigger_keywords intersect the query, else
    # fall back to the level-1 hint, else the templated summary.
    matched: Optional[TopicHint] = None
    for h in hints:
        try:
            kws = json.loads(h.trigger_keywords or "[]")
        except (TypeError, ValueError):
            kws = []
        if any(kw and kw.lower() in q for kw in kws):
            matched = h
            break
    if matched is None and is_lab_help and hints:
        matched = hints[0]
    if matched is not None:
        return matched.hint_text or "(empty hint)"

    # No matched hint — return a templated lesson + next-step table.
    parts: list[str] = []
    parts.append(f"Noted — you're working on **{topic.title}**.")
    parts.append("")
    parts.append("Here's a short reminder of what this topic covers, plus a "
                 "place to go next:")
    items = (ContentItem.query
             .filter_by(topic_id=topic.id, is_active=True,
                        type="lesson_md")
             .order_by(ContentItem.order_index).all())
    if items:
        parts.append("")
        for it in items[:3]:
            body = (it.body_markdown or "").strip()
            excerpt = re.sub(r"[*_`#>]", "", body.split("\n\n")[0])[:300]
            parts.append(f"- **{it.title}** — {excerpt}{'…' if len(body)>300 else ''}")
    parts.append("")
    parts.append("_Tip: include words like 'hint', 'help', or 'stuck' for "
                 "progressive lab hints, or set up Ollama for live answers "
                 "(see `/offline/settings/ai-tutor`)._")
    return "\n".join(parts)


def _stub_reply(query: str, topic: Optional[Topic]) -> str:
    """Shown only when an LLM call returned nothing usable."""
    topic_line = f" on '{topic.title}'" if topic else ""
    return (f"(AI tutor returned no content{topic_line}. Your question: "
            f"{query})")


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def answer(query: str, topic_id: Optional[int] = None, user_id: Optional[int] = None) -> str:
    """Return the assistant's reply to a user message (plan §7.1) — SYNCHRONOUS."""
    topic = db_get_topic(topic_id) if topic_id else None
    context = _retrieve_context(topic_id, query)
    user_context = _get_user_context(user_id) if user_id else None
    system = _build_system_prompt(topic, user_context)

    provider = current_app.config.get("AI_TUTOR_PROVIDER", "auto")
    if provider == "auto":
        provider = "ollama" if ollama_alive() else "rules"

    if provider == "ollama":
        return _ollama_reply(query, system, context, topic)
    if provider == "anthropic" and current_app.config.get("ANTHROPIC_API_KEY"):
        out = _anthropic_reply(query, system, context)
        if out:
            return out
        # fall through to rules if Anthropic blew up
    return _rules_reply(query, topic)


def answer_async(query: str, topic_id: Optional[int] = None, 
                 callback: Optional[Callable[[str], None]] = None):
    """Non-blocking AI tutor call — returns a Future.
    
    Usage:
        future = answer_async("How do I kerberoast?", topic_id=123)
        # ... do other work ...
        reply = future.result()  # blocks until ready
        
    Or with callback:
        answer_async("How do I kerberoast?", topic_id=123, 
                     callback=lambda reply: socketio.emit('ai_reply', reply))
    """
    def _run():
        with current_app.app_context():
            return answer(query, topic_id)
    
    future = _executor.submit(_run)
    if callback:
        future.add_done_callback(lambda f: callback(f.result()))
    return future


def shutdown_executor():
    """Shutdown the thread pool on app teardown."""
    _executor.shutdown(wait=True)