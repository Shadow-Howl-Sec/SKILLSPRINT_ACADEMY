import os
import sys
import json
import secrets
import webbrowser
import threading
import atexit
from datetime import datetime, timezone
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, flash, abort, g)
from dotenv import load_dotenv
from sqlalchemy import text
from extensions import db, migrate, limiter, csrf
load_dotenv()

if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
else:
    app = Flask(__name__)
app.config.from_object('config.Config')

OFFLINE_MODE = True


# ---------------------------------------------------------------------------
# CSP — Hardened for offline operation with nonce-based script execution
# ---------------------------------------------------------------------------
_csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'strict-dynamic'"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'font-src': ["'self'", 'data:'],
    'img-src': ["'self'", 'data:'],
    'connect-src': ["'self'", 'http://127.0.0.1:11434'],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'none'"],
}

from flask_talisman import Talisman
talisman = Talisman(
    app,
    content_security_policy=_csp,
    force_https=False,
    strict_transport_security=False,
    content_security_policy_nonce_in=['script-src'],
)

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------
db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)
csrf.init_app(app)

# ---------------------------------------------------------------------------
# Nonce for CSP — expose to templates
# ---------------------------------------------------------------------------
@app.context_processor
def inject_nonce():
    return {'csp_nonce': getattr(request, 'csp_nonce', '')}

# ---------------------------------------------------------------------------
# Blueprints — SkillSprint Purple Team only
# ---------------------------------------------------------------------------
from blueprints.roadmap.routes import roadmap_bp
from blueprints.dashboard.routes import dashboard_bp
from blueprints.labs.routes import labs_bp
from blueprints.purple_team.routes import purple_team_bp
from blueprints.offline.routes import offline_bp
from blueprints.job_roles.routes import job_roles_bp
from blueprints.library.routes import library_bp
from blueprints.assistant.routes import assistant_bp
from blueprints.assessment.routes import assessment_bp
from blueprints.settings.routes import settings_bp
from blueprints.topics.routes import topics_bp

