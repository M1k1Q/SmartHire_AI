"""
scripts/candidate_eval_test.py
Per-candidate evaluation test:
  - Candidate name & email
  - Job they applied to
  - Parsed skills from resume
  - Parsed experience years
  - Skill overlap with job requirements (%)
  - Expected outcome (rule-based: score >= 0.40 = Suitable)
  - Actual ML prediction
  - Match Score (rank_score)
  - Confidence %
  - PASS/FAIL (expected == actual)
"""
import os, sys, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import mongo
from bson import ObjectId

def run_candidate_eval():
    app = create_app()
    with app.app_context():
        db = mongo.db
        apps = list(db.applications.find(
            {"rank_score": {"$exists": True}, "prediction": {"$exists": True}},
        ).sort("job_id", 1))

        rows = []
        passed = 0
        failed = 0

        for a in apps:
            # Enrich with user info
            user = db.users.find_one({"_id": ObjectId(a["candidate_id"])}, {"name": 1, "email": 1})
            job  = db.jobs.find_one({"_id": ObjectId(a["job_id"])}, {"title": 1, "required_skills": 1})

            if not user or not job:
                continue

            required_skills   = set(s.lower() for s in job.get("required_skills", []))
            extracted_skills  = set(s.lower() for s in a.get("extracted_skills", []))
            experience_years  = a.get("experience_years", 0.0)
            rank_score        = round(a.get("rank_score", 0.0), 4)
            actual_prediction = a.get("prediction", "Unknown")
            confidence        = round(a.get("prediction_prob", 0.0) * 100, 1)

            # Compute skill overlap
            matched_skills = extracted_skills & required_skills
            overlap_pct = round(len(matched_skills) / len(required_skills) * 100, 1) if required_skills else 0.0

            # Determine expected outcome (deterministic rule, mirrors pipeline logic)
            if rank_score >= 0.40:
                expected = "Suitable"
            elif rank_score < 0.20:
                expected = "Not Suitable"
            else:
                expected = "Borderline"  # 0.20 – 0.40 grey zone

            # PASS if actual matches expected (for borderline, actual can be either)
            if expected == "Borderline":
                test_result = "N/A (Borderline)"
            elif actual_prediction == expected:
                test_result = "PASS ✅"
                passed += 1
            else:
                test_result = "FAIL ❌"
                failed += 1

            rows.append({
                "candidate":        user.get("name", "Unknown"),
                "email":            user.get("email", ""),
                "job":              job.get("title", "Unknown"),
                "required_skills":  sorted(list(required_skills)),
                "extracted_skills": sorted(list(extracted_skills)),
                "matched_skills":   sorted(list(matched_skills)),
                "overlap_pct":      overlap_pct,
                "experience_years": experience_years,
                "rank_score":       rank_score,
                "confidence_pct":   confidence,
                "expected":         expected,
                "actual":           actual_prediction,
                "result":           test_result,
            })

        # Save full JSON
        out_path = os.path.join(os.path.dirname(__file__), "candidate_eval_results.json")
        with open(out_path, "w") as f:
            json.dump({"rows": rows, "summary": {
                "total": len(rows),
                "passed": passed,
                "failed": failed,
                "borderline": len([r for r in rows if "Borderline" in r["result"]]),
                "pass_rate": round(passed / max(passed + failed, 1) * 100, 1)
            }}, f, indent=2)

        print(f"\nTotal: {len(rows)} | PASS: {passed} | FAIL: {failed} | Pass Rate: {round(passed/max(passed+failed,1)*100,1)}%")
        print(f"Results saved to {out_path}")

if __name__ == "__main__":
    run_candidate_eval()
