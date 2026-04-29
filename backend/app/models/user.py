"""
models/user.py — MongoDB User document helper.

Schema:
    _id          : ObjectId (auto)
    name         : str
    email        : str (unique, lowercase)
    password_hash: str (bcrypt)
    role         : str  ('hr' | 'candidate')
    created_at   : ISO datetime string
"""
from datetime import datetime, timezone


def create_user_doc(name: str, email: str, password_hash: str, role: str) -> dict:
    """Build a new user document ready for MongoDB insertion."""
    return {
        "name": name.strip(),
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def serialize_user(user: dict) -> dict:
    """Convert a MongoDB user document to a JSON-safe dict (omits password)."""
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", ""),
        "created_at": user.get("created_at", ""),
    }
