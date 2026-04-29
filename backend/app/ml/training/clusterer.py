"""
ml/training/clusterer.py
Unsupervised clustering of candidates by skill/text similarity.

Algorithms:
  - K-Means (primary)
  - Hierarchical / Agglomerative (optional)

Evaluation:
  - Elbow Method (inertia vs K)
  - Silhouette Score

Dimensionality Reduction for visualization:
  - PCA (2D projection)
  - t-SNE (2D non-linear)
"""
import logging
from typing import Dict, List, Tuple

import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.preprocessing import Normalizer

logger = logging.getLogger(__name__)


def find_optimal_k(X, k_range: range = range(2, 11)) -> Dict:
    """
    Elbow Method: compute inertia and silhouette scores for different K values
    to suggest the optimal number of clusters.

    Args:
        X: Feature matrix (dense or sparse).
        k_range: Range of K values to evaluate.

    Returns:
        dict with 'inertias', 'silhouette_scores', 'optimal_k'
    """
    if hasattr(X, "toarray"):
        X_dense = X.toarray()
    else:
        X_dense = np.array(X)

    # Normalize
    X_norm = Normalizer().fit_transform(X_dense)

    inertias = []
    sil_scores = []
    k_values = list(k_range)

    n_samples = X_norm.shape[0]

    for k in k_values:
        if k >= n_samples:
            break
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_norm)
        inertias.append(round(km.inertia_, 2))
        if k > 1 and len(set(labels)) > 1:
            sil_scores.append(round(silhouette_score(X_norm, labels), 4))
        else:
            sil_scores.append(0.0)

    # Optimal K: highest silhouette score
    if sil_scores:
        best_idx = int(np.argmax(sil_scores))
        optimal_k = k_values[best_idx]
    else:
        optimal_k = 3

    return {
        "k_values": k_values[:len(inertias)],
        "inertias": inertias,
        "silhouette_scores": sil_scores,
        "optimal_k": optimal_k,
    }


def kmeans_cluster(X, n_clusters: int = 3) -> Tuple[np.ndarray, float, KMeans]:
    """
    Perform K-Means clustering.

    Args:
        X: Feature matrix.
        n_clusters: Number of clusters.

    Returns:
        Tuple of (labels array, silhouette score, fitted KMeans model)
    """
    if hasattr(X, "toarray"):
        X_dense = X.toarray()
    else:
        X_dense = np.array(X)

    X_norm = Normalizer().fit_transform(X_dense)

    n_samples = X_norm.shape[0]
    n_clusters = min(n_clusters, max(2, n_samples - 1))

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_norm)

    if len(set(labels)) > 1:
        sil = silhouette_score(X_norm, labels)
    else:
        sil = 0.0

    logger.info(f"K-Means: {n_clusters} clusters, silhouette={sil:.4f}")
    return labels, round(sil, 4), km


def hierarchical_cluster(X, n_clusters: int = 3) -> np.ndarray:
    """
    Perform Agglomerative (Hierarchical) Clustering.

    Returns:
        Label array
    """
    if hasattr(X, "toarray"):
        X_dense = X.toarray()
    else:
        X_dense = np.array(X)

    X_norm = Normalizer().fit_transform(X_dense)
    n_clusters = min(n_clusters, max(2, X_norm.shape[0] - 1))

    agg = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
    labels = agg.fit_predict(X_norm)
    logger.info(f"Hierarchical clustering: {n_clusters} clusters")
    return labels


def reduce_to_2d(X, method: str = "pca") -> np.ndarray:
    """
    Reduce feature matrix to 2D for visualization.

    Args:
        X: Feature matrix (sparse or dense).
        method: 'pca' or 'tsne'

    Returns:
        2D numpy array of shape (n_samples, 2)
    """
    if hasattr(X, "toarray"):
        X_dense = X.toarray()
    else:
        X_dense = np.array(X)

    X_norm = Normalizer().fit_transform(X_dense)

    if method == "tsne":
        try:
            from sklearn.manifold import TSNE
            n_samples = X_norm.shape[0]
            perplexity = min(30, max(5, n_samples // 3))
            reducer = TSNE(n_components=2, random_state=42, perplexity=perplexity)
            # First reduce with PCA if high dimensional
            if X_norm.shape[1] > 50:
                pca = PCA(n_components=min(50, X_norm.shape[0], X_norm.shape[1]))
                X_norm = pca.fit_transform(X_norm)
            coords = reducer.fit_transform(X_norm)
        except Exception as e:
            logger.warning(f"t-SNE failed ({e}), falling back to PCA.")
            coords = _pca_reduce(X_norm)
    else:
        coords = _pca_reduce(X_norm)

    return coords


def _pca_reduce(X_norm) -> np.ndarray:
    """Reduce to 2D with PCA."""
    n_components = min(2, X_norm.shape[0], X_norm.shape[1])
    pca = PCA(n_components=n_components)
    coords = pca.fit_transform(X_norm)
    if coords.shape[1] == 1:
        coords = np.hstack([coords, np.zeros((coords.shape[0], 1))])
    return coords


def cluster_and_visualize(X, candidate_ids: List[str], method: str = "tsne") -> List[Dict]:
    """
    Full clustering pipeline: find optimal K → cluster → reduce to 2D.

    Returns:
        List of dicts with: id, cluster_id, x, y
    """
    if X.shape[0] < 2:
        return [{"id": candidate_ids[0], "cluster_id": 0, "x": 0.0, "y": 0.0}]

    # Find optimal K
    elbow = find_optimal_k(X)
    k = elbow["optimal_k"]

    # Cluster
    labels, sil, _ = kmeans_cluster(X, n_clusters=k)

    # Reduce to 2D
    coords_2d = reduce_to_2d(X, method=method)

    points = []
    for i, cid in enumerate(candidate_ids):
        points.append({
            "id": cid,
            "cluster_id": int(labels[i]),
            "x": round(float(coords_2d[i, 0]), 4),
            "y": round(float(coords_2d[i, 1]), 4),
        })

    return points, k, round(sil, 4), elbow
