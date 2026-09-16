import os
import secrets
import sys
from dotenv import load_dotenv
from paths import get_data_root

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _persisted_secret(name: str, filename: str, *, min_length: int = 32) -> str:
    """Return a stable secret from environment or a per-user file, never a weak fallback."""
    env_value = os.environ.get(name)
    if env_value and env_value.strip() and len(env_value.strip()) >= min_length:
        return env_value.strip()

    data_root = get_data_root()
    secret_path = os.path.join(data_root, filename)
    existing = None
    try:
        if os.path.exists(secret_path):
            with open(secret_path, 'r', encoding='utf-8') as fh:
                existing = fh.read().strip()
    except OSError:
        existing = None

    if existing and len(existing) >= min_length:
        os.environ[name] = existing
        return existing

    generated = secrets.token_hex(32)
    try:
        os.makedirs(data_root, exist_ok=True)
        with open(secret_path, 'w', encoding='utf-8') as fh:
            fh.write(generated)
        os.chmod(secret_path, 0o600)
    except OSError:
        pass
    os.environ[name] = generated
    return generated


class Config:
    """SkillSprint Academy configuration — fully offline Purple Team mastery platform."""
    SECRET_KEY = _persisted_secret('SECRET_KEY', 'secret.key')
    APP_NAME = 'SkillSprint Academy'
    APP_TAGLINE = 'Zero to Purple Team Mastery — Fully Offline'

    OFFLINE_MODE = True
    OFFLINE_BIND_HOST = os.environ.get('OFFLINE_BIND_HOST', '127.0.0.1')
    OFFLINE_BIND_PORT = int(os.environ.get('OFFLINE_BIND_PORT', 52837))

    _default_database = os.path.join(
        get_data_root() if getattr(sys, 'frozen', False) else os.getcwd(),
        'skillsprint.db'
    ).replace('\\', '/')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + _default_database)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    AI_TUTOR_PROVIDER = 'auto'
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b-instruct')

    XP_PER_CONTENT_ITEM = 10
    XP_PER_LAB = 50
    XP_PER_QUIZ = 20
    XP_STREAK_BONUS = 10
    STREAK_FREEZES_PER_WEEK = 1

    ROADMAP_BUFFER_PERCENT = 0.15

    UPDATE_HMAC_SECRET = _persisted_secret('UPDATE_HMAC_SECRET', 'update_hmac_secret.key')

    VM_CONFIG_KEY = _persisted_secret('VM_CONFIG_KEY', 'vm_config_key.key')

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLES_DIR = os.path.join(BASE_DIR, 'bundles')
    BUNDLES_LABS_DIR = os.path.join(BUNDLES_DIR, 'labs')
    RESOURCE_CACHE_DIR = os.path.join(BASE_DIR, 'instance', 'resource_cache')
    USER_UPLOADS_DIR = os.path.join(BASE_DIR, 'instance', 'user_uploads')

    # VM Connection Config (host-only IPs from VirtualBox setup)
    VM_KALI_IP = os.environ.get('VM_KALI_IP', '192.168.56.5')
    VM_DC01_IP = os.environ.get('VM_DC01_IP', '192.168.56.10')
    VM_WIN10_IP = os.environ.get('VM_WIN10_IP', '192.168.56.11')
    VM_DVWA_IP = os.environ.get('VM_DVWA_IP', '192.168.56.21')
    VM_METASPLOITABLE_IP = os.environ.get('VM_METASPLOITABLE_IP', '192.168.56.20')
    VM_WAZUH_IP = os.environ.get('VM_WAZUH_IP', '192.168.56.30')
    VM_SSH_USER = os.environ.get('VM_SSH_USER', 'kali')
    VM_SSH_KEY = os.environ.get('VM_SSH_KEY', '')
    VM_WINRM_USER = os.environ.get('VM_WINRM_USER', 'Administrator')
    VM_WINRM_PASS = os.environ.get('VM_WINRM_PASS', '')
    WAZUH_API_URL = os.environ.get('WAZUH_API_URL', 'https://192.168.56.30:55000')
    WAZUH_API_USER = os.environ.get('WAZUH_API_USER', 'wazuh')
    WAZUH_API_PASS = os.environ.get('WAZUH_API_PASS', '')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False