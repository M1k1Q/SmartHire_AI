"""
ml/pipeline.py
Master ML pipeline orchestrator.

Responsibilities:
  parse → preprocess → vectorize → rank → classify → cluster → persist results

Also provides a retrain() method that rebuilds all models from DB data.
"""
import os
import logging
from typing import Dict

import numpy as np

from .preprocessing.resume_parser import parse_resume
from .preprocessing.nlp_pipeline import (
    preprocess_text, extract_entities, build_tfidf_vectorizer, transform_with_vectorizer
)
from .training.ranker import compute_composite_score, compute_cosine_similarity, compute_skill_overlap, normalize_experience
from .training.classifier import train_with_smote, predict, compare_all_models
from .training.clusterer import find_optimal_k, kmeans_cluster, cluster_and_visualize
from .evaluation.metrics import split_data, evaluate_classifier, cross_validate
from .evaluation.explainability import compute_shap_values, detect_bias
from .model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class MLPipeline:
    """
    Unified ML pipeline for the Smart Recruitment Platform.

    Lifecycle:
        1. train()       — Build vectorizer + classifier on synthetic/real data
        2. process()     — Run a single resume through the full pipeline
        3. retrain()     — Rebuild models from live DB data
    """

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.registry = ModelRegistry(model_dir)
        self._vectorizer = None
        self._classifier = None

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _ensure_models_loaded(self):
        """Lazy-load models from registry."""
        if self._vectorizer is None:
            try:
                self._vectorizer = self.registry.load_latest("vectorizer")
                logger.info("Vectorizer loaded from registry.")
            except FileNotFoundError:
                logger.warning("No vectorizer found. Training on synthetic data.")
                self._bootstrap_train()

        if self._classifier is None:
            try:
                self._classifier = self.registry.load_latest("classifier")
                logger.info("Classifier loaded from registry.")
            except FileNotFoundError:
                logger.warning("No classifier found. Training on synthetic data.")
                self._bootstrap_train()

    def _bootstrap_train(self):
        """Train on synthetic data when no real data is available."""
        from .data.generate_synthetic_data import generate_synthetic_dataset
        logger.info("Bootstrapping: generating synthetic training data...")
        docs, labels, metadata = generate_synthetic_dataset(n_samples=200)

        processed = [preprocess_text(d) for d in docs]
        vectorizer, X = build_tfidf_vectorizer(processed)
        y = np.array(labels)

        X_train, X_test, y_train, y_test = split_data(X, y)
        classifier, _, _ = train_with_smote(X_train, y_train, model_name="random_forest")

        metrics = evaluate_classifier(classifier, X_test, y_test)

        self._vectorizer = vectorizer
        self._classifier = classifier

        self.registry.save(vectorizer, "vectorizer", {"source": "synthetic_bootstrap"})
        self.registry.save(classifier, "classifier", {
            "source": "synthetic_bootstrap",
            "metrics": metrics,
        })
        logger.info(f"Bootstrap training complete. F1={metrics['f1_score']}, AUC={metrics['roc_auc']}")

    # ------------------------------------------------------------------
    # Single-resume processing
    # ------------------------------------------------------------------

    def process(
        self,
        resume_path: str,
        job_description: str,
        job_skills: list,
    ) -> Dict:
        """
        Run the full ML pipeline on a single resume.

        Steps:
          1. Parse PDF/DOCX → text
          2. Preprocess (tokenize, lemmatize, remove stopwords)
          3. NER extraction (skills, experience)
          4. TF-IDF vectorization
          5. Cosine similarity ranking score
          6. Classification (Suitable / Not Suitable)
          7. Return structured results

        Args:
            resume_path:     Absolute path to resume file.
            job_description: Raw job description text.
            job_skills:      Required skills list from job posting.

        Returns:
            dict with: resume_text, processed_text, extracted_skills,
                       experience_years, rank_score, prediction, prediction_prob
        """
        self._ensure_models_loaded()

        # Step 1: Parse
        resume_text = parse_resume(resume_path)

        # Step 2: Preprocess
        processed = preprocess_text(resume_text)

        # Step 3: Named Entity Recognition
        entities = extract_entities(resume_text)
        extracted_skills = entities.get("skills", [])
        experience_years = entities.get("experience_years", 0.0)

        # Step 4: Vectorize resume + job description
        resume_vector = transform_with_vectorizer(self._vectorizer, [processed])
        job_processed = preprocess_text(job_description)
        job_vector = transform_with_vectorizer(self._vectorizer, [job_processed])

        # Step 5: Ranking score (composite)
        similarity = compute_cosine_similarity(resume_vector, job_vector)
        skill_overlap = compute_skill_overlap(extracted_skills, job_skills)
        rank_score = compute_composite_score(similarity, experience_years, extracted_skills, job_skills)

        # Step 6: Classification
        predictions, probabilities = predict(self._classifier, resume_vector)
        label_map = {1: "Suitable", 0: "Not Suitable"}
        prediction = label_map.get(int(predictions[0]), "Not Suitable")
        prediction_prob = float(probabilities[0])

        # Override prediction with rank_score threshold if classifier not yet trained on real data
        if rank_score >= 0.40:
            prediction = "Suitable"
            prediction_prob = max(prediction_prob, rank_score)
        elif rank_score < 0.20:
            prediction = "Not Suitable"
            prediction_prob = min(prediction_prob, 1 - rank_score)

        return {
            "resume_text": resume_text,
            "processed_text": processed,
            "extracted_skills": extracted_skills,
            "experience_years": experience_years,
            "similarity": round(similarity, 4),
            "skill_overlap": round(skill_overlap, 4),
            "rank_score": round(rank_score, 4),
            "prediction": prediction,
            "prediction_prob": round(prediction_prob, 4),
        }

    # ------------------------------------------------------------------
    # Retraining from DB
    # ------------------------------------------------------------------

    def retrain(self, db) -> Dict:
        """
        Retrain the vectorizer and classifier using all application data in MongoDB.

        Args:
            db: PyMongo database instance.

        Returns:
            dict with training results and metrics.
        """
        logger.info("Starting model retraining from database...")

        # Fetch all applications with resume text and prediction
        apps = list(db.applications.find(
            {"resume_text": {"$ne": ""}, "prediction": {"$in": ["Suitable", "Not Suitable"]}}
        ))

        if len(apps) < 10:
            logger.warning(f"Only {len(apps)} labeled samples. Supplementing with synthetic data.")
            from .data.generate_synthetic_data import generate_synthetic_dataset
            syn_docs, syn_labels, _ = generate_synthetic_dataset(n_samples=150)
            documents = [preprocess_text(a["resume_text"]) for a in apps] + [preprocess_text(d) for d in syn_docs]
            labels = [1 if a["prediction"] == "Suitable" else 0 for a in apps] + syn_labels
        else:
            documents = [preprocess_text(a["resume_text"]) for a in apps]
            labels = [1 if a["prediction"] == "Suitable" else 0 for a in apps]

        # Build new vectorizer
        vectorizer, X = build_tfidf_vectorizer(documents)
        y = np.array(labels)

        # Train/test split
        X_train, X_test, y_train, y_test = split_data(X, y)

        # Compare all models and pick best
        comparison, best_classifier = compare_all_models(X_train, y_train, X_test, y_test)
        logger.info(f"Model comparison: {comparison}")

        if best_classifier is None:
            best_classifier, _, _ = train_with_smote(X_train, y_train)

        # Evaluate best model
        metrics = evaluate_classifier(best_classifier, X_test, y_test)
        cv_results = cross_validate(best_classifier, X, y)

        # Save to registry
        self._vectorizer = vectorizer
        self._classifier = best_classifier
        self.registry.save(vectorizer, "vectorizer", {"n_documents": len(documents)})
        self.registry.save(best_classifier, "classifier", {
            "metrics": metrics,
            "cv": cv_results,
            "best_model": comparison.get("best_model", "unknown"),
            "n_samples": len(documents),
        })

        # Persist metrics to DB
        db.model_metrics.insert_one({
            "trained_at": __import__("datetime").datetime.utcnow().isoformat(),
            "n_samples": len(documents),
            "metrics": metrics,
            "cv_results": cv_results,
            "model_comparison": comparison,
        })

        return {
            "status": "success",
            "n_samples": len(documents),
            "metrics": metrics,
            "cv_results": cv_results,
            "best_model": comparison.get("best_model"),
        }

    # ------------------------------------------------------------------
    # Cluster all applications for a job
    # ------------------------------------------------------------------

    def cluster_job_applicants(self, applications: list) -> list:
        """
        Cluster all applicants for a job and return 2D visualization data.

        Args:
            applications: List of application dicts with 'resume_text' and 'id'.

        Returns:
            List of cluster point dicts (id, cluster_id, x, y).
        """
        self._ensure_models_loaded()
        if not applications:
            return []

        texts = [preprocess_text(a.get("resume_text", "")) for a in applications]
        ids = [a["id"] for a in applications]
        X = transform_with_vectorizer(self._vectorizer, texts)

        result = cluster_and_visualize(X, ids, method="tsne")
        if isinstance(result, tuple):
            points, k, sil, elbow = result
        else:
            points = result
            k, sil, elbow = 3, 0.0, {}

        return {"points": points, "n_clusters": k, "silhouette_score": sil, "elbow": elbow}

    # ------------------------------------------------------------------
    # Feature importance (for analytics dashboard)
    # ------------------------------------------------------------------

    def get_feature_importance(self, top_n: int = 20) -> list:
        """Return top N TF-IDF feature importance from the current classifier."""
        self._ensure_models_loaded()
        try:
            feature_names = self._vectorizer.get_feature_names_out().tolist()
            # Pull a small dummy sample for SHAP
            dummy_X = transform_with_vectorizer(self._vectorizer, ["python machine learning experience"])
            result = compute_shap_values(self._classifier, dummy_X, feature_names)
            return result.get("top_features", [])[:top_n]
        except Exception as e:
            logger.error(f"Feature importance failed: {e}")
            return []
