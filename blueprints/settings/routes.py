# blueprints/settings/routes.py
import os
import hmac
import hashlib
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


@settings_bp.route("/api/update/status", methods=["GET", "POST"])
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
    """Apply an update by downloading and installing it.

    In OFFLINE_MODE, updates are disabled - this endpoint will return an error.
    In online mode, requires HMAC-SHA256 signature verification to prevent unauthorized updates.
    Signature is computed as: HMAC-SHA256(UPDATE_HMAC_SECRET, download_url)
    """
    from flask import current_app
    data = request.get_json(silent=True) or {}
    download_url = data.get("download_url")

    if not download_url:
        return jsonify({"error": "download_url required"}), 400

    # In offline mode, updates are not supported
    offline_mode = current_app.config.get('OFFLINE_MODE', True)
    if offline_mode:
        return jsonify({"error": "Updates disabled in offline mode"}), 400

    # Online mode: require HMAC signature
    signature = data.get("signature")  # hex-encoded HMAC-SHA256
    if not signature:
        return jsonify({"error": "signature required"}), 400

    # Verify HMAC signature
    hmac_secret = current_app.config.get("UPDATE_HMAC_SECRET")
    if not hmac_secret:
        current_app.logger.error("UPDATE_HMAC_SECRET not configured")
        return jsonify({"error": "server not configured for updates"}), 500

    expected_signature = hmac.new(
        hmac_secret.encode('utf-8'),
        download_url.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()  # type: ignore[attr-defined]

    if not hmac.compare_digest(signature, expected_signature):
        current_app.logger.warning("Invalid update signature from %s", request.remote_addr)
        return jsonify({"error": "invalid signature"}), 403

    apply_update(download_url)
    # Process exits inside apply_update, no response sent
    return jsonify({"status": "updating"})


# Exempt API endpoints from CSRF protection
from extensions import csrf
csrf.exempt(settings_bp)