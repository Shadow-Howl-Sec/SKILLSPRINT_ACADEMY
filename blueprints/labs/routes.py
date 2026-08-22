"""Virtual labs (plan §5.5; offline plan §5).

  /labs            browse all labs (filterable by SkillArea / provider)
                   Offline-mode: greys out link-out labs and shows only
                   self_hosted_offline ones unless the user explicitly asks.
  /lab/<id>        lab launcher — renders bundled-challenge buttons +
                   proof submission UI for offline labs.
  /lab/<id>/submit (POST) validate flag (self-hosted) or store self-report.
  /lab/<id>/file/<path> serve a bundled challenge artifact (read-only).
"""
from __future__ import annotations

import hashlib
import os

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, abort, current_app, send_from_directory)
from flask_login import login_required, current_user
from werkzeug.utils import safe_join

from extensions import db
from models import Lab, RoadmapItem

from services.xp_service import award_xp, touch_streak
from datetime import date, datetime

labs_bp = Blueprint("labs", __name__)


# Providers that require the public internet — hidden in OFFLINE_MODE (plan §5.4).
_ONLINE_PROVIDERS = {"tryhackme", "htb", "portswigger", "overthewire", "picoctf"}


def _offline_mode() -> bool:
    return bool(current_app.config.get("OFFLINE_MODE", False))


@labs_bp.route("/labs")
@login_required
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
@login_required
def detail(lab_id: int):
    lab = Lab.query.get_or_404(lab_id)
    if _offline_mode() and lab.provider in _ONLINE_PROVIDERS:
        # Link-out labs are disabled in offline mode (plan §5.4 / §9).
        flash("This lab requires internet and is disabled in offline mode.", "info")
        return redirect(url_for("labs.browse"))
    return render_template("labs/detail.html", lab=lab,
                           OFFLINE_MODE=_offline_mode())


@labs_bp.route("/lab/<int:lab_id>/file/<path:filename>")
@login_required
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


@labs_bp.route("/lab/<int:lab_id>/submit", methods=["POST"])
@login_required
def submit(lab_id: int):
    lab = Lab.query.get_or_404(lab_id)
    proof = request.form.get("proof", "").strip()

    if lab.proof_type == "flag" and lab.flag_hash:
        actual = hashlib.sha256(proof.encode()).hexdigest()
        if actual != lab.flag_hash:
            flash("Incorrect flag — keep trying!", "error")
            return redirect(url_for("labs.detail", lab_id=lab.id))
    elif lab.proof_type == "self_report":
        if not proof:
            flash("Add a short note about what you did.", "error")
            return redirect(url_for("labs.detail", lab_id=lab.id))
    # screenshot / writeup_url: accept anything non-empty for the MVP

    award_xp(current_user.id, "lab", lab.id, xp_amount=lab.xp_reward,
             description=f"Completed lab: {lab.title}")
    touch_streak(current_user.id, date.today())
    db.session.commit()
    flash(f"+{lab.xp_reward} XP — lab complete!", "success")
    return redirect(url_for("labs.browse"))
