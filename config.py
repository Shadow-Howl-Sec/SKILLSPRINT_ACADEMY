import os
from dotenv import load_dotenv

# Load environment variables once at the config level
load_dotenv()

class Config:
    """Base configuration class."""
    # Core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key')
    
    # Database Configuration
    # Defaults to a local SQLite database for local development if .env is missing.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///skillsprint.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'skillsprint_support@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your_email_password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'skillsprint_support@gmail.com')
    
    # Razorpay
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_xxxxxxxx')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'xxxxxxxxxxxxxx')
    
    # Google OAuth
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

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
