import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    """SkillSprint Academy configuration — fully offline Purple Team mastery platform."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'skillsprint-dev-secret-change-in-prod')
    APP_NAME = 'SkillSprint Academy'
    APP_TAGLINE = 'Zero to Purple Team Mastery — Fully Offline'

    OFFLINE_MODE = True
    OFFLINE_BIND_HOST = os.environ.get('OFFLINE_BIND_HOST', '127.0.0.1')
    OFFLINE_BIND_PORT = int(os.environ.get('OFFLINE_BIND_PORT', 52837))

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///skillsprint.db')
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

    UPDATE_HMAC_SECRET = os.environ.get('UPDATE_HMAC_SECRET', '')

    VM_CONFIG_KEY = os.environ.get('VM_CONFIG_KEY', '')

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