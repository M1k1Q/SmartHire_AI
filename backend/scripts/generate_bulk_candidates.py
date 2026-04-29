"""
scripts/generate_bulk_candidates.py
Generates 5 synthetic candidates for each active job posting.
Usage: python -m scripts.generate_bulk_candidates
"""

import os
import sys
import random
import uuid
from bson import ObjectId
from werkzeug.security import generate_password_hash

# Ensure the backend directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import mongo
from app.ml.data.generate_synthetic_data import SKILL_POOL, _generate_resume
from app.services.resume_service import process_resume_for_application

def generate_bulk():
    app = create_app()
    with app.app_context():
        db = mongo.db
        jobs = list(db.jobs.find({"is_active": True}))
        print(f"--- Found {len(jobs)} active jobs ---")

        all_skills = SKILL_POOL["tech"] + SKILL_POOL["ml"] + SKILL_POOL["data"] + SKILL_POOL["soft"]
        
        for job in jobs:
            job_id = str(job["_id"])
            job_title = job["title"]
            required_skills = set(job.get("required_skills", []))
            print(f"\nProcessing Job: {job_title} ({job_id})")

            for i in range(5):
                # 3 suitable (60% match+), 2 average
                is_suitable = i < 3
                
                n_skills = random.randint(8, 15)
                if is_suitable and required_skills:
                    # Match most required skills
                    match_count = min(len(required_skills), random.randint(3, 6))
                    matched = random.sample(list(required_skills), match_count)
                    padding = random.sample(all_skills, max(0, n_skills - len(matched)))
                    candidate_skills = list(set(matched + padding))
                    experience_years = random.randint(4, 12)
                else:
                    candidate_skills = random.sample(all_skills, n_skills)
                    experience_years = random.randint(0, 5)

                candidate_name = f"{job_title.split()[0]} Expert {uuid.uuid4().hex[:4].upper()}"
                email = f"candidate_{uuid.uuid4().hex[:6]}@example.com"
                
                # Create User
                user_id = db.users.insert_one({
                    "name": candidate_name,
                    "email": email,
                    "password_hash": generate_password_hash("password123"),
                    "role": "candidate"
                }).inserted_id

                # Generate Resume Text
                resume_text = _generate_resume(candidate_skills, experience_years, i, name_hint=candidate_name)
                
                # Save Resume File
                filename = f"{user_id}_{job_id}_resume.txt"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(resume_text)

                # Create Application
                app_doc = {
                    "candidate_id": str(user_id),
                    "job_id": job_id,
                    "resume_path": filename,
                    "status": "pending",
                    "applied_at": "2026-04-18T19:30:00Z", # Demo timestamp
                    "resume_text": resume_text,
                    "extracted_skills": candidate_skills,
                    "experience_years": float(experience_years)
                }
                result = db.applications.insert_one(app_doc)
                application_id = str(result.inserted_id)

                # Process with ML
                print(f"  - Generated {candidate_name} ({email}) | Suitable: {is_suitable}")
                try:
                    process_resume_for_application(
                        resume_path=filepath,
                        job_description=job["description"],
                        job_skills=list(required_skills),
                        application_id=application_id,
                        db=db
                    )
                except Exception as e:
                    print(f"    ML Error: {e}")

        print("\n--- Bulk Generation Complete! ---")

if __name__ == "__main__":
    generate_bulk()
