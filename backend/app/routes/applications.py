"""
routes/applications.py — Resume upload, application submission, and ranking endpoints.

Routes:
  POST  /api/applications               — Candidate: apply to a job (multipart upload)
  GET   /api/applications/my            — Candidate: view own applications
  GET   /api/applications/job/<job_id>  — HR: view ranked candidates for a job
  PUT   /api/applications/<id>/status   — HR: update application status
  GET   /api/applications/<id>          — HR/Candidate: view single application detail
"""
import os
from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from werkzeug.utils import secure_filename

from ..extensions import mongo
from ..auth.middleware import require_auth, require_role, get_current_user_id, get_current_role
from ..models.application import create_application_doc, serialize_application
from ..utils.validators import validate_required_fields, validate_object_id, validate_file_extension
from ..utils.exceptions import NotFoundError, AuthorizationError, ValidationError
from ..utils.logger import audit_log
from ..services.resume_service import process_resume_for_application

applications_bp = Blueprint("applications", __name__)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf", "docx"}


@applications_bp.route("", methods=["POST"])
@require_role("candidate")
def apply_to_job():
    """
    Candidate submits a job application with resume file.
    Triggers the full ML pipeline (parse → NLP → rank → classify → cluster).
    """
    # Validate form fields
    job_id = request.form.get("job_id", "").strip()
    if not job_id:
        raise ValidationError("job_id is required.")
    validate_object_id(job_id, "job_id")

    # Validate file
    if "resume" not in request.files:
        raise ValidationError("Resume file is required.")
    file = request.files["resume"]
    if file.filename == "":
        raise ValidationError("No file selected.")
    validate_file_extension(file.filename)

    # Check job exists
    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id), "is_active": True})
    if not job:
        raise NotFoundError(f"Job {job_id} not found or is no longer active.")

    candidate_id = get_current_user_id()

    # Prevent duplicate application
    existing = mongo.db.applications.find_one({
        "candidate_id": candidate_id,
        "job_id": job_id,
    })
    if existing:
        raise ValidationError("You have already applied to this job.", 409)

    # Save resume file
    filename = secure_filename(file.filename)
    unique_name = f"{candidate_id}_{job_id}_{filename}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(upload_path)

    # Create initial application document
    app_doc = create_application_doc(candidate_id, job_id, unique_name)
    result = mongo.db.applications.insert_one(app_doc)
    app_id = str(result.inserted_id)

    # Process with ML pipeline (parse, rank, classify, cluster)
    try:
        ml_results = process_resume_for_application(
            resume_path=upload_path,
            job_description=job["description"],
            job_skills=job.get("required_skills", []),
            application_id=app_id,
            db=mongo.db,
        )
        audit_log(mongo.db, candidate_id, "apply_job", {
            "job_id": job_id, "application_id": app_id,
            "prediction": ml_results.get("prediction"),
            "rank_score": ml_results.get("rank_score"),
        })
    except Exception as e:
        current_app.logger.error(f"ML pipeline failed for application {app_id}: {e}")
        # Application is still saved even if ML fails
        audit_log(mongo.db, candidate_id, "apply_job_ml_failed", {"job_id": job_id, "error": str(e)})

    final_app = mongo.db.applications.find_one({"_id": result.inserted_id})
    return jsonify({
        "message": "Application submitted successfully.",
        "application": serialize_application(final_app)
    }), 201


@applications_bp.route("/my", methods=["GET"])
@require_role("candidate")
def my_applications():
    """Candidate views their own applications with job details."""
    candidate_id = get_current_user_id()
    apps_cursor = mongo.db.applications.find(
        {"candidate_id": candidate_id}
    ).sort("applied_at", -1)

    results = []
    for app_doc in apps_cursor:
        serialized = serialize_application(app_doc)
        # Enrich with job title
        job = mongo.db.jobs.find_one({"_id": ObjectId(app_doc["job_id"])}, {"title": 1})
        serialized["job_title"] = job["title"] if job else "Unknown"
        results.append(serialized)

    return jsonify({"applications": results, "total": len(results)}), 200


@applications_bp.route("/job/<job_id>", methods=["GET"])
@require_role("hr")
def ranked_candidates(job_id):
    """HR views all applications for a job, sorted by rank score (descending)."""
    validate_object_id(job_id, "job_id")

    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")

    apps_cursor = mongo.db.applications.find(
        {"job_id": job_id}
    ).sort("rank_score", -1)

    results = []
    for i, app_doc in enumerate(apps_cursor):
        serialized = serialize_application(app_doc)
        serialized["rank"] = i + 1
        # Enrich with candidate name/email
        candidate = mongo.db.users.find_one(
            {"_id": ObjectId(app_doc["candidate_id"])},
            {"name": 1, "email": 1}
        )
        serialized["candidate_name"] = candidate["name"] if candidate else "Unknown"
        serialized["candidate_email"] = candidate["email"] if candidate else ""
        results.append(serialized)

    return jsonify({
        "job": {"id": job_id, "title": job["title"]},
        "applications": results,
        "total": len(results)
    }), 200


@applications_bp.route("/<app_id>/status", methods=["PUT"])
@require_role("hr")
def update_status(app_id):
    """HR updates the status of an application."""
    validate_object_id(app_id, "app_id")
    data = request.get_json(silent=True) or {}
    validate_required_fields(data, ["status"])

    allowed_statuses = {"pending", "reviewed", "shortlisted", "rejected"}
    if data["status"] not in allowed_statuses:
        raise ValidationError(f"Status must be one of: {', '.join(allowed_statuses)}")

    app_doc = mongo.db.applications.find_one({"_id": ObjectId(app_id)})
    if not app_doc:
        raise NotFoundError(f"Application {app_id} not found.")

    mongo.db.applications.update_one(
        {"_id": ObjectId(app_id)},
        {"$set": {"status": data["status"]}}
    )
    return jsonify({"message": f"Status updated to '{data['status']}'."}), 200


@applications_bp.route("/<app_id>", methods=["GET"])
@require_auth
def get_application(app_id):
    """View a single application. HR can see any; candidates only their own."""
    validate_object_id(app_id, "app_id")
    app_doc = mongo.db.applications.find_one({"_id": ObjectId(app_id)})
    if not app_doc:
        raise NotFoundError(f"Application {app_id} not found.")

    role = get_current_role()
    uid = get_current_user_id()
    if role == "candidate" and app_doc["candidate_id"] != uid:
        raise AuthorizationError("You can only view your own applications.")

    return jsonify({"application": serialize_application(app_doc, include_resume_text=True)}), 200

@applications_bp.route("/<app_id>", methods=["DELETE"])
@require_role("hr")
def delete_application(app_id):
    """HR deletes an application to clear up the screen."""
    validate_object_id(app_id, "app_id")
    app_doc = mongo.db.applications.find_one({"_id": ObjectId(app_id)})
    if not app_doc:
        raise NotFoundError(f"Application {app_id} not found.")

    mongo.db.applications.delete_one({"_id": ObjectId(app_id)})
    return jsonify({"message": "Application removed successfully."}), 200
