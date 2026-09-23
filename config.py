import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
EXPORTS_DIR = os.path.join(INSTANCE_DIR, "exports")

class Config:
    # Flask sessions and application secret
    SECRET_KEY = os.environ.get("SECRET_KEY", "tma-dev-secret-key-must-be-at-least-32-bytes-long")

    # Use SQLite database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(INSTANCE_DIR, "trekmanager.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Token Secrets
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "tma-dev-jwt-secret-key-must-be-at-least-32-bytes-long")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8  # 8 hours
    JWT_TOKEN_LOCATION = ["headers"]

    # Default admin account
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trekmanager.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "System Administrator")

    # Redis/In-Memory Cache configuration
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 120  # seconds - cache expiry for trek listings

    # Celery uses Redis as both the broker and the backend
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

    # Mail Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 25))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "no-reply@trekmanager.local"
    )
    MAIL_SUPPRESS_SEND = os.environ.get(
        "MAIL_SUPPRESS_SEND", "true"
    ).lower() == "true"

    EXPORTS_DIR = EXPORTS_DIR