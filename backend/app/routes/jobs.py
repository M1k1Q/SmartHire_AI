"""
routes/jobs.py — Job posting CRUD endpoints (HR only for write operations).

Routes:
  POST   /api/jobs          — HR: Create job posting
  GET    /api/jobs          — All users: List active jobs
  GET    /api/jobs/<id>     — All users: Job details
  PUT    /api/jobs/<id>     — HR: Update job posting
  DELETE /api/jobs/<id>     — HR: Delete job posting
"""
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone

from ..extensions import mongo
from ..auth.middleware import require_auth, require_role, get_current_user_id
from ..models.job import create_job_doc, serialize_job
from ..utils.validators import validate_required_fields, validate_object_id
from ..utils.exceptions import NotFoundError, AuthorizationError

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("", methods=["POST"])
@require_role("hr")
def create_job():
    """HR creates a new job posting."""
    data = request.get_json(silent=True) or {}
    validate_required_fields(data, ["title", "description"])

    skills = data.get("required_skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]

    doc = create_job_doc(
        title=data["title"],
        description=data["description"],
        required_skills=skills,
        hr_id=get_current_user_id(),
    )

    result = mongo.db.jobs.insert_one(doc)
    doc["_id"] = result.inserted_id

    return jsonify({"message": "Job created.", "job": serialize_job(doc)}), 201


@jobs_bp.route("", methods=["GET"])
@require_auth
def list_jobs():
    """List all active job postings. Supports ?q= text search."""
    query_str = request.args.get("q", "").strip()
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 20))

    filter_q = {"is_active": True}
    if query_str:
        filter_q["$or"] = [
            {"title": {"$regex": query_str, "$options": "i"}},
            {"description": {"$regex": query_str, "$options": "i"}},
        ]

    jobs_cursor = mongo.db.jobs.find(filter_q).sort("created_at", -1).skip(skip).limit(limit)
    total = mongo.db.jobs.count_documents(filter_q)
    jobs = [serialize_job(j) for j in jobs_cursor]

    return jsonify({"jobs": jobs, "total": total, "skip": skip, "limit": limit}), 200


@jobs_bp.route("/<job_id>", methods=["GET"])
@require_auth
def get_job(job_id):
    """Get a single job posting by ID."""
    validate_object_id(job_id, "job_id")
    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")
    return jsonify({"job": serialize_job(job)}), 200


@jobs_bp.route("/<job_id>", methods=["PUT"])
@require_role("hr")
def update_job(job_id):
    """HR updates a job posting (only their own)."""
    validate_object_id(job_id, "job_id")
    data = request.get_json(silent=True) or {}

    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")
    if job["hr_id"] != get_current_user_id():
        raise AuthorizationError("You can only edit your own job postings.")

    update_fields = {}
    for field in ["title", "description", "required_skills", "is_active"]:
        if field in data:
            update_fields[field] = data[field]
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": update_fields})
    updated = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})

    return jsonify({"message": "Job updated.", "job": serialize_job(updated)}), 200


@jobs_bp.route("/<job_id>", methods=["DELETE"])
@require_role("hr")
def delete_job(job_id):
    """HR soft-deletes a job posting."""
    validate_object_id(job_id, "job_id")
    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")
    if job["hr_id"] != get_current_user_id():
        raise AuthorizationError("You can only delete your own job postings.")

    mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": {"is_active": False}})
    return jsonify({"message": "Job deleted."}), 200
