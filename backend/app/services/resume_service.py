"""
services/resume_service.py
Coordinates the resume upload process and ML pipeline execution.

Called by the applications route when a candidate submits a resume.
Updates the application document in MongoDB with ML results.
"""
import logging
from typing import Dict

from ..ml.pipeline import MLPipeline
from ..utils.exceptions import MLPipelineError

logger = logging.getLogger(__name__)

# Module-level pipeline instance (cached per process)
_pipeline_instance: MLPipeline = None


def _get_pipeline(model_dir: str) -> MLPipeline:
    """Return a cached MLPipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MLPipeline(model_dir=model_dir)
    return _pipeline_instance


def process_resume_for_application(
    resume_path: str,
    job_description: str,
    job_skills: list,
    application_id: str,
    db,
    model_dir: str = "ml_models",
) -> Dict:
    """
    Run the full ML pipeline on an uploaded resume and persist results to MongoDB.

    Args:
        resume_path:     Absolute path to the uploaded resume file.
        job_description: Job posting description text.
        job_skills:      List of required skills from the job posting.
        application_id:  MongoDB ObjectId string of the application document.
        db:              PyMongo database instance.
        model_dir:       Path to the models directory.

    Returns:
        dict with ML results (prediction, rank_score, skills, etc.)

    Raises:
        MLPipelineError: If pipeline processing fails.
    """
    try:
        from flask import current_app
        model_dir = current_app.config.get("MODELS_FOLDER", model_dir)
    except RuntimeError:
        pass  # Not in app context (e.g., during testing)

    try:
        pipeline = _get_pipeline(model_dir)
        results = pipeline.process(
            resume_path=resume_path,
            job_description=job_description,
            job_skills=job_skills,
        )
    except Exception as e:
        logger.error(f"Pipeline failed for application {application_id}: {e}")
        raise MLPipelineError(f"Resume processing failed: {str(e)}")

    # Update the application document with ML results
    from bson import ObjectId
    update_data = {
        "resume_text": results.get("resume_text", ""),
        "extracted_skills": results.get("extracted_skills", []),
        "experience_years": results.get("experience_years", 0.0),
        "rank_score": results.get("rank_score", 0.0),
        "prediction": results.get("prediction", "Not Suitable"),
        "prediction_prob": results.get("prediction_prob", 0.0),
    }

    try:
        db.applications.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": update_data}
        )
        logger.info(f"Application {application_id} updated: prediction={update_data['prediction']}, score={update_data['rank_score']}")
    except Exception as e:
        logger.error(f"DB update failed for application {application_id}: {e}")

    return results
