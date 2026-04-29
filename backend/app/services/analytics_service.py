"""
services/analytics_service.py
Generates aggregated analytics for the HR dashboard.

Functions:
  - get_dashboard_stats()    — Summary numbers (jobs, apps, predictions)
  - get_cluster_data()       — Per-job cluster visualization data
  - get_model_metrics()      — Latest ML evaluation metrics from DB
  - get_bias_report()        — Fairness analysis on all predictions
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def get_dashboard_stats(db) -> Dict:
    """
    Aggregate summary statistics for the HR dashboard.

    Returns:
        dict with: total_jobs, total_applications, suitable_count,
                   not_suitable_count, pending_count, shortlisted_count,
                   recent_applications (last 5)
    """
    try:
        total_jobs = db.jobs.count_documents({"is_active": True})
        total_applications = db.applications.count_documents({})
        suitable = db.applications.count_documents({"prediction": "Suitable"})
        not_suitable = db.applications.count_documents({"prediction": "Not Suitable"})
        pending = db.applications.count_documents({"prediction": "Pending"})
        shortlisted = db.applications.count_documents({"status": "shortlisted"})

        # Avg rank score
        pipeline = [
            {"$match": {"rank_score": {"$gt": 0}}},
            {"$group": {"_id": None, "avg_score": {"$avg": "$rank_score"}}},
        ]
        avg_result = list(db.applications.aggregate(pipeline))
        avg_score = round(avg_result[0]["avg_score"], 4) if avg_result else 0.0

        # Recent 5 applications
        recent_cursor = db.applications.find(
            {}, {"candidate_id": 1, "job_id": 1, "prediction": 1, "rank_score": 1, "applied_at": 1}
        ).sort("applied_at", -1).limit(5)

        recent = []
        for app in recent_cursor:
            # Enrich with candidate name + job title
            user = db.users.find_one({"_id": __import__("bson").ObjectId(app["candidate_id"])}, {"name": 1})
            job = db.jobs.find_one({"_id": __import__("bson").ObjectId(app["job_id"])}, {"title": 1})
            recent.append({
                "id": str(app["_id"]),
                "candidate_name": user["name"] if user else "Unknown",
                "job_title": job["title"] if job else "Unknown",
                "prediction": app.get("prediction", "Pending"),
                "rank_score": round(app.get("rank_score", 0), 4),
                "applied_at": app.get("applied_at", ""),
            })

        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "suitable_count": suitable,
            "not_suitable_count": not_suitable,
            "pending_count": pending,
            "shortlisted_count": shortlisted,
            "avg_rank_score": avg_score,
            "recent_applications": recent,
        }
    except Exception as e:
        logger.error(f"Dashboard stats failed: {e}")
        return {"error": str(e)}


def get_cluster_data(db, job_id: str) -> Dict:
    """
    Produce cluster visualization data for all applicants of a specific job.
    Runs the clustering pipeline and returns 2D points + metadata.
    """
    try:
        from flask import current_app
        model_dir = current_app.config.get("MODELS_FOLDER", "ml_models")
    except RuntimeError:
        model_dir = "ml_models"

    try:
        apps_cursor = db.applications.find(
            {"job_id": job_id},
            {"_id": 1, "resume_text": 1, "rank_score": 1, "prediction": 1,
             "candidate_id": 1, "extracted_skills": 1}
        )
        applications = []
        for app in apps_cursor:
            user = db.users.find_one(
                {"_id": __import__("bson").ObjectId(app["candidate_id"])}, {"name": 1}
            )
            applications.append({
                "id": str(app["_id"]),
                "resume_text": app.get("resume_text", ""),
                "rank_score": app.get("rank_score", 0.0),
                "prediction": app.get("prediction", "Pending"),
                "skills": app.get("extracted_skills", []),
                "candidate_name": user["name"] if user else "Unknown",
            })

        if not applications:
            return {"points": [], "n_clusters": 0, "silhouette_score": 0}

        if len(applications) < 2:
            return {
                "points": [{"id": applications[0]["id"], "cluster_id": 0, "x": 0, "y": 0,
                             "rank_score": applications[0]["rank_score"],
                             "prediction": applications[0]["prediction"],
                             "candidate_name": applications[0]["candidate_name"]}],
                "n_clusters": 1,
                "silhouette_score": 0,
            }

        from ..ml.pipeline import MLPipeline
        pipeline = MLPipeline(model_dir=model_dir)
        cluster_result = pipeline.cluster_job_applicants(applications)

        # Enrich points with metadata
        app_lookup = {a["id"]: a for a in applications}
        enriched_points = []
        for point in cluster_result.get("points", []):
            app_data = app_lookup.get(point["id"], {})
            enriched_points.append({
                **point,
                "rank_score": app_data.get("rank_score", 0.0),
                "prediction": app_data.get("prediction", "Pending"),
                "candidate_name": app_data.get("candidate_name", "Unknown"),
                "skills": app_data.get("skills", []),
            })

        # Update cluster_id in DB for each application
        for point in enriched_points:
            db.applications.update_one(
                {"_id": __import__("bson").ObjectId(point["id"])},
                {"$set": {"cluster_id": point["cluster_id"]}}
            )

        return {
            "points": enriched_points,
            "n_clusters": cluster_result.get("n_clusters", 1),
            "silhouette_score": cluster_result.get("silhouette_score", 0.0),
            "elbow": cluster_result.get("elbow", {}),
        }

    except Exception as e:
        logger.error(f"Cluster data generation failed: {e}")
        return {"error": str(e), "points": []}


def get_model_metrics(db) -> Dict:
    """Return the latest model evaluation metrics stored in MongoDB."""
    try:
        latest = db.model_metrics.find_one({}, sort=[("trained_at", -1)])
        if not latest:
            return {
                "message": "No training run found. Submit applications and retrain.",
                "metrics": None,
            }
        del latest["_id"]
        return latest
    except Exception as e:
        logger.error(f"get_model_metrics failed: {e}")
        return {"error": str(e)}


def get_bias_report(db) -> Dict:
    """Run bias detection on all current application predictions."""
    try:
        from ..ml.evaluation.explainability import detect_bias

        apps = list(db.applications.find(
            {"prediction": {"$in": ["Suitable", "Not Suitable"]}},
            {"prediction": 1, "rank_score": 1}
        ))
        predictions = [
            {"prediction": a.get("prediction"), "rank_score": a.get("rank_score", 0.0)}
            for a in apps
        ]
        return detect_bias(predictions)
    except Exception as e:
        logger.error(f"Bias report failed: {e}")
        return {"error": str(e)}
