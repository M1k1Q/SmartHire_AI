"""
routes/analytics.py — Dashboard analytics endpoints for HR.

Routes:
  GET /api/analytics/dashboard       — Summary stats for HR dashboard
  GET /api/analytics/clusters/<job_id> — Cluster visualization data
  GET /api/analytics/metrics         — ML model evaluation metrics
  GET /api/analytics/bias-report     — Bias & fairness analysis
  POST /api/analytics/retrain        — Trigger model retraining
"""
from flask import Blueprint, jsonify, request, current_app
from bson import ObjectId

from ..extensions import mongo
from ..auth.middleware import require_role
from ..services.analytics_service import (
    get_dashboard_stats,
    get_cluster_data,
    get_model_metrics,
    get_bias_report,
)
from ..ml.model_registry import ModelRegistry
from ..utils.validators import validate_object_id
from ..utils.exceptions import NotFoundError

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@require_role("hr")
def dashboard():
    """Return aggregate stats: total jobs, applications, suitable predictions, cluster counts."""
    stats = get_dashboard_stats(mongo.db)
    return jsonify({"stats": stats}), 200


@analytics_bp.route("/clusters/<job_id>", methods=["GET"])
@require_role("hr")
def clusters(job_id):
    """
    Return 2D t-SNE/PCA cluster visualization data for a specific job's applicants.
    Response includes: points (x, y, cluster_id, candidate_name, rank_score, prediction).
    """
    validate_object_id(job_id, "job_id")
    job = mongo.db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise NotFoundError(f"Job {job_id} not found.")

    data = get_cluster_data(mongo.db, job_id)
    return jsonify({"job_id": job_id, "job_title": job["title"], "clusters": data}), 200


@analytics_bp.route("/metrics", methods=["GET"])
@require_role("hr")
def model_metrics():
    """Return the latest ML model evaluation metrics (accuracy, F1, ROC-AUC, etc.)."""
    metrics = get_model_metrics(mongo.db)
    return jsonify({"metrics": metrics}), 200


@analytics_bp.route("/bias-report", methods=["GET"])
@require_role("hr")
def bias_report():
    """Return the bias and fairness analysis report."""
    report = get_bias_report(mongo.db)
    return jsonify({"report": report}), 200


@analytics_bp.route("/retrain", methods=["POST"])
@require_role("hr")
def retrain():
    """
    Trigger model retraining using all applications currently in the database.
    This endpoint runs synchronously for demo purposes.
    In production this should be dispatched to a background task queue (Celery/RQ).
    """
    try:
        registry = ModelRegistry(current_app.config["MODELS_FOLDER"])
        from ..ml.pipeline import MLPipeline
        pipeline = MLPipeline(model_dir=current_app.config["MODELS_FOLDER"])
        result = pipeline.retrain(mongo.db)
        return jsonify({"message": "Model retrained successfully.", "result": result}), 200
    except Exception as e:
        current_app.logger.error(f"Retraining failed: {e}")
        return jsonify({"error": f"Retraining failed: {str(e)}"}), 500
