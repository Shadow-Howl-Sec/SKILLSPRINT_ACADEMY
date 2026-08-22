"""Roadmap generation / re-planning engine (plan §5.3) — the core product loop.

Two-layer design:
  Layer A — Curriculum Graph (admin-authored Topic DAG + per-role templates).
  Layer B — Per-user personalization:
    1. Select base template (job_role's DAG or general foundations).
    2. Prune/reorder using the user's SkillProfile (skip-topics, remediation).
    3. Estimate time per topic from ContentItem/Lab estimated_minutes.
    4. Sequence into calendar via scheduler_service.
    5. Persist Roadmap + RoadmapItems.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from flask import current_app
from extensions import db
from models import (
    Roadmap, RoadmapItem, Topic, JobRole, JobRoleTopic, ContentItem, Lab,
    SkillProfile, WeeklyAvailability, UserResource,
)

from services.scheduler_service import schedule_items, availability_for_user


# ---------------------------------------------------------------------------
# Helpers: DAG topological order
# ---------------------------------------------------------------------------

def _topo_order(topics: list[Topic], prerequisites: dict[int, list[int]]) -> list[Topic]:
    """Kahn's algorithm restricted to `topics`. `prerequisites` maps
    topic_id -> list of prerequisite topic_ids (which may include topics
    outside this set; those are ignored)."""
    by_id = {t.id: t for t in topics}
    indeg: dict[int, int] = {t.id: 0 for t in topics}
    for t in topics:
        for p in prerequisites.get(t.id, []):
            if p in by_id:
                indeg[t.id] += 1

    q = [tid for tid, d in indeg.items() if d == 0]
    order: list[Topic] = []
    while q:
        q.sort(key=lambda tid: by_id[tid].difficulty if by_id[tid].difficulty else 1)
        tid = q.pop(0)
        order.append(by_id[tid])
        for other in topics:
            if tid in prerequisites.get(other.id, []):
                indeg[other.id] -= 1
                if indeg[other.id] == 0 and other not in order and other.id not in q:
                    q.append(other.id)
    # Append any leftover (cycles / unresolved deps)
    for t in topics:
        if t not in order:
            order.append(t)
    return order


def _topic_prerequisites_map(topics: list[Topic]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = {}
    for t in topics:
        result[t.id] = [p.prerequisite_topic_id for p in t.prerequisites
                        if p.prerequisite_topic_id is not None]
    return result


# ---------------------------------------------------------------------------
# Template selection
# ---------------------------------------------------------------------------

def select_base_topics(job_role_id: int | None) -> list[Topic]:
    """Return the ordered set of Topics for a role template, or the general
    foundations graph (all active topics, DAG-ordered) when no role is set."""
    if job_role_id:
        role_rows = (JobRoleTopic.query
                     .filter_by(job_role_id=job_role_id)
                     .order_by(JobRoleTopic.order_index)
                     .all())
        topics = [r.topic for r in role_rows if r.topic and r.topic.is_active]
    else:
        topics = Topic.query.filter_by(is_active=True).all()

    prerequisites = _topic_prerequisites_map(topics)
    return _topo_order(topics, prerequisites)


# ---------------------------------------------------------------------------
# Personalization (prune + remediation)
# ---------------------------------------------------------------------------

@dataclass
class TopicDecision:
    topic: Topic
    skip: bool               # True -> compress to a single checkpoint review
    remediation: bool        # True -> inserted as remedial mini-module


def _area_score_map(user_id: int) -> dict[int, SkillProfile]:
    rows = SkillProfile.query.filter_by(user_id=user_id).all()
    return {r.skill_area_id: r for r in rows}


def decide_topics(topics: list[Topic], skill_profiles: dict[int, SkillProfile]
                   ) -> list[TopicDecision]:
    """For each topic decide skip / remediation using the skill profile of
    its parent SkillArea."""
    decisions: list[TopicDecision] = []
    for t in topics:
        sp = skill_profiles.get(t.skill_area_id)
        if sp and sp.score >= 80 and sp.confidence != "low":
            decisions.append(TopicDecision(topic=t, skip=True, remediation=False))
        elif sp and sp.score < 30 and sp.confidence != "low":
            decisions.append(TopicDecision(topic=t, skip=False, remediation=True))
        else:
            decisions.append(TopicDecision(topic=t, skip=False, remediation=False))
    return decisions


# ---------------------------------------------------------------------------
# Item expansion: for each kept topic, emit RoadmapItem-equivalent dicts
# ---------------------------------------------------------------------------

def expand_topic_to_items(topic: Topic, skip: bool) -> list[dict]:
    """Produce a flat list of schedule items for a topic.

    For a skipped topic we compress to a single checkpoint_quiz item.
    For a kept topic we emit each ContentItem (in order) then each Lab.
    """
    items: list[dict] = []
    if skip:
        items.append({
            "item_type": "checkpoint_quiz",
            "topic_id": topic.id,
            "estimated_minutes": 10,
            "title": f"Checkpoint: {topic.title}",
        })
        return items

    content = (ContentItem.query
               .filter_by(topic_id=topic.id, is_active=True)
               .order_by(ContentItem.order_index)
               .all())
    for c in content:
        items.append({
            "item_type": "content_item",
            "content_item_id": c.id,
            "topic_id": topic.id,
            "estimated_minutes": c.estimated_minutes or 15,
            "title": c.title,
        })

    labs = (Lab.query
            .filter_by(topic_id=topic.id, is_active=True)
            .order_by(Lab.difficulty)
            .all())
    for lab in labs:
        items.append({
            "item_type": "lab",
            "lab_id": lab.id,
            "topic_id": topic.id,
            "estimated_minutes": lab.estimated_minutes or 30,
            "title": lab.title,
        })

    # If topic has no resources yet, still schedule a placeholder so the user
    # can see it on the roadmap (admin can backfill content later).
    if not items:
        items.append({
            "item_type": "checkpoint_quiz",
            "topic_id": topic.id,
            "estimated_minutes": topic.estimated_minutes or 30,
            "title": f"Study: {topic.title}",
        })
    return items


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _append_external_resources(items: list[dict], user_id: int) -> list[dict]:
    """Append user-added (unscheduled) external resources at the end, so they
    appear on the roadmap and can be re-dragged afterwards."""
    pending = (UserResource.query
                .filter_by(user_id=user_id, is_completed=False)
                .order_by(UserResource.added_at)
                .all())
    for r in pending:
        items.append({
            "item_type": "external_resource",
            "user_resource_id": r.id,
            "estimated_minutes": r.estimated_minutes or 30,
            "title": r.title,
        })
    return items


def _persist_roadmap(user_id: int, job_role_id: int | None,
                     scheduled: list[dict], total_minutes: int) -> Roadmap:
    """Invalidate any prior active roadmap and persist a new one + items."""
    # Pause existing active roadmaps for the user (keep history).
    prior = Roadmap.query.filter_by(user_id=user_id, status="active").all()
    for r in prior:
        r.status = "paused"

    roadmap = Roadmap(
        user_id=user_id,
        job_role_id=job_role_id,
        target_completion_date=scheduled[-1]["scheduled_date"] if scheduled else None,
        status="active",
        version=(max([r.version for r in prior], default=0) + 1),
    )
    db.session.add(roadmap)
    db.session.flush()

    for s in scheduled:
        item = RoadmapItem(
            roadmap_id=roadmap.id,
            item_type=s["item_type"],
            content_item_id=s.get("content_item_id"),
            lab_id=s.get("lab_id"),
            topic_id=s.get("topic_id"),
            user_resource_id=s.get("user_resource_id"),
            scheduled_date=s["scheduled_date"],
            order_index=s["order_index"],
            estimated_minutes=s["estimated_minutes"],
            status="pending",
        )
        db.session.add(item)
    db.session.flush()
    return roadmap


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_roadmap(user_id: int, job_role_id: int | None = None,
                     start_date: date | None = None) -> Roadmap:
    """Full end-to-end generation: assessment → roadmap → dashboard ready."""
    start = start_date or date.today()

    topics = select_base_topics(job_role_id)
    profiles = _area_score_map(user_id)
    decisions = decide_topics(topics, profiles)

    raw_items: list[dict] = []
    for d in decisions:
        topic_items = expand_topic_to_items(d.topic, d.skip)
        raw_items.extend(topic_items)

    raw_items = _append_external_resources(raw_items, user_id)

    availability = availability_for_user(user_id, WeeklyAvailability)
    buffer_pct = float(current_app.config.get("ROADMAP_BUFFER_PERCENT", 0.20))

    scheduled = schedule_items(raw_items, availability,
                               start_date=start, buffer_percent=buffer_pct)

    total_minutes = sum(s["estimated_minutes"] for s in scheduled)
    return _persist_roadmap(user_id, job_role_id, scheduled, total_minutes)


def replan_roadmap(roadmap: Roadmap) -> Roadmap:
    """Re-generate the roadmap preserving completed items' progress.

    Reuses the user's existing SkillProfile and availability; completed
    RoadmapItems are re-applied as 'done' on the new plan where an
    equivalent topic/content_item matches.
    """
    completed = [(i.item_type, i.content_item_id, i.lab_id,
                  i.topic_id, i.user_resource_id, i.completed_at)
                 for i in roadmap.items if i.status == "done"]

    new_roadmap = generate_roadmap(roadmap.user_id,
                                   job_role_id=roadmap.job_role_id)

    # Re-match completed items onto the new plan
    for it in new_roadmap.items:
        for (itype, cid, lid, tid, urid, done_at) in completed:
            if (itype == it.item_type and cid == it.content_item_id
                    and lid == it.lab_id and tid == it.topic_id
                    and urid == it.user_resource_id):
                it.status = "done"
                it.completed_at = done_at
    db.session.flush()
    return new_roadmap
