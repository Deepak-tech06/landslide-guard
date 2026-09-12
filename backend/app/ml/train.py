"""
Train the demo landslide risk model.

⚠ DEMONSTRATION MODEL — Trained on synthetic data.
Run: python -m app.ml.train
"""

import os
import json
import joblib
import logging
from datetime import datetime, timezone

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from app.ml.synthetic_data import generate_training_data, FEATURES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("landslide_guard.train")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")


def train_model():
    """Train a Random Forest model on synthetic NER landslide data."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    logger.info("Generating synthetic training data...")
    df = generate_training_data(n_samples=5000)

    X = df[FEATURES]
    y = df["landslide_occurred"]

    logger.info(f"Dataset: {len(df)} samples, positive rate: {y.mean():.2%}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Save model
    model_path = os.path.join(MODEL_DIR, "risk_model.joblib")
    joblib.dump(model, model_path)
    logger.info(f"Model saved → {model_path}")

    # Log feature importances (NOT accuracy claims)
    importances = dict(zip(FEATURES, model.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    logger.info("Feature importances (from synthetic training data):")
    for feat, imp in sorted_imp:
        logger.info(f"  {feat}: {imp:.4f}")

    # Save metadata
    metadata = {
        "version": "v1-demo",
        "model_type": "RandomForestClassifier",
        "data_type": "DEMO",
        "n_samples": len(df),
        "n_features": len(FEATURES),
        "features": FEATURES,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Prototype model trained on synthetic NER data. "
            "NOT an operational forecast. "
            "Do NOT cite any accuracy metrics from this model as validated performance."
        ),
    }
    meta_path = os.path.join(MODEL_DIR, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved → {meta_path}")

    return model


if __name__ == "__main__":
    train_model()
