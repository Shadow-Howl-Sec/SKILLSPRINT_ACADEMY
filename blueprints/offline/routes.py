"""Offline-mode helper blueprint (plan §10, §6.3, §7).

Surfaces the static setup guides and the AI-tutor settings page that are
only meaningful in OFFLINE_MODE. Routes intentionally live behind their
own prefix so they don't collide with the existing eight blueprints.
"""
from __future__ import annotations

import json
from pathlib import Path

from flask import (Blueprint, render_template, redirect, url_for, request,
                   flash, current_app, jsonify, abort, g)
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

# VM prerequisite keys (stored in instance/vm_prereqs.json)
_VM_PREREQ_FILE = Path("instance/vm_prereqs.json")
_VM_LIST = [
    ("kali", "Kali Linux (Attacker)", "Primary attack platform with tools: nmap, impacket, bloodhound.py, hashcat, sqlmap, metasploit"),
    ("metasploitable", "Metasploitable2 (Target)", "Intentionally vulnerable Linux for exploitation practice"),
    ("dvwa", "DVWA / Juice Shop (Web Target)", "Damn Vulnerable Web App for OWASP Top 10 practice"),
    ("goad_dc", "GOAD-DC01 (AD Target)", "Game of Active Directory Domain Controller"),
    ("goad_win10", "GOAD-WIN10 (Windows Target)", "Windows 10 joined to GOAD domain for lateral movement"),
    ("wazuh", "Wazuh Manager (Detection)", "SIEM/XDR for log collection and alerting"),
]


def _load_vm_prereqs() -> dict:
    """Load VM prerequisite checkboxes from JSON file."""
    if _VM_PREREQ_FILE.exists():
        try:
            data = json.loads(_VM_PREREQ_FILE.read_text(encoding="utf-8"))
            if "metasploitable" not in data and "metasploitable2" in data:
                data["metasploitable"] = data["metasploitable2"]
            return data
        except Exception:
            return {}
    return {}


def _save_vm_prereqs(data: dict) -> None:
    """Save VM prerequisite checkboxes to JSON file."""
    _VM_PREREQ_FILE.parent.mkdir(parents=True, exist_ok=True)
    _VM_PREREQ_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


@offline_bp.route("/exercise/<int:exercise_id>")
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


@offline_bp.route("/lab-setup", methods=["GET", "POST"])
def lab_setup():
    """Lab setup guide & VM prerequisite checklist (Gap 1).

    - Shows checklist of required VMs for vm_exercise labs
    - User manually ticks off VMs they have running
    - vm_exercise labs are greyed out until their prerequisites are met
    """
    if request.method == "POST":
        # Save checklist state
        prereqs = {}
        for key, _, _ in _VM_LIST:
            prereqs[key] = request.form.get(f"vm_{key}") == "on"
        _save_vm_prereqs(prereqs)
        flash("VM checklist saved.", "success")
        return redirect(url_for("offline.lab_setup"))

    # Load current state
    prereqs = _load_vm_prereqs()

    # Get all vm_exercise labs and their requirements
    vm_labs = Lab.query.filter_by(provider="vm_exercise", is_active=True).all()
    lab_requirements = {}
    lab_all_ready = {}
    for lab in vm_labs:
        reqs = []
        if lab.attacker_vm and lab.attacker_vm.lower() != "kali":
            reqs.append(lab.attacker_vm.lower().replace(" ", "_"))
        elif lab.attacker_vm:
            reqs.append("kali")
        if lab.target_vm:
            # Map target VM names to our checklist keys
            target_lower = lab.target_vm.lower()
            if "metasploitable" in target_lower:
                reqs.append("metasploitable")
            elif "dvwa" in target_lower or "juice shop" in target_lower:
                reqs.append("dvwa")
            elif "goad" in target_lower and "dc" in target_lower:
                reqs.append("goad_dc")
            elif "goad" in target_lower and "win" in target_lower:
                reqs.append("goad_win10")
            else:
                reqs.append(target_lower.replace(" ", "_"))
        if lab.detection_vm and "wazuh" in lab.detection_vm.lower():
            reqs.append("wazuh")
        lab_requirements[lab.id] = reqs
        
        # Pre-compute whether all prerequisites are met
        lab_all_ready[lab.id] = all(prereqs.get(req, False) for req in reqs)

    return render_template("offline/lab_setup.html",
                           vm_list=_VM_LIST,
                           prereqs=prereqs,
                           vm_labs=vm_labs,
                           lab_requirements=lab_requirements,
                           lab_all_ready=lab_all_ready)


@offline_bp.route("/resource-cache")
def resource_cache_info():
    """Shows status of the one-time resource cache sync (plan §6.2)."""
    return render_template("offline/resource_cache.html")


@offline_bp.route("/settings/ai-tutor", methods=["GET", "POST"])
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