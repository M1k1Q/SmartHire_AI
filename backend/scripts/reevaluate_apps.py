"""
scripts/reevaluate_apps.py
Recalculates scores and suitability for all existing applications using updated weights/thresholds.
"""

import os
import sys
from bson import ObjectId

# Ensure the backend directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import mongo
from app.services.resume_service import process_resume_for_application

def reevaluate():
    app = create_app()
    with app.app_context():
        db = mongo.db
        apps = list(db.applications.find({}))
        print(f"--- Re-evaluating {len(apps)} applications ---")
        
        for i, app_doc in enumerate(apps):
            job = db.jobs.find_one({"_id": ObjectId(app_doc["job_id"])})
            if not job:
                print(f"Skipping app {app_doc['_id']}: Job not found.")
                continue
                
            resume_path = os.path.join(app.config["UPLOAD_FOLDER"], app_doc["resume_path"])
            
            print(f"[{i+1}/{len(apps)}] Re-processing Application {app_doc['_id']}...")
            try:
                process_resume_for_application(
                    resume_path=resume_path,
                    job_description=job["description"],
                    job_skills=job.get("required_skills", []),
                    application_id=str(app_doc["_id"]),
                    db=db
                )
            except Exception as e:
                print(f"Error: {e}")

        print("\n--- Re-evaluation Complete! ---")

if __name__ == "__main__":
    reevaluate()
