"""
ml/model_registry.py
Model versioning, saving, loading, and lifecycle management.

Stores models in the ml_models/ directory with metadata (version, type, metrics, trained_at).
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

import joblib

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Simple file-based model registry.

    Directory structure:
        ml_models/
          ├── classifier_v1.pkl
          ├── classifier_v1_meta.json
          ├── vectorizer_v1.pkl
          └── registry.json       ← index of all saved models
    """

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.registry_path = os.path.join(model_dir, "registry.json")
        self._registry = self._load_registry()

    # -----------------------------------------------------------------
    # Registry persistence
    # -----------------------------------------------------------------

    def _load_registry(self) -> Dict:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"models": []}

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self._registry, f, indent=2)

    # -----------------------------------------------------------------
    # Save / Load
    # -----------------------------------------------------------------

    def save(self, obj, name: str, metadata: Dict = None) -> str:
        """
        Save a model/vectorizer to disk and register it.

        Args:
            obj: The sklearn object to save.
            name: A descriptive name (e.g. 'classifier', 'vectorizer').
            metadata: Optional dict of metrics, params, etc.

        Returns:
            Path where the model was saved.
        """
        version = self._next_version(name)
        filename = f"{name}_v{version}.pkl"
        path = os.path.join(self.model_dir, filename)

        joblib.dump(obj, path)

        meta = {
            "name": name,
            "version": version,
            "filename": filename,
            "path": path,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }

        # Save metadata sidecar
        meta_path = path.replace(".pkl", "_meta.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        self._registry["models"].append(meta)
        self._save_registry()

        logger.info(f"Saved {name} v{version} → {path}")
        return path

    def load_latest(self, name: str):
        """Load the most recent version of a named model."""
        entries = [m for m in self._registry["models"] if m["name"] == name]
        if not entries:
            raise FileNotFoundError(f"No saved model with name '{name}'.")
        # Sort by version descending
        entries.sort(key=lambda x: x["version"], reverse=True)
        path = entries[0]["path"]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file missing: {path}")
        logger.info(f"Loaded {name} v{entries[0]['version']} from {path}")
        return joblib.load(path)

    def load_version(self, name: str, version: int):
        """Load a specific version of a model."""
        for entry in self._registry["models"]:
            if entry["name"] == name and entry["version"] == version:
                return joblib.load(entry["path"])
        raise FileNotFoundError(f"Model '{name}' v{version} not found in registry.")

    def exists(self, name: str) -> bool:
        """Check if any version of a named model exists."""
        return any(m["name"] == name for m in self._registry["models"])

    def list_models(self) -> list:
        """Return all registered models."""
        return self._registry["models"]

    def get_latest_metadata(self, name: str) -> Optional[Dict]:
        """Get metadata for the latest version of a model."""
        entries = [m for m in self._registry["models"] if m["name"] == name]
        if not entries:
            return None
        entries.sort(key=lambda x: x["version"], reverse=True)
        return entries[0]

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _next_version(self, name: str) -> int:
        existing = [m["version"] for m in self._registry["models"] if m["name"] == name]
        return max(existing, default=0) + 1
