"""
models/job.py — MongoDB Job Posting document helper.

Schema:
    _id              : ObjectId (auto)
    title            : str
    description      : str
    required_skills  : list[str]
    hr_id            : str (ObjectId ref -> users)
    is_active        : bool
    created_at       : ISO datetime string
"""
from datetime import datetime, timezone


def create_job_doc(title: str, description: str, required_skills: list, hr_id: str) -> dict:
    """Build a new job document ready for MongoDB insertion."""
    return {
        "title": title.strip(),
        "description": description.strip(),
        "required_skills": [s.strip().lower() for s in required_skills if s.strip()],
        "hr_id": hr_id,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def serialize_job(job: dict) -> dict:
    """Convert a MongoDB job document to a JSON-safe dict."""
    return {
        "id": str(job["_id"]),
        "title": job.get("title", ""),
        "description": job.get("description", ""),
        "required_skills": job.get("required_skills", []),
        "hr_id": job.get("hr_id", ""),
        "is_active": job.get("is_active", True),
        "created_at": job.get("created_at", ""),
    }
