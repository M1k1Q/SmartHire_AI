"""
auth/routes.py — Authentication endpoints.

Routes:
  POST /api/auth/register  — Register a new user (hr or candidate)
  POST /api/auth/login     — Login and receive JWT token
  GET  /api/auth/me        — Get current authenticated user profile
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timezone

from ..extensions import mongo, bcrypt
from ..utils.validators import validate_email, validate_password, validate_required_fields, validate_role
from ..utils.exceptions import ValidationError, AuthenticationError
from ..utils.logger import audit_log

auth_bp = Blueprint("auth", __name__)


def _serialize_user(user: dict) -> dict:
    """Convert MongoDB user document to JSON-safe dict."""
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user.get("created_at", ""),
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new HR admin or Candidate account."""
    data = request.get_json(silent=True) or {}

    # Validate required fields
    validate_required_fields(data, ["name", "email", "password", "role"])
    validate_email(data["email"])
    validate_password(data["password"])
    validate_role(data["role"])

    db = mongo.db

    # Check for duplicate email
    if db.users.find_one({"email": data["email"].lower()}):
        raise ValidationError("An account with this email already exists.", 409)

    # Hash password
    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    user_doc = {
        "name": data["name"].strip(),
        "email": data["email"].lower().strip(),
        "password_hash": password_hash,
        "role": data["role"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    # Create JWT
    token = create_access_token(
        identity=str(result.inserted_id),
        additional_claims={"role": data["role"]}
    )

    current_app.logger.info(f"New user registered: {data['email']} as {data['role']}")
    audit_log(db, str(result.inserted_id), "register", {"email": data["email"], "role": data["role"]})

    return jsonify({
        "message": "Registration successful.",
        "token": token,
        "user": _serialize_user(user_doc)
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return a JWT access token."""
    data = request.get_json(silent=True) or {}
    validate_required_fields(data, ["email", "password"])

    db = mongo.db
    user = db.users.find_one({"email": data["email"].lower().strip()})

    if not user or not bcrypt.check_password_hash(user["password_hash"], data["password"]):
        raise AuthenticationError("Invalid email or password.")

    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={"role": user["role"]}
    )

    audit_log(db, str(user["_id"]), "login", {"email": data["email"]})
    current_app.logger.info(f"User logged in: {data['email']}")

    return jsonify({
        "message": "Login successful.",
        "token": token,
        "user": _serialize_user(user)
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return the currently authenticated user's profile."""
    identity = get_jwt_identity()
    db = mongo.db
    user = db.users.find_one({"_id": ObjectId(identity["id"])})

    if not user:
        raise AuthenticationError("User not found.")

    return jsonify({"user": _serialize_user(user)}), 200
