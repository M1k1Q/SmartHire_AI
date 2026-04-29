"""
config.py — Application configuration for Smart Recruitment Platform.
Reads from environment variables with sensible defaults for development.
"""
import os
from datetime import timedelta


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "24")))
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_CSRF_PROTECT = False

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/recruitment_db")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "recruitment_db")

    # File uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "..", "uploads"))
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # ML Models storage
    MODELS_FOLDER = os.getenv("MODELS_FOLDER", os.path.join(os.path.dirname(__file__), "..", "ml_models"))

    # CORS
    CORS_ORIGINS = ["*"]

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "recruitment.log")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
