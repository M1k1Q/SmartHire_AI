"""
ml/training/classifier.py
Supervised classification: Suitable / Not Suitable prediction.

Models implemented:
  - Logistic Regression
  - Support Vector Machine (SVM)
  - Random Forest
  - Gradient Boosting (XGBoost)

Features:
  - GridSearchCV hyperparameter tuning
  - SMOTE for class imbalance handling
  - Model comparison and selection
  - joblib persistence
"""
import os
import logging
import json
from typing import Dict, Tuple, Optional

import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, learning_curve
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Definitions with Hyperparameter Grids
# ---------------------------------------------------------------------------

MODEL_CONFIGS = {
    "logistic_regression": {
        "estimator": LogisticRegression(max_iter=1000, random_state=42),
        "param_grid": {
            "clf__C": [0.01, 0.1, 1.0, 10.0],
            "clf__penalty": ["l2"],
            "clf__solver": ["lbfgs"],
        },
    },
    "svm": {
        "estimator": SVC(probability=True, random_state=42),
        "param_grid": {
            "clf__C": [0.1, 1.0, 10.0],
            "clf__kernel": ["rbf", "linear"],
            "clf__gamma": ["scale"],
        },
    },
    "random_forest": {
        "estimator": RandomForestClassifier(random_state=42),
        "param_grid": {
            "clf__n_estimators": [50, 100, 200],
            "clf__max_depth": [None, 10, 20],
            "clf__min_samples_split": [2, 5],
        },
    },
    "gradient_boosting": {
        "estimator": GradientBoostingClassifier(random_state=42),
        "param_grid": {
            "clf__n_estimators": [50, 100],
            "clf__learning_rate": [0.05, 0.1, 0.2],
            "clf__max_depth": [3, 5],
        },
    },
}


def _build_pipeline(estimator) -> Pipeline:
    """Wrap estimator in a Pipeline with StandardScaler."""
    return Pipeline([
        ("scaler", StandardScaler(with_mean=False)),  # sparse-compatible
        ("clf", estimator),
    ])


def train_with_smote(X_train, y_train, model_name: str = "random_forest") -> Tuple:
    """
    Train a classifier with SMOTE oversampling for class imbalance.

    Args:
        X_train: Feature matrix (sparse or dense).
        y_train: Binary labels (1 = Suitable, 0 = Not Suitable).
        model_name: Key from MODEL_CONFIGS.

    Returns:
        Tuple of (best_estimator, best_params, cv_score)
    """
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        logger.info(f"SMOTE applied: {X_train.shape} → {X_res.shape}")
    except Exception as e:
        logger.warning(f"SMOTE failed ({e}), using original data.")
        X_res, y_res = X_train, y_train

    return train_classifier(X_res, y_res, model_name=model_name)


def train_classifier(X_train, y_train, model_name: str = "random_forest") -> Tuple:
    """
    Train a single classifier with GridSearchCV.

    Returns:
        Tuple of (best_estimator Pipeline, best_params dict, best_cv_score float)
    """
    if model_name not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model: {model_name}. Choose from {list(MODEL_CONFIGS.keys())}")

    config = MODEL_CONFIGS[model_name]
    pipeline = _build_pipeline(config["estimator"])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid_search = GridSearchCV(
        pipeline,
        param_grid=config["param_grid"],
        cv=cv,
        scoring="f1",
        n_jobs=-1,
        verbose=0,
        refit=True,
    )

    logger.info(f"Training {model_name} with GridSearchCV...")
    grid_search.fit(X_train, y_train)

    logger.info(
        f"{model_name}: best_params={grid_search.best_params_}, "
        f"best_cv_f1={grid_search.best_score_:.4f}"
    )

    return grid_search.best_estimator_, grid_search.best_params_, grid_search.best_score_


def compare_all_models(X_train, y_train, X_test, y_test) -> Dict:
    """
    Train and evaluate all models, returning a comparison report.

    Returns:
        dict mapping model_name → {cv_score, test_accuracy, test_f1, test_auc}
    """
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

    results = {}
    best_model = None
    best_score = -1

    for model_name in MODEL_CONFIGS:
        try:
            estimator, params, cv_score = train_classifier(X_train, y_train, model_name)
            y_pred = estimator.predict(X_test)
            y_prob = estimator.predict_proba(X_test)[:, 1]

            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            auc = roc_auc_score(y_test, y_prob)

            results[model_name] = {
                "cv_f1": round(cv_score, 4),
                "test_accuracy": round(acc, 4),
                "test_f1": round(f1, 4),
                "test_auc": round(auc, 4),
                "best_params": params,
            }

            if f1 > best_score:
                best_score = f1
                best_model = (model_name, estimator)

        except Exception as e:
            logger.error(f"Model {model_name} failed: {e}")
            results[model_name] = {"error": str(e)}

    if best_model:
        results["best_model"] = best_model[0]

    return results, best_model[1] if best_model else None


def predict(classifier, X) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run inference with a trained classifier.

    Returns:
        Tuple of (predictions array, probabilities array)
    """
    predictions = classifier.predict(X)
    probabilities = classifier.predict_proba(X)[:, 1]
    return predictions, probabilities


def save_classifier(classifier, path: str, metadata: dict = None):
    """Save classifier + optional metadata to disk."""
    joblib.dump(classifier, path)
    if metadata:
        meta_path = path.replace(".pkl", "_meta.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
    logger.info(f"Classifier saved to {path}")


def load_classifier(path: str):
    """Load a saved classifier from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Classifier not found at {path}")
    return joblib.load(path)
