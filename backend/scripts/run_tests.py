"""
scripts/run_tests.py
Comprehensive test suite for SmartHire AI — evaluates:
  1. Global Model Training (all 4 classifiers compared)
  2. Candidate Evaluation (rank scores, prediction accuracy)
  3. Skill Clustering (per-job silhouette scores, optimal K)
Outputs results as JSON for markdown table generation.
"""
import os, sys, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import mongo
import numpy as np

def run_tests():
    app = create_app()
    with app.app_context():
        db = mongo.db
        results = {}

        # ----------------------------------------------------------------
        # TEST 1: Global Model Training (compare all classifiers)
        # ----------------------------------------------------------------
        print("\n[1/3] Running Global Model Training tests...")
        from app.ml.preprocessing.nlp_pipeline import preprocess_text, build_tfidf_vectorizer
        from app.ml.data.generate_synthetic_data import generate_synthetic_dataset
        from app.ml.training.classifier import compare_all_models
        from app.ml.evaluation.metrics import split_data

        docs, labels, meta = generate_synthetic_dataset(n_samples=300)
        processed = [preprocess_text(d) for d in docs]
        vectorizer, X = build_tfidf_vectorizer(processed)
        y = np.array(labels)
        X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.25)

        print(f"  Dataset: {len(docs)} samples | Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
        print(f"  Class balance: {sum(labels)} Suitable / {len(labels)-sum(labels)} Not Suitable")

        comparison, best_clf = compare_all_models(X_train, y_train, X_test, y_test)
        results["model_training"] = {
            "n_train": int(X_train.shape[0]),
            "n_test": int(X_test.shape[0]),
            "n_features": int(X_train.shape[1]),
            "class_suitable": int(sum(labels)),
            "class_not_suitable": int(len(labels) - sum(labels)),
            "comparison": {
                k: v for k, v in comparison.items() if k != "best_model"
            },
            "best_model": comparison.get("best_model", "random_forest")
        }
        print(f"  Best model: {comparison.get('best_model')}")

        # ----------------------------------------------------------------
        # TEST 2: Candidate Evaluation (from real DB applications)
        # ----------------------------------------------------------------
        print("\n[2/3] Running Candidate Evaluation tests...")
        apps = list(db.applications.find(
            {"rank_score": {"$exists": True}, "prediction": {"$exists": True}},
            {"candidate_id": 1, "job_id": 1, "rank_score": 1, "prediction": 1,
             "extracted_skills": 1, "experience_years": 1, "prediction_prob": 1}
        ).sort("rank_score", -1))

        if apps:
            suitable = [a for a in apps if a.get("prediction") == "Suitable"]
            not_suitable = [a for a in apps if a.get("prediction") == "Not Suitable"]
            scores = [a.get("rank_score", 0) for a in apps]
            probs  = [a.get("prediction_prob", 0) for a in apps if a.get("prediction_prob")]

            per_job = {}
            for a in apps:
                jid = a["job_id"]
                per_job.setdefault(jid, []).append(a.get("rank_score", 0))

            job_stats = []
            for jid, sc in per_job.items():
                job = db.jobs.find_one({"_id": __import__("bson").ObjectId(jid)}, {"title": 1})
                job_stats.append({
                    "job_title": job["title"] if job else "Unknown",
                    "n_candidates": len(sc),
                    "avg_score": round(float(np.mean(sc)), 4),
                    "max_score": round(float(np.max(sc)), 4),
                    "min_score": round(float(np.min(sc)), 4),
                })

            results["candidate_evaluation"] = {
                "total_applications": len(apps),
                "suitable_count": len(suitable),
                "not_suitable_count": len(not_suitable),
                "avg_rank_score": round(float(np.mean(scores)), 4),
                "max_rank_score": round(float(np.max(scores)), 4),
                "min_rank_score": round(float(np.min(scores)), 4),
                "avg_confidence": round(float(np.mean(probs)), 4) if probs else 0,
                "per_job": job_stats,
            }
        else:
            results["candidate_evaluation"] = {"error": "No applications found in DB."}
        print(f"  Total apps: {len(apps)} | Suitable: {len(suitable)} | Not Suitable: {len(not_suitable)}")

        # ----------------------------------------------------------------
        # TEST 3: Skill Clustering (per job)
        # ----------------------------------------------------------------
        print("\n[3/3] Running Skill Clustering tests...")
        from app.ml.training.clusterer import find_optimal_k, kmeans_cluster
        from app.ml.preprocessing.nlp_pipeline import transform_with_vectorizer

        from app.ml.model_registry import ModelRegistry
        registry = ModelRegistry(app.config["MODELS_FOLDER"])
        try:
            vec = registry.load_latest("vectorizer")
        except Exception:
            vec = vectorizer  # fall back to freshly trained one

        jobs = list(db.jobs.find({"is_active": True}, {"_id": 1, "title": 1}))
        cluster_results = []

        for job in jobs:
            job_id = str(job["_id"])
            job_apps = list(db.applications.find(
                {"job_id": job_id, "resume_text": {"$exists": True, "$ne": ""}},
                {"resume_text": 1}
            ))
            if len(job_apps) < 2:
                cluster_results.append({"job": job["title"], "n": len(job_apps), "note": "Too few candidates"})
                continue

            texts = [preprocess_text(a.get("resume_text", "")) for a in job_apps]
            X_c = transform_with_vectorizer(vec, texts)
            elbow = find_optimal_k(X_c, k_range=range(2, min(8, len(job_apps))))
            labels, sil, _ = kmeans_cluster(X_c, n_clusters=elbow["optimal_k"])
            dist = {str(c): int(np.sum(labels == c)) for c in set(labels)}
            cluster_results.append({
                "job": job["title"],
                "n_candidates": len(job_apps),
                "optimal_k": elbow["optimal_k"],
                "silhouette_score": round(sil, 4),
                "cluster_distribution": dist,
                "inertias": elbow["inertias"][:5],
            })
            print(f"  {job['title']}: K={elbow['optimal_k']}, Sil={sil:.4f}, n={len(job_apps)}")

        results["clustering"] = cluster_results

        # ----------------------------------------------------------------
        # Save & Print
        # ----------------------------------------------------------------
        out_path = os.path.join(os.path.dirname(__file__), "test_results.json")
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n--- All tests complete. Results saved to {out_path} ---")
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_tests()