app.register_blueprint(roadmap_bp)
app.register_blueprint(topics_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(labs_bp)
app.register_blueprint(purple_team_bp)
app.register_blueprint(offline_bp)
app.register_blueprint(job_roles_bp)
app.register_blueprint(library_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(settings_bp)

from models import User

# ---------------------------------------------------------------------------
# Start background services
# ---------------------------------------------------------------------------
# Note: scheduler service is initialized lazily on first request to avoid
# circular imports. Update checker is started after app creation.

# ---------------------------------------------------------------------------
# Single-user context
# ---------------------------------------------------------------------------
@app.before_request
def load_default_user():
    if not hasattr(g, 'user'):
        user = User.query.first()
        if user is None:
            user = User(
                username='Shubham',
                email='shubham@skillsprint.local',
                first_name='Shubham',
                last_name='',
                email_verified=True,
                is_active=True,
                is_admin=True,
            )
            user.set_password('skillsprint')
            db.session.add(user)
            db.session.commit()
        g.user = user


# Start update checker after first request context is available
_update_checker_started = False

@app.before_request
def start_background_services():
    global _update_checker_started
    if not _update_checker_started:
        try:
            from services.scheduler_service import start_update_checker
            start_update_checker(app)
            _update_checker_started = True
        except Exception as e:
            app.logger.warning(f"Failed to start update checker: {e}")


@app.template_filter("from_json")
def from_json_filter(value):
    if not value:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


@app.template_filter("basename")
def basename_filter(value):
    if not value:
        return ""
    return os.path.basename(str(value).replace("\\", "/").rstrip("/"))


@app.template_filter("markdown")
def markdown_filter(value):
    if not value:
        return ""
    try:
        import markdown as md
        return md.markdown(value, extensions=['fenced_code', 'tables', 'codehilite'])
    except ImportError:
        return value.replace('\n', '<br>\n')


@app.context_processor
def inject_globals():
    from datetime import date
    update_info = None
    try:
        from services.scheduler_service import get_cached_update_info
        update_info = get_cached_update_info()
    except Exception:
        pass
    
    return {
        "now": date.today().isoformat(),
        "OFFLINE_MODE": True,
        "current_user": g.get('user'),
        "APP_NAME": app.config.get('APP_NAME', 'SkillSprint Academy'),
        "APP_TAGLINE": app.config.get('APP_TAGLINE', 'Zero to Purple Team Mastery'),
        "UPDATE_RELEASES_URL": "https://github.com/Shadow-Howl-Sec/SKILLSPRINT_ACADEMY/releases",
        "update_info": update_info,
    }


@app.route('/')
def index():
    from models import StreakRecord, Roadmap
    user = g.get('user')
    xp = user.total_xp if user else 0
    streak = StreakRecord.query.filter_by(user_id=user.id).first() if user else None
    
    # Check if user has an active roadmap
    has_roadmap = False
    active_roadmap = None
    if user:
        active_roadmap = Roadmap.query.filter_by(user_id=user.id, status='active').first()
        has_roadmap = active_roadmap is not None
    
    return render_template('index.html', xp=xp, streak=streak, has_roadmap=has_roadmap, active_roadmap=active_roadmap)


@app.route('/health')
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected', 'offline': True}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/health/vm')
def vm_health_check():
    """Verify VM connectivity for labs."""
    from models import VMConfig
    import socket
    
    vm = VMConfig.query.filter_by(user_id=g.user.id).first()
    if not vm:
        return jsonify({'status': 'no_config', 'vms': {}})
    
    results = {}
    vm_dict = vm.get_vm_dict()
    for name, config in vm_dict.items():
        if not isinstance(config, dict):
            continue
        ip = config.get('ip')
        port = config.get('ssh_port') or config.get('winrm_port') or config.get('port') or 22
        if ip:
            try:
                sock = socket.create_connection((ip, port), timeout=2)
                sock.close()
                results[name] = {'status': 'reachable', 'ip': ip, 'port': port}
            except Exception as e:
                results[name] = {'status': 'unreachable', 'ip': ip, 'port': port, 'error': str(e)}
        else:
            results[name] = {'status': 'not_configured'}
    
    all_ok = all(r['status'] == 'reachable' for r in results.values() if r['status'] != 'not_configured')
    return jsonify({
        'status': 'healthy' if all_ok else 'degraded', 
        'vms': results,
        'validated': vm.is_validated
    })


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    try:
        db.session.rollback()
    except Exception:
        pass
    return render_template('errors/500.html'), 500


# ---------------------------------------------------------------------------
# Shutdown handlers
# ---------------------------------------------------------------------------
def shutdown_background_services():
    """Clean up background threads on process exit."""
    try:
        from services.scheduler_service import stop_update_checker
        stop_update_checker()
    except Exception:
        pass
    try:
        from services.ai_tutor_service import shutdown_executor
        shutdown_executor()
    except Exception:
        pass

atexit.register(shutdown_background_services)


def create_tables():
    with app.app_context():
        try:
            db.create_all()
            print("[OK] Database tables created successfully!")
        except Exception as e:
            print(f"[ERR] Error creating database tables: {e}")
            return
        print("Database initialized successfully!")
        # Seed reference data if empty
        try:
            from models import JobRole
            if JobRole.query.count() == 0:
                print("Seeding reference data...")
                import seed_comprehensive
                seed_comprehensive.main()
                print("Reference data seeded successfully!")
        except Exception as e:
            print(f"[WARN] Seeding failed: {e}")


if __name__ == '__main__':
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        create_tables()
        bind_host = app.config.get('OFFLINE_BIND_HOST', '127.0.0.1')
        bind_port = int(app.config.get('OFFLINE_BIND_PORT', 52837))
        url = f"http://{bind_host}:{bind_port}"
        print(f" {app.config.get('APP_NAME', 'skillsprint')} starting...")
        print(f" [OFFLINE MODE] binding to {url}")
        
        # Open browser in a background thread after 1.5 seconds
        def open_browser():
            import time
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()
        app.run(debug=False, host=bind_host, port=bind_port)
    except KeyboardInterrupt:
        print(f"\n {app.config.get('APP_NAME', 'skillsprint')} stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")