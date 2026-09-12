"""
LandslideGuard ML Model — Modular Risk Prediction Interface

⚠ DEMONSTRATION MODEL — Trained on synthetic data
Not an operational forecast. Thresholds require calibration.
"""

import os
import logging
import numpy as np
import joblib
from typing import Optional

logger = logging.getLogger("landslide_guard.ml")

FEATURES = [
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_24h", "rainfall_72h",
    "soil_moisture", "slope", "elevation", "geology_susceptibility",
    "historical_landslide_density", "distance_to_historical_landslide",
    "drainage_density",
]

# Feature defaults for missing values — conservative estimates
FEATURE_DEFAULTS = {
    "rainfall_1h": 0.0,
    "rainfall_3h": 0.0,
    "rainfall_6h": 0.0,
    "rainfall_24h": 0.0,
    "rainfall_72h": 0.0,
    "soil_moisture": 0.5,          # moderate default
    "slope": 20.0,                 # moderate slope
    "elevation": 500.0,
    "geology_susceptibility": 0.5,
    "historical_landslide_density": 0.0,
    "distance_to_historical_landslide": 100.0,
    "drainage_density": 0.5,
}

RISK_THRESHOLDS = [
    (0, 29, "LOW"),
    (30, 49, "MODERATE"),
    (50, 69, "HIGH"),
    (70, 84, "VERY_HIGH"),
    (85, 100, "CRITICAL"),
]


def score_to_level(score: float) -> str:
    """Convert risk score (0-100) to risk level string."""
    for low, high, level in RISK_THRESHOLDS:
        if low <= score <= high:
            return level
    return "CRITICAL" if score > 84 else "LOW"


class RiskModel:
    """
    Modular ML model interface for landslide risk prediction.

    Supports swapping the underlying algorithm (Random Forest, XGBoost, etc.)
    without changing the prediction API.
    """

    def __init__(self, model_path: str, version: str = "v1-demo"):
        self.model_path = model_path
        self.version = version
        self.model = None
        self.feature_names = FEATURES
        self._feature_importances = None

    def load(self):
        """Load the trained model from disk."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}. "
                "Run 'python -m app.ml.train' to train the demo model."
            )
        self.model = joblib.load(self.model_path)
        # Cache feature importances
        if hasattr(self.model, 'feature_importances_'):
            self._feature_importances = dict(
                zip(self.feature_names, self.model.feature_importances_)
            )
        logger.info(f"Model loaded: {self.version} (DEMO MODEL)")

    def is_loaded(self) -> bool:
        return self.model is not None

    def predict(self, features: dict) -> dict:
        """
        Run risk prediction.

        Args:
            features: dict of feature_name → value. Missing features
                      are filled with conservative defaults.

        Returns:
            dict with risk_score, risk_level, confidence, model_version,
            top_drivers, input_snapshot, data_status
        """
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load() first.")

        # Build feature vector, handling missing values
        feature_vector = []
        missing_features = []
        input_snapshot = {}

        for fname in self.feature_names:
            if fname in features and features[fname] is not None:
                val = float(features[fname])
            else:
                val = FEATURE_DEFAULTS[fname]
                missing_features.append(fname)
            feature_vector.append(val)
            input_snapshot[fname] = val

        X = np.array([feature_vector])

        # Probability prediction
        probabilities = self.model.predict_proba(X)[0]
        landslide_probability = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])

        # Risk score: 0-100
        risk_score = round(landslide_probability * 100, 1)
        risk_score = max(0, min(100, risk_score))

        risk_level = score_to_level(risk_score)

        # Confidence: reduce if features are missing
        base_confidence = landslide_probability if landslide_probability > 0.5 else (1 - landslide_probability)
        missing_penalty = len(missing_features) * 0.05
        confidence = round(max(0.3, base_confidence - missing_penalty), 2)

        # Top drivers
        top_drivers = self._get_feature_drivers(input_snapshot)

        # Data status
        data_status = "DEMO"  # Always DEMO until validated data integrated

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "model_version": self.version,
            "top_drivers": top_drivers,
            "input_snapshot": input_snapshot,
            "missing_features": missing_features,
            "data_status": data_status,
        }

    def _get_feature_drivers(self, input_snapshot: dict) -> list:
        """
        Get feature contribution/importance for this prediction.

        Uses model feature importance (NOT SHAP by default).
        SHAP is optional — if installed, it can enhance this.
        """
        if self._feature_importances is None:
            return []

        drivers = []
        for fname, importance in self._feature_importances.items():
            value = input_snapshot.get(fname, 0)
            # Normalize contribution: importance * normalized feature value
            max_val = self._get_feature_max(fname)
            normalized = min(value / max_val, 1.0) if max_val > 0 else 0
            contribution = round(importance * normalized * 100, 1)

            drivers.append({
                "feature": fname,
                "importance": round(importance, 4),
                "value": value,
                "contribution": contribution,
            })

        # Sort by contribution descending
        drivers.sort(key=lambda d: d["contribution"], reverse=True)
        return drivers[:8]  # Top 8 drivers

    @staticmethod
    def _get_feature_max(fname: str) -> float:
        """Approximate max values for normalization."""
        maxes = {
            "rainfall_1h": 50, "rainfall_3h": 100, "rainfall_6h": 150,
            "rainfall_24h": 300, "rainfall_72h": 600,
            "soil_moisture": 1.0, "slope": 50, "elevation": 4000,
            "geology_susceptibility": 1.0, "historical_landslide_density": 3.0,
            "distance_to_historical_landslide": 200, "drainage_density": 1.0,
        }
        return maxes.get(fname, 1.0)

    def get_version(self) -> str:
        return self.version

    def get_info(self) -> dict:
        return {
            "version": self.version,
            "model_type": type(self.model).__name__ if self.model else "not_loaded",
            "data_type": "DEMO",
            "features": self.feature_names,
            "loaded": self.is_loaded(),
            "note": "Prototype model trained on synthetic NER data. NOT an operational forecast.",
        }
