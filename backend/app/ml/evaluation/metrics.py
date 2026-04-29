"""
ml/evaluation/metrics.py
Model evaluation utilities:
  - Train/Test split
  - K-Fold Cross Validation
  - Accuracy, Precision, Recall, F1, ROC-AUC
  - Confusion Matrix
  - Learning curve (overfitting analysis)
  - Model comparison report
"""
import logging
from typing import Dict, Tuple, List

import numpy as np
from sklearn.model_selection import (
    train_test_split, cross_val_score, StratifiedKFold, learning_curve
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve
)

logger = logging.getLogger(__name__)


def split_data(X, y, test_size: float = 0.2, random_state: int = 42):
    """
    Stratified train/test split to preserve class distribution.

    Returns:
        X_train, X_test, y_train, y_test
    """
    return train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )


def evaluate_classifier(classifier, X_test, y_test) -> Dict:
    """
    Compute full evaluation metrics for a trained classifier.

    Returns:
        dict with accuracy, precision, recall, f1, roc_auc, confusion_matrix,
        roc_curve, classification_report
    """
    y_pred = classifier.predict(X_test)
    y_prob = classifier.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    try:
        auc = roc_auc_score(y_test, y_prob)
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_data = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
    except Exception:
        auc = 0.0
        roc_data = {"fpr": [], "tpr": []}

    cm = confusion_matrix(y_test, y_pred).tolist()
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": cm,
        "roc_curve": roc_data,
        "classification_report": report,
    }


def cross_validate(classifier, X, y, cv: int = 5) -> Dict:
    """
    K-Fold cross-validation evaluation.

    Returns:
        dict with mean and std for accuracy, f1, roc_auc.
    """
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

    acc_scores = cross_val_score(classifier, X, y, cv=skf, scoring="accuracy")
    f1_scores = cross_val_score(classifier, X, y, cv=skf, scoring="f1")
    auc_scores = cross_val_score(classifier, X, y, cv=skf, scoring="roc_auc")

    return {
        "cv_folds": cv,
        "accuracy": {"mean": round(acc_scores.mean(), 4), "std": round(acc_scores.std(), 4)},
        "f1_score": {"mean": round(f1_scores.mean(), 4), "std": round(f1_scores.std(), 4)},
        "roc_auc": {"mean": round(auc_scores.mean(), 4), "std": round(auc_scores.std(), 4)},
    }


def compute_learning_curves(classifier, X, y, cv: int = 5) -> Dict:
    """
    Compute learning curves to analyze overfitting vs underfitting.

    Returns:
        dict with train_sizes, train_scores_mean/std, val_scores_mean/std
    """
    train_sizes_frac = np.linspace(0.1, 1.0, 10)
    train_sizes, train_scores, val_scores = learning_curve(
        classifier, X, y,
        train_sizes=train_sizes_frac,
        cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42),
        scoring="f1",
        n_jobs=-1,
    )

    return {
        "train_sizes": train_sizes.tolist(),
        "train_scores_mean": train_scores.mean(axis=1).round(4).tolist(),
        "train_scores_std": train_scores.std(axis=1).round(4).tolist(),
        "val_scores_mean": val_scores.mean(axis=1).round(4).tolist(),
        "val_scores_std": val_scores.std(axis=1).round(4).tolist(),
    }


def compare_models_report(model_results: Dict) -> str:
    """
    Format a model comparison table as a string.

    Args:
        model_results: Dict from classifier.compare_all_models()

    Returns:
        Formatted string table.
    """
    lines = ["\n=== Model Comparison Report ==="]
    header = f"{'Model':<25} {'Accuracy':>10} {'F1':>8} {'ROC-AUC':>10}"
    lines.append(header)
    lines.append("-" * 60)

    for name, metrics in model_results.items():
        if name == "best_model" or "error" in metrics:
            continue
        acc = metrics.get("test_accuracy", 0)
        f1 = metrics.get("test_f1", 0)
        auc = metrics.get("test_auc", 0)
        lines.append(f"{name:<25} {acc:>10.4f} {f1:>8.4f} {auc:>10.4f}")

    if "best_model" in model_results:
        lines.append(f"\n✔ Best Model: {model_results['best_model']}")

    return "\n".join(lines)
