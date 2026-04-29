"""
validators.py — Input validation helpers for API endpoints.
"""
import re
from .exceptions import ValidationError

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ALLOWED_EXTENSIONS = {"pdf", "docx"}


def validate_email(email: str):
    if not email or not EMAIL_REGEX.match(email):
        raise ValidationError("Invalid email address.")


def validate_password(password: str):
    if not password or len(password) < 6:
        raise ValidationError("Password must be at least 6 characters.")


def validate_required_fields(data: dict, fields: list):
    """Ensure all required fields are present and non-empty."""
    for field in fields:
        if not data.get(field):
            raise ValidationError(f"Field '{field}' is required.")


def validate_role(role: str):
    allowed = {"hr", "candidate"}
    if role not in allowed:
        raise ValidationError(f"Role must be one of: {', '.join(allowed)}")


def validate_file_extension(filename: str):
    if "." not in filename:
        raise ValidationError("File has no extension.")
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Only PDF and DOCX files are allowed. Got: .{ext}")


def validate_object_id(oid: str, field_name: str = "id"):
    """Validate a MongoDB ObjectId string."""
    from bson import ObjectId
    try:
        ObjectId(oid)
    except Exception:
        raise ValidationError(f"Invalid {field_name}: must be a valid ObjectId.")
