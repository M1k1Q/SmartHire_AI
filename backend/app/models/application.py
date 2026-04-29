"""
models/application.py — MongoDB Application document helper.

Schema:
    _id            : ObjectId (auto)
    candidate_id   : str  (ObjectId ref -> users)
    job_id         : str  (ObjectId ref -> jobs)
    resume_path    : str  (relative path to uploaded file)
    resume_text    : str  (parsed plain text)
    extracted_skills: list[str]
    experience_years: float
    rank_score     : float  (cosine similarity 0-1)
    prediction     : str   ('Suitable' | 'Not Suitable')
    prediction_prob: float (confidence 0-1)
    cluster_id     : int
    status         : str  ('pending' | 'reviewed' | 'shortlisted' | 'rejected')
    applied_at     : ISO datetime string
"""
from datetime import datetime, timezone


def create_application_doc(candidate_id: str, job_id: str, resume_path: str) -> dict:
    """Build a new application document ready for MongoDB insertion."""
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "resume_path": resume_path,
        "resume_text": "",
        "extracted_skills": [],
        "experience_years": 0.0,
        "rank_score": 0.0,
        "prediction": "Pending",
        "prediction_prob": 0.0,
        "cluster_id": -1,
        "status": "pending",
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }


def serialize_application(app_doc: dict, include_resume_text: bool = False) -> dict:
    """Convert a MongoDB application document to a JSON-safe dict."""
    result = {
        "id": str(app_doc["_id"]),
        "candidate_id": app_doc.get("candidate_id", ""),
        "job_id": app_doc.get("job_id", ""),
        "resume_path": app_doc.get("resume_path", ""),
        "extracted_skills": app_doc.get("extracted_skills", []),
        "experience_years": app_doc.get("experience_years", 0.0),
        "rank_score": round(app_doc.get("rank_score", 0.0), 4),
        "prediction": app_doc.get("prediction", "Pending"),
        "prediction_prob": round(app_doc.get("prediction_prob", 0.0), 4),
        "cluster_id": app_doc.get("cluster_id", -1),
        "status": app_doc.get("status", "pending"),
        "applied_at": app_doc.get("applied_at", ""),
    }
    if include_resume_text:
        result["resume_text"] = app_doc.get("resume_text", "")
    return result
