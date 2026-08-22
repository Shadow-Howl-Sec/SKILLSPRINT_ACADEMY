import os
from dotenv import load_dotenv

# Load environment variables once at the config level
load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Base configuration class."""
    # Core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key')

    # ------------------------------------------------------------------
    # OFFLINE MODE (see SkillSprint_Offline_Plan.md §2.3, §14)
    # When True the platform runs entirely on 127.0.0.1 with no internet
    # dependency: Razorpay / Google OAuth / SMTP are gated off, the AI tutor
    # falls back to Ollama-then-rules, the contact form stores messages
    # locally, and Talisman CSP is tightened to 'self' only.
    # ------------------------------------------------------------------
    OFFLINE_MODE = _env_bool('OFFLINE_MODE', True)  # default ON for this build
    OFFLINE_BIND_HOST = os.environ.get('OFFLINE_BIND_HOST', '127.0.0.1')
    OFFLINE_BIND_PORT = int(os.environ.get('OFFLINE_BIND_PORT', 5000))

    # Database Configuration (SQLite locally by default in offline mode).
    # The original cloud plan supported Postgres/Oracle; offline uses SQLite.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///skillsprint.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Mail — disabled in OFFLINE_MODE (no SMTP available locally)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'skillsprint_support@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_email_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'skillsprint_support@gmail.com')

    # Razorpay — disabled in OFFLINE_MODE
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_xxxxxxxx')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'xxxxxxxxxxxxxx')

    # Google OAuth — disabled in OFFLINE_MODE
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', 'your_google_client_id_here')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', 'your_google_client_secret_here')

    # Admin Credentials
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@skillsprint.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'fallback_secure_pw_123!')

    # Security Headers & Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # --- CyberSec Platform ---
    # AI Tutor provider: auto | ollama | anthropic | rules
    AI_TUTOR_PROVIDER = os.environ.get('AI_TUTOR_PROVIDER', 'auto')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

    # Ollama (offline LLM) — see plan §7.1
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b-instruct')
    OLLAMA_PROBE_TIMEOUT = float(os.environ.get('OLLAMA_PROBE_TIMEOUT', 0.2))  # seconds

    # XP & Gamification
    XP_PER_CONTENT_ITEM = int(os.environ.get('XP_PER_CONTENT_ITEM', 10))
    XP_PER_LAB = int(os.environ.get('XP_PER_LAB', 25))
    XP_PER_QUIZ = int(os.environ.get('XP_PER_QUIZ', 15))
    XP_STREAK_BONUS = int(os.environ.get('XP_STREAK_BONUS', 5))
    STREAK_FREEZES_PER_WEEK = int(os.environ.get('STREAK_FREEZES_PER_WEEK', 1))

    # Assessment Engine
    ASSESSMENT_QUESTIONS_PER_AREA = int(os.environ.get('ASSESSMENT_QUESTIONS_PER_AREA', 5))
    ASSESSMENT_START_DIFFICULTY = int(os.environ.get('ASSESSMENT_START_DIFFICULTY', 3))  # 1-5

    # Roadmap Engine
    ROADMAP_BUFFER_PERCENT = float(os.environ.get('ROADMAP_BUFFER_PERCENT', 0.20))  # 20% buffer for spaced rep

    # Path conventions for offline artifacts (plan §8, §12)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLES_DIR = os.path.join(BASE_DIR, 'bundles')
    BUNDLES_LABS_DIR = os.path.join(BUNDLES_DIR, 'labs')
    RESOURCE_CACHE_DIR = os.path.join(BASE_DIR, 'instance', 'resource_cache')
    USER_UPLOADS_DIR = os.path.join(BASE_DIR, 'instance', 'user_uploads')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
