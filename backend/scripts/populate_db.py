"""
scripts/populate_db.py
Stand-alone script to populate the recruitment database with synthetic data.
Run using: python -m scripts.populate_db
"""

import os
import sys
import random
from datetime import datetime, timezone
from bson import ObjectId

# Ensure the backend directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import mongo, bcrypt
from app.models.user import create_user_doc
from app.models.job import create_job_doc
from app.models.application import create_application_doc
from app.ml.data.generate_synthetic_data import generate_synthetic_dataset
from app.services.resume_service import process_resume_for_application

def populate():
    app = create_app()
    with app.app_context():
        db = mongo.db
        print("--- Cleaning existing data ---")
        db.users.delete_many({})
        db.jobs.delete_many({})
        db.applications.delete_many({})
        db.audit_logs.delete_many({})
        db.model_metrics.delete_many({})
        
        # 1. Create HR Manager
        hr_email = "hr@example.com"
        hr_pass = "password123"
        hr_pass_hash = bcrypt.generate_password_hash(hr_pass).decode('utf-8')
        hr_doc = create_user_doc("Sarah Recruiter", hr_email, hr_pass_hash, "hr")
        result = db.users.insert_one(hr_doc)
        hr_id = str(result.inserted_id)
        print(f"Created HR User: {hr_email} (ID: {hr_id})")

        # 2. Create Job Postings
        jobs_data = [
            {
                "title": "Senior AI Architect",
                "description": "Looking for a specialist in NLP and Transformers to lead our recruitment automation project.",
                "skills": ["Python", "Machine Learning", "NLP", "PyTorch", "Transformers", "SQL"]
            },
            {
                "title": "Full Stack Developer (Flask/React)",
                "description": "Join our team building modern web applications with a focus on AI integration.",
                "skills": ["Python", "Flask", "React", "JavaScript", "Docker", "REST APIs", "SQL"]
            }
        ]
        
        job_ids = []
        for jd in jobs_data:
            job_doc = create_job_doc(jd["title"], jd["description"], jd["skills"], hr_id)
            res = db.jobs.insert_one(job_doc)
            job_ids.append(str(res.inserted_id))
            print(f"Created Job: {jd['title']} (ID: {res.inserted_id})")

        # 3. Generate Candidates and Applications
        print("--- Generating synthetic candidates (20) ---")
        docs, labels, metadata = generate_synthetic_dataset(n_samples=20)
        
        resumes_dir = os.path.join(app.config["UPLOAD_FOLDER"], "resumes")
        os.makedirs(resumes_dir, exist_ok=True)

        for i in range(20):
            # Create Candidate User
            cand_email = f"candidate{i}@example.com"
            cand_pass_hash = bcrypt.generate_password_hash("password123").decode('utf-8')
            cand_doc = create_user_doc(f"Candidate {i}", cand_email, cand_pass_hash, "candidate")
            c_res = db.users.insert_one(cand_doc)
            candidate_id = str(c_res.inserted_id)

            # Assign to a random job
            target_job_id = random.choice(job_ids)
            target_job = db.jobs.find_one({"_id": ObjectId(target_job_id)})

            # Save resume text to file
            resume_filename = f"resume_cand_{i}.txt"
            resume_path = os.path.join(resumes_dir, resume_filename)
            with open(resume_path, "w", encoding="utf-8") as f:
                f.write(docs[i])

            # Create Application
            app_doc = create_application_doc(candidate_id, target_job_id, f"resumes/{resume_filename}")
            a_res = db.applications.insert_one(app_doc)
            application_id = str(a_res.inserted_id)

            # Process through ML pipeline (simulates "submission")
            print(f"[{i+1}/20] Processing application for {cand_email} -> {target_job['title']}...")
            try:
                process_resume_for_application(
                    resume_path=resume_path,
                    job_description=target_job["description"],
                    job_skills=target_job["required_skills"],
                    application_id=application_id,
                    db=db
                )
            except Exception as e:
                print(f"Error processing {cand_email}: {e}")

        print("\n--- Population Complete! ---")
        print(f"HR Login: {hr_email} / {hr_pass}")
        print(f"Created {len(job_ids)} jobs and 20 candidate evaluations.")

if __name__ == "__main__":
    populate()
