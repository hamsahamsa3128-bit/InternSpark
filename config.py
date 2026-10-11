import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'internspark-dev-secret-key-change-in-production-2026')
    DATABASE = os.path.join(BASE_DIR, os.environ.get('DATABASE_PATH', 'internspark.db'))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5 MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}
    
    # Session Security Settings
    SESSION_COOKIE_HTTPONLY = True       # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'      # Protect against CSRF in cross-site requests
    SESSION_COOKIE_SECURE = False        # In development: HTTP. In production: True (requires HTTPS)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DATABASE = os.path.join(BASE_DIR, 'test_internspark.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'test_uploads')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True         # Require HTTPS in production

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
