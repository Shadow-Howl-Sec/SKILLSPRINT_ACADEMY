"""Topic Learning Modules — 5-component comprehensive learning experience."""
from __future__ import annotations

from flask import Blueprint, render_template, abort
from extensions import db
from models import Topic, TopicLearningModule, Lab

topics_bp = Blueprint("topics", __name__)


@topics_bp.route("/topic/<int:topic_id>")
def detail(topic_id: int):
    """Display the comprehensive 5-component learning module for a topic."""
    topic = db.session.get(Topic, topic_id)
    if not topic:
        abort(404)

    module = topic.learning_module
    labs = Lab.query.filter_by(topic_id=topic.id, is_active=True).all()

    # Get prerequisite topics
    prereqs = [p.prerequisite for p in topic.prerequisites]

    # Get next topics (topics that require this one)
    next_topics = [r.topic for r in topic.required_by]

    return render_template(
        "topics/detail.html",
        topic=topic,
        module=module,
        labs=labs,
        prereqs=prereqs,
        next_topics=next_topics
    )