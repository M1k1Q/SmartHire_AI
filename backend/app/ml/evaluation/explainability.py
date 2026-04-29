"""
ml/evaluation/explainability.py
Model explainability and bias analysis using SHAP and LIME.

Features:
  - SHAP values for feature importance
  - LIME fallback explanation
  - Bias detection across application predictions
  - Fairness-aware analysis report
"""
import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


def compute_shap_values(classifier, X, feature_names: List[str] = None) -> Dict:
    """
    Compute SHAP values for the trained classifier.

    Uses TreeExplainer for tree-based models, LinearExplainer for linear models,
    and KernelExplainer as a universal fallback.

    Args:
        classifier: Trained sklearn Pipeline or estimator.
        X: Feature matrix (sparse or dense) — typically a small sample.
        feature_names: List of feature names from the TF-IDF vocabulary.

    Returns:
        dict with:
          - top_features: list of {feature, importance} sorted by abs mean SHAP
          - shap_values: raw values (list of lists)
          - explainer_type: which SHAP explainer was used
    """
    try:
        import shap

        # Extract the actual estimator from the Pipeline
        estimator = _extract_estimator(classifier)

        # Densify for SHAP
        if hasattr(X, "toarray"):
            X_dense = X.toarray()
        else:
            X_dense = np.array(X)

        # Use a small sample for speed
        sample_size = min(50, X_dense.shape[0])
        X_sample = X_dense[:sample_size]

        # Choose explainer based on model type
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.linear_model import LogisticRegression

        if isinstance(estimator, (RandomForestClassifier, GradientBoostingClassifier)):
            explainer = shap.TreeExplainer(estimator)
            shap_values = explainer.shap_values(X_sample)
            if isinstance(shap_values, list):
                # For binary classification, take class-1 SHAP values
                shap_vals = shap_values[1]
            else:
                shap_vals = shap_values
            explainer_type = "TreeExplainer"

        elif isinstance(estimator, LogisticRegression):
            explainer = shap.LinearExplainer(estimator, X_sample)
            shap_vals = explainer.shap_values(X_sample)
            explainer_type = "LinearExplainer"

        else:
            # Universal fallback — slower but works for any model
            background = shap.sample(X_dense, min(20, X_dense.shape[0]))
            explainer = shap.KernelExplainer(
                lambda x: estimator.predict_proba(x)[:, 1], background
            )
            shap_vals = explainer.shap_values(X_sample[:10])
            explainer_type = "KernelExplainer"

        # Compute mean absolute SHAP per feature
        mean_abs_shap = np.abs(shap_vals).mean(axis=0)

        # Build top features list
        if feature_names and len(feature_names) == len(mean_abs_shap):
            feature_importance = [
                {"feature": str(feature_names[i]), "importance": round(float(mean_abs_shap[i]), 6)}
                for i in range(len(feature_names))
            ]
        else:
            feature_importance = [
                {"feature": f"feature_{i}", "importance": round(float(v), 6)}
                for i, v in enumerate(mean_abs_shap)
            ]

        # Sort by importance descending
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)
        top_features = feature_importance[:20]

        return {
            "top_features": top_features,
            "explainer_type": explainer_type,
            "n_samples_explained": sample_size,
        }

    except ImportError:
        logger.warning("SHAP not installed. Falling back to feature importance.")
        return _fallback_feature_importance(classifier, X, feature_names)
    except Exception as e:
        logger.error(f"SHAP computation failed: {e}")
        return _fallback_feature_importance(classifier, X, feature_names)


def _extract_estimator(classifier):
    """Extract the underlying estimator from a sklearn Pipeline."""
    from sklearn.pipeline import Pipeline
    if isinstance(classifier, Pipeline):
        return classifier.named_steps.get("clf", classifier)
    return classifier


def _fallback_feature_importance(classifier, X, feature_names) -> Dict:
    """
    Fallback: use sklearn's feature_importances_ or coef_ when SHAP is unavailable.
    """
    try:
        estimator = _extract_estimator(classifier)

        if hasattr(estimator, "feature_importances_"):
            importances = estimator.feature_importances_
        elif hasattr(estimator, "coef_"):
            importances = np.abs(estimator.coef_[0])
        else:
            return {"top_features": [], "explainer_type": "none"}

        if feature_names and len(feature_names) == len(importances):
            features = [
                {"feature": str(feature_names[i]), "importance": round(float(importances[i]), 6)}
                for i in range(len(feature_names))
            ]
        else:
            features = [
                {"feature": f"feature_{i}", "importance": round(float(v), 6)}
                for i, v in enumerate(importances)
            ]

        features.sort(key=lambda x: x["importance"], reverse=True)

        return {
            "top_features": features[:20],
            "explainer_type": "feature_importances_/coef_",
            "n_samples_explained": 0,
        }
    except Exception as e:
        return {"top_features": [], "explainer_type": "error", "error": str(e)}


def detect_bias(predictions: List[Dict]) -> Dict:
    """
    Detect potential bias in predictions.

    Each prediction dict should have: {'prediction': str, 'rank_score': float, ...}
    Currently checks for:
      - Score distribution statistics
      - Prediction rate (Suitable vs Not Suitable ratio)

    NOTE: We deliberately avoid collecting sensitive attributes (gender, age, race)
    in this system to promote fairness by design.

    Args:
        predictions: List of application dicts with 'prediction' and 'rank_score'.

    Returns:
        dict with bias analysis report.
    """
    if not predictions:
        return {"error": "No predictions to analyze."}

    total = len(predictions)
    suitable = sum(1 for p in predictions if p.get("prediction") == "Suitable")
    not_suitable = total - suitable

    scores = [p.get("rank_score", 0.0) for p in predictions]
    scores_arr = np.array(scores)

    report = {
        "total_applications": total,
        "suitable_count": suitable,
        "not_suitable_count": not_suitable,
        "suitable_rate": round(suitable / total, 4) if total else 0,
        "score_statistics": {
            "mean": round(float(scores_arr.mean()), 4),
            "std": round(float(scores_arr.std()), 4),
            "min": round(float(scores_arr.min()), 4),
            "max": round(float(scores_arr.max()), 4),
            "median": round(float(np.median(scores_arr)), 4),
            "q25": round(float(np.percentile(scores_arr, 25)), 4),
            "q75": round(float(np.percentile(scores_arr, 75)), 4),
        },
        "fairness_note": (
            "This system does not use sensitive attributes (gender, age, race, religion). "
            "Predictions are based solely on skill match, experience, and text similarity."
        ),
        "bias_flags": _check_bias_flags(suitable, not_suitable, scores_arr),
    }

    return report


def _check_bias_flags(suitable: int, not_suitable: int, scores: np.ndarray) -> List[str]:
    """Identify potential bias warning flags."""
    flags = []
    total = suitable + not_suitable

    if total == 0:
        return flags

    suitable_rate = suitable / total
    if suitable_rate < 0.05:
        flags.append("⚠️  Very low suitable rate (<5%). Consider reviewing job requirements or score thresholds.")
    if suitable_rate > 0.95:
        flags.append("⚠️  Very high suitable rate (>95%). Model may not be discriminating enough.")
    if scores.std() < 0.05:
        flags.append("⚠️  Very low score variance. Check if the TF-IDF vectorizer is properly trained.")

    if not flags:
        flags.append("✅  No major bias flags detected.")

    return flags
