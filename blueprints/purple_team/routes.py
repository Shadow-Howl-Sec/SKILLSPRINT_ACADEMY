"""Purple Team Exercise Log & Coverage (Gap 2).

Routes:
  GET  /purple-team/log              — timeline of completed exercises
  POST /purple-team/log/new          — manual log entry for ad-hoc practice
  GET  /purple-team/coverage         — ATT&CK matrix coverage grid
  GET  /purple-team/export           — Markdown portfolio export
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from collections import defaultdict

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, abort, g, make_response)
from extensions import db
from models import PurpleTeamExerciseLog, AttackCoverage, Lab, User, SkillArea

purple_team_bp = Blueprint("purple_team", __name__, url_prefix="/purple-team")


# MITRE ATT&CK Tactics (Enterprise) - ordered for display
MITRE_TACTICS = [
    ("Reconnaissance", "TA0043"),
    ("Resource Development", "TA0042"),
    ("Initial Access", "TA0001"),
    ("Execution", "TA0002"),
    ("Persistence", "TA0003"),
    ("Privilege Escalation", "TA0004"),
    ("Defense Evasion", "TA0005"),
    ("Credential Access", "TA0006"),
    ("Discovery", "TA0007"),
    ("Lateral Movement", "TA0008"),
    ("Collection", "TA0009"),
    ("Command and Control", "TA0011"),
    ("Exfiltration", "TA0010"),
    ("Impact", "TA0040"),
]


@purple_team_bp.route("/log")
def log_list():
    """Timeline of completed purple team exercises."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    
    # Filter options
    tactic_filter = request.args.get("tactic")
    technique_filter = request.args.get("technique")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    
    query = PurpleTeamExerciseLog.query.filter_by(user_id=g.user.id)
    
    if technique_filter:
        query = query.filter(PurpleTeamExerciseLog.mitre_id == technique_filter)
    if date_from:
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(PurpleTeamExerciseLog.date_completed >= dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(PurpleTeamExerciseLog.date_completed <= dt)
        except ValueError:
            pass
    
    logs = query.order_by(PurpleTeamExerciseLog.date_completed.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Get unique MITRE techniques for filter dropdown
    user_techniques = db.session.query(PurpleTeamExerciseLog.mitre_id).filter_by(
        user_id=g.user.id).distinct().all()
    user_techniques = [t[0] for t in user_techniques if t[0]]
    
    return render_template("purple_team/log.html",
                           logs=logs,
                           user_techniques=user_techniques,
                           tactic_filter=tactic_filter,
                           technique_filter=technique_filter,
                           date_from=date_from,
                           date_to=date_to,
                           mitre_tactics=MITRE_TACTICS)


@purple_team_bp.route("/log/new", methods=["GET", "POST"])
def log_new():
    """Manual log entry for ad-hoc practice (e.g., Atomic Red Team tests)."""
    labs = Lab.query.filter_by(is_active=True).order_by(Lab.title).all()
    
    if request.method == "POST":
        technique_title = request.form.get("technique_title", "").strip()
        mitre_id = request.form.get("mitre_id", "").strip() or None
        attack_succeeded = request.form.get("attack_succeeded") == "on"
        detected = request.form.get("detected") == "on"
        rule_written = request.form.get("rule_written") == "on"
        notes = request.form.get("notes", "").strip()
        lab_id = request.form.get("lab_id", type=int)
        
        if not technique_title:
            flash("Technique title is required.", "error")
            return render_template("purple_team/log_form.html", labs=labs)
        
        log = PurpleTeamExerciseLog(
            user_id=g.user.id,
            lab_id=lab_id,
            technique_title=technique_title,
            mitre_id=mitre_id,
            attack_succeeded=attack_succeeded,
            detected=detected,
            rule_written=rule_written,
            notes=notes,
        )
        db.session.add(log)
        
        # Update AttackCoverage if MITRE ID provided
        if mitre_id:
            _update_coverage(g.user.id, mitre_id, attack_succeeded, detected, rule_written)
        
        db.session.commit()
        flash("Exercise logged successfully!", "success")
        return redirect(url_for("purple_team.log_list"))
    
    return render_template("purple_team/log_form.html", labs=labs)


@purple_team_bp.route("/log/<int:log_id>/edit", methods=["GET", "POST"])
def log_edit(log_id: int):
    """Edit an existing log entry."""
    log = PurpleTeamExerciseLog.query.get_or_404(log_id)
    if log.user_id != g.user.id:
        abort(403)
    
    labs = Lab.query.filter_by(is_active=True).order_by(Lab.title).all()
    
    if request.method == "POST":
        log.technique_title = request.form.get("technique_title", "").strip()
        log.mitre_id = request.form.get("mitre_id", "").strip() or None
        log.attack_succeeded = request.form.get("attack_succeeded") == "on"
        log.detected = request.form.get("detected") == "on"
        log.rule_written = request.form.get("rule_written") == "on"
        log.notes = request.form.get("notes", "").strip()
        log.lab_id = request.form.get("lab_id", type=int)
        
        if not log.technique_title:
            flash("Technique title is required.", "error")
            return render_template("purple_team/log_form.html", labs=labs, log=log)
        
        # Update AttackCoverage
        if log.mitre_id:
            _update_coverage(g.user.id, log.mitre_id, log.attack_succeeded, log.detected, log.rule_written)
        
        db.session.commit()
        flash("Exercise log updated!", "success")
        return redirect(url_for("purple_team.log_list"))
    
    return render_template("purple_team/log_form.html", labs=labs, log=log)


@purple_team_bp.route("/log/<int:log_id>/delete", methods=["POST"])
def log_delete(log_id: int):
    """Delete a log entry."""
    log = PurpleTeamExerciseLog.query.get_or_404(log_id)
    if log.user_id != g.user.id:
        abort(403)
    
    db.session.delete(log)
    db.session.commit()
    flash("Exercise log deleted.", "success")
    return redirect(url_for("purple_team.log_list"))


@purple_team_bp.route("/coverage")
def coverage():
    """ATT&CK matrix coverage grid."""
    # Get all coverage records for user
    coverage_records = AttackCoverage.query.filter_by(user_id=g.user.id).all()
    
    # Build matrix: tactic -> list of techniques with status
    matrix = defaultdict(list)
    for record in coverage_records:
        matrix[record.mitre_tactic].append({
            "technique_id": record.mitre_technique_id,
            "attacked": record.first_attacked_date is not None,
            "detected": record.first_detected_date is not None,
            "rule_written": record.detection_rule_written,
            "first_attacked": record.first_attacked_date,
            "first_detected": record.first_detected_date,
            "last_reviewed": record.last_reviewed_date,
        })
    
    # Also include techniques from logs that don't have coverage records yet
    logs = PurpleTeamExerciseLog.query.filter_by(user_id=g.user.id).all()
    for log in logs:
        if log.mitre_id and log.mitre_id not in [t["technique_id"] for t in matrix.get("", [])]:
            # We don't know the tactic from the log alone
            # In a full implementation, you'd have a MITRE reference table
            pass
    
    # Calculate summary stats
    total_techniques = sum(len(techs) for techs in matrix.values())
    attacked_count = sum(1 for techs in matrix.values() for t in techs if t["attacked"])
    detected_count = sum(1 for techs in matrix.values() for t in techs if t["detected"])
    rule_count = sum(1 for techs in matrix.values() for t in techs if t["rule_written"])
    
    return render_template("purple_team/coverage.html",
                           matrix=matrix,
                           mitre_tactics=MITRE_TACTICS,
                           total_techniques=total_techniques,
                           attacked_count=attacked_count,
                           detected_count=detected_count,
                           rule_count=rule_count)


@purple_team_bp.route("/export")
def export():
    """Export exercise log as Markdown for portfolio."""
    logs = PurpleTeamExerciseLog.query.filter_by(user_id=g.user.id).order_by(
        PurpleTeamExerciseLog.date_completed).all()
    
    now_utc = datetime.now(timezone.utc)
    md_lines = [
        "# Purple Team Exercise Log",
        f"**Generated:** {now_utc.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**User:** {g.user.username}",
        "",
        "---",
        "",
    ]
    
    # Summary
    total = len(logs)
    attacked = sum(1 for l in logs if l.attack_succeeded)
    detected = sum(1 for l in logs if l.detected)
    rules = sum(1 for l in logs if l.rule_written)
    
    md_lines.extend([
        "## Summary",
        f"- **Total Exercises:** {total}",
        f"- **Attacks Successful:** {attacked}",
        f"- **Detected:** {detected}",
        f"- **Rules Written:** {rules}",
        "",
        "---",
        "",
        "## Exercises",
        "",
    ])
    
    for log in logs:
        md_lines.extend([
            f"### {log.technique_title}",
            f"- **Date:** {log.date_completed.strftime('%Y-%m-%d %H:%M')}",
            f"- **MITRE ID:** {log.mitre_id or 'N/A'}",
            f"- **Lab:** {log.lab.title if log.lab else 'Manual Entry'}",
            f"- **Attack Succeeded:** {'✅' if log.attack_succeeded else '❌'}",
            f"- **Detected:** {'✅' if log.detected else '❌'}",
            f"- **Rule Written:** {'✅' if log.rule_written else '❌'}",
            "",
            "**Notes:**",
            log.notes or "_No notes_",
            "",
            "---",
            "",
        ])
    
    md_content = "\n".join(md_lines)
    
    response = make_response(md_content)
    response.headers["Content-Type"] = "text/markdown"
    response.headers["Content-Disposition"] = f'attachment; filename="purple_team_log_{now_utc.strftime("%Y%m%d")}.md"'
    return response


def _update_coverage(user_id: int, mitre_id: str, attack_succeeded: bool, detected: bool, rule_written: bool):
    """Update AttackCoverage record for a technique."""
    # In a full implementation, you'd look up the tactic from a MITRE reference table
    # For now, we'll leave tactic empty or derive from technique ID prefix
    tactic = _guess_tactic_from_technique(mitre_id)
    
    coverage = AttackCoverage.query.filter_by(
        user_id=user_id,
        mitre_technique_id=mitre_id
    ).first()
    
    if coverage is None:
        coverage = AttackCoverage(
            user_id=user_id,
            mitre_tactic=tactic,
            mitre_technique_id=mitre_id,
        )
        db.session.add(coverage)
    
    now = datetime.now(timezone.utc)
    if attack_succeeded and not coverage.first_attacked_date:
        coverage.first_attacked_date = now
    if detected and not coverage.first_detected_date:
        coverage.first_detected_date = now
    if rule_written:
        coverage.detection_rule_written = True
    coverage.last_reviewed_date = now


def _guess_tactic_from_technique(technique_id: str) -> str:
    """Rough guess of tactic from technique ID. In production, use a proper MITRE lookup table."""
    # This is a very rough mapping - in reality you'd have a proper MITRE ATT&CK reference table
    # T1xxx techniques span multiple tactics
    return "Unknown"


# Jinja filter for matrix cell rendering
@purple_team_bp.app_template_filter("coverage_cell")
def coverage_cell_filter(technique_id: str, matrix: dict, tactic: str):
    """Get coverage data for a specific technique in a tactic."""
    for tech in matrix.get(tactic, []):
        if tech["technique_id"] == technique_id:
            return tech
    return None