"""Offline-mode helper blueprint (plan §10, §6.3, §7).

Surfaces the static setup guides and the AI-tutor settings page that are
only meaningful in OFFLINE_MODE. Routes intentionally live behind their
own prefix so they don't collide with the existing eight blueprints.
"""
from __future__ import annotations

import json

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, current_app, jsonify, abort)
from flask_login import login_required

from extensions import db
from models import ContentItem, Lab

from services.ai_tutor_service import ollama_alive, list_ollama_models

offline_bp = Blueprint("offline", __name__, url_prefix="/offline")


# Pre-fix lookups to avoid recreating the include path on every render.
_KIND_TEMPLATE = {
    "code_py":           "exercises/code_py.html",
    "code_js":           "exercises/code_js.html",
    "quiz_interactive":  "exercises/quiz_interactive.html",
    "regex_lab":         "exercises/regex_lab.html",
    "cipher_lab":        "exercises/cipher_lab.html",
    "pcap_challenge":    "exercises/pcap_challenge.html",
    "binary_inspector":  "exercises/binary_inspector.html",
}


@offline_bp.route("/exercise/<int:exercise_id>")
@login_required
def view_exercise(exercise_id: int):
    """Render an `interactive_exercise` ContentItem (plan §4 / §11 Phase C)."""
    item = ContentItem.query.get_or_404(exercise_id)
    if item.type != "interactive_exercise" or not item.is_active:
        abort(404)
    spec_json = item.exercise_spec or "{}"
    import json
    try:
        spec = json.loads(spec_json)
    except Exception:
        spec = {}
    kind = spec.get("kind", "code_py")
    kind_template = _KIND_TEMPLATE.get(kind, "exercises/code_py.html")
    return render_template("exercises/base.html",
                           exercise=item,
                           spec=spec,
                           spec_json=spec_json,
                           kind_template=kind_template)


@offline_bp.route("/about")
def about():
    """Explains what offline mode does / doesn't do (plan §14)."""
    return render_template("offline/about.html",
                           offline=current_app.config.get("OFFLINE_MODE", False))


@offline_bp.route("/lab-setup")
def lab_setup():
    """Lab setup guide — Kali VM + bundled challenges (plan §5, §10.2)."""
    return render_template("offline/lab_setup.html")


@offline_bp.route("/resource-cache")
def resource_cache_info():
    """Shows status of the one-time resource cache sync (plan §6.2)."""
    return render_template("offline/resource_cache.html")


@offline_bp.route("/settings/ai-tutor", methods=["GET", "POST"])
@login_required
def ai_tutor_settings():
    """Pick the Ollama model and test the connection (plan §7.1)."""
    cfg = current_app.config
    current_model = cfg.get("OLLAMA_MODEL", "llama3.1:8b-instruct")
    base_url = cfg.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    models: list[str] = []
    alive = False

    if request.method == "POST":
        # The actual model selection lives in env / app.config at runtime;
        # we persist a small override into the user's .env via a side file so
        # subsequent launcher runs pick it up.
        chosen = request.form.get("model", "").strip()
        if chosen:
            try:
                from pathlib import Path
                override = Path(current_app.config["BASE_DIR"]) / "instance" / "ollama_model.txt"
                override.parent.mkdir(parents=True, exist_ok=True)
                override.write_text(chosen, encoding="utf-8")
                current_app.config["OLLAMA_MODEL"] = chosen
                current_model = chosen
                flash(f"AI tutor model set to {chosen}", "success")
            except Exception as exc:
                flash(f"Could not persist model choice: {exc}", "error")

    test = request.args.get("test") == "1"
    if test or request.method == "POST":
        alive = ollama_alive()
        if alive:
            try:
                models = list_ollama_models()
            except Exception:
                models = []
        flash(("Ollama is reachable." if alive
               else "Ollama not reachable — start it with `ollama serve` "
                    "or the setup script."),
              "success" if alive else "warning")

    return render_template("offline/ai_tutor_settings.html",
                           offline=current_app.config.get("OFFLINE_MODE", False),
                           current_model=current_model,
                           base_url=base_url,
                           ollama_alive=alive,
                           models=models)
