# blueprints/settings/routes.py
from flask import Blueprint, request, jsonify, current_app
from services.update_service import apply_update
from services.scheduler_service import check_for_updates, get_cached_update_info

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/api/update/check", methods=["GET", "POST"])
def check_update():
    """Check for application updates."""
    force = request.args.get("force") == "1" or (request.get_json(silent=True) or {}).get("force")
    
    try:
        update_info = check_for_updates(current_app, force=force)
        if update_info is None:
            return jsonify({
                "update_available": None,
                "current_version": "unknown",
                "error": "check_failed"
            })
        
        # Add version info if not present
        if "current_version" not in update_info:
            from paths import get_app_root
            import os
            version_file = os.path.join(get_app_root(), "VERSION")
            try:
                with open(version_file) as f:
                    update_info["current_version"] = f.read().strip()
            except Exception:
                update_info["current_version"] = "1.0.0"
        
        return jsonify(update_info)
    except Exception as e:
        current_app.logger.error(f"Update check error: {e}")
        return jsonify({
            "update_available": None,
            "current_version": "unknown",
            "error": str(e)
        }), 500


@settings_bp.route("/api/update/status")
def update_status():
    """Get cached update status without checking."""
    try:
        cached = get_cached_update_info()
        if cached:
            return jsonify(cached)
    except Exception:
        pass
    
    return jsonify({
        "update_available": None,
        "current_version": "1.0.0"
    })


@settings_bp.route("/settings/apply-update", methods=["POST"])
def apply_update_route():
    """Apply an update by downloading and installing it."""
    data = request.get_json(silent=True) or {}
    download_url = data.get("download_url")
    if not download_url:
        return jsonify({"error": "download_url required"}), 400
    
    apply_update(download_url)
    # Process exits inside apply_update, no response sent
    return jsonify({"status": "updating"})


# Exempt API endpoints from CSRF protection
from app import csrf
csrf.exempt(settings_bp)