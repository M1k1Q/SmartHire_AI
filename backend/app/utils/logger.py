"""
logger.py — Structured logging setup with file and console handlers.
Includes audit trail support for tracking user actions.
"""
import logging
import os
from datetime import datetime, timezone


def setup_logger(app):
    """Configure application logging with file + console handlers."""
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    log_file = app.config.get("LOG_FILE", "recruitment.log")

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    app.logger.setLevel(log_level)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    # Also configure root logger
    logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])
    app.logger.info("Logger initialized.")


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)


def audit_log(db, user_id: str, action: str, details: dict = None):
    """
    Write an immutable audit entry to the database.
    Used to track sensitive actions (login, resume upload, prediction).
    """
    try:
        db.audit_logs.insert_one({
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        })
    except Exception as e:
        logging.getLogger(__name__).error(f"Audit log failed: {e}")
