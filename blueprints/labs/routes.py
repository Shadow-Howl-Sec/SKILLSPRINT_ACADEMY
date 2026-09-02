"""Virtual labs (plan §5.5; offline plan §5).

  /labs            browse all labs (filterable by SkillArea / provider)
                   Offline-mode: greys out link-out labs and shows only
                   self_hosted_offline / vm_exercise ones unless the user explicitly asks.
  /lab/<id>        lab launcher — renders bundled-challenge buttons +
                   proof submission UI for offline labs.
                   For vm_exercise: renders attack/detection instructions + checklist.
  /lab/<id>/submit (POST) validate flag (self-hosted) or store self-report/checklist.
  /lab/<id>/file/<path> serve a bundled challenge artifact (read-only).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, abort, current_app, send_from_directory, g)
from werkzeug.utils import safe_join

from extensions import db
from models import Lab, RoadmapItem, PurpleTeamExerciseLog, AttackCoverage

from services.xp_service import award_xp, touch_streak

labs_bp =Blueprint("labs", __name__)


# Providers that require the public internet — hidden in OFFLINE_MODE (plan §5.4).
_ONLINE_PROVIDERS = {"tryhackme", "htb", "portswigger", "overthewire", "picoctf"}


def _offline_mode() -> bool:
    return bool(current_app.config.get("OFFLINE_MODE", False))


@labs_bp.route("/labs")
def browse():
    provider = request.args.get("provider")
    show_all = request.args.get("all") == "1"
    q = Lab.query.filter_by(is_active=True)
    if provider:
        q = q.filter_by(provider=provider)
    labs = q.order_by(Lab.difficulty).all()

    if _offline_mode() and not show_all:
        # Grey out link-out labs in the browse UI (plan §5.4). We keep the rows
        # in the result so the template can render them as "requires internet".
        # vm_exercise labs ARE offline-available (they run on user's VMs).
        offline_labs = [l for l in labs if l.is_offline_available]
        online_labs = [l for l in labs
                       if l.provider in _ONLINE_PROVIDERS]
        return render_template("labs/browse.html", labs=offline_labs,
                               online_labs=online_labs,
                               current_provider=provider,
                               show_all=show_all,
                               OFFLINE_MODE=True)
    return render_template("labs/browse.html", labs=labs,
                           online_labs=[],
                           current_provider=provider,
                           show_all=show_all,
                           OFFLINE_MODE=_offline_mode())


@labs_bp.route("/lab/<int:lab_id>")
def detail(lab_id: int):
    lab = Lab.query.get_or_404(lab_id)
    if _offline_mode() and lab.provider in _ONLINE_PROVIDERS:
        # Link-out labs are disabled in offline mode (plan §5.4 / §9).
        flash("This lab requires internet and is disabled in offline mode.", "info")
        return redirect(url_for("labs.browse"))
    
    # Use different template for vm_exercise labs
    if lab.is_vm_exercise:
        return render_template("labs/detail_vm_exercise.html", lab=lab,
                               OFFLINE_MODE=_offline_mode())
    return render_template("labs/detail.html", lab=lab,
                           OFFLINE_MODE=_offline_mode())


@labs_bp.route("/lab/<int:lab_id>/file/<path:filename>")
def serve_bundle_file(lab_id: int, filename: str):
    """Serve a bundled challenge artifact (plan §5.3). Read-only & sandboxed.

    `filename` is interpreted relative to the app's bundles/labs/ root; we use
    safe_join + an explicit under-bundles-dir check so no escaping is possible.
    """
    lab = Lab.query.get_or_404(lab_id)
    if not lab.is_offline_available:
        abort(404)
    bundles_root = current_app.config.get("BUNDLES_LABS_DIR")
    if not bundles_root:
        abort(404)
    # The lab may carry url_or_container_ref like "networking/capture_challenge1.pcap"
    sub = (lab.url_or_container_ref or "").strip("/").replace("\\", "/")
    full = safe_join(bundles_root, os.path.join(sub, filename)) if sub else \
           safe_join(bundles_root, filename)
    if not full or not os.path.isfile(full):
        abort(404)
    # Confirm resolved path is still under bundles_root.
    if os.path.commonpath([os.path.abspath(full),
                           os.path.abspath(bundles_root)]) != os.path.abspath(bundles_root):
        abort(404)
    return send_from_directory(os.path.dirname(full), os.path.basename(full),
                               as_attachment=True)


def _log_purple_team_exercise(lab, form_data):
    """Create PurpleTeamExerciseLog entry and update AttackCoverage."""
    log = PurpleTeamExerciseLog(
        user_id=g.user.id,
        lab_id=lab.id,
        technique_title=lab.title,
        mitre_id=lab.mitre_technique,
        attack_succeeded=form_data.get('attack_succeeded', False),
        detected=form_data.get('detected', False),
        rule_written=form_data.get('rule_written', False),
        notes=form_data.get('notes', ''),
    )
    db.session.add(log)
    db.session.flush()

    # Update AttackCoverage
    if lab.mitre_technique:
        # We need the tactic - for now extract from technique or leave empty
        # In a full implementation, you'd have a MITRE reference table
        coverage = AttackCoverage.query.filter_by(
            user_id=g.user.id,
            mitre_technique_id=lab.mitre_technique
        ).first()
        if coverage is None:
            coverage = AttackCoverage(
                user_id=g.user.id,
                mitre_tactic="",  # Would be populated from MITRE reference data
                mitre_technique_id=lab.mitre_technique,
            )
            db.session.add(coverage)
        
        now = datetime.utcnow()
        if form_data.get('attack_succeeded') and not coverage.first_attacked_date:
            coverage.first_attacked_date = now
        if form_data.get('detected') and not coverage.first_detected_date:
            coverage.first_detected_date = now
        if form_data.get('rule_written'):
            coverage.detection_rule_written = True
        coverage.last_reviewed_date = now


@labs_bp.route("/lab/<int:lab_id>/submit", methods=["POST"])
def submit(lab_id: int):
    lab = Lab.query.get_or_404(lab_id)
    proof = request.form.get("proof", "").strip()

    # Handle vm_exercise checklist proof
    if lab.is_vm_exercise:
        # Proof is JSON string from the checklist form
        try:
            form_data = json.loads(proof) if proof else {}
        except json.JSONDecodeError:
            form_data = {}
        
        # For vm_exercise, at least one checkbox or notes must be present
        has_input = any([
            form_data.get('attack_succeeded'),
            form_data.get('detected'),
            form_data.get('rule_written'),
            form_data.get('notes', '').strip()
        ])
        if not has_input:
            flash("Please check at least one item or add notes before submitting.", "error")
            return redirect(url_for("labs.detail", lab_id=lab.id))
        
        # Log the purple team exercise
        _log_purple_team_exercise(lab, form_data)
        
    elif lab.proof_type == "flag" and lab.flag_hash:
        actual = hashlib.sha256(proof.encode()).hexdigest()
        if actual != lab.flag_hash:
            flash("Incorrect flag — keep trying!", "error")
            return redirect(url_for("labs.detail", lab_id=lab.id))
    elif lab.proof_type == "self_report":
        if not proof:
            flash("Add a short note about what you did.", "error")
            return redirect(url_for("labs.detail", lab_id=lab.id))
    # screenshot / writeup_url / self_report_checklist: accept anything non-empty for MVP

    award_xp(g.user.id, "lab", lab.id, xp_amount=lab.xp_reward,
             description=f"Completed lab: {lab.title}")
    touch_streak(g.user.id, date.today())
    db.session.commit()
    flash(f"+{lab.xp_reward} XP — lab complete!", "success")
    return redirect(url_for("labs.browse"))