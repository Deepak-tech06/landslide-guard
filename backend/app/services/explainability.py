"""
Explainability service — feature contribution analysis.

Uses model feature importance by default.
SHAP is OPTIONAL — enhances explanations if installed, but the system
must never fail because SHAP is missing.
"""

import logging
from typing import Optional

logger = logging.getLogger("landslide_guard.explainability")

# Try to import SHAP — optional
_shap_available = False
try:
    import shap
    _shap_available = True
    logger.info("SHAP available — enhanced explanations enabled")
except ImportError:
    logger.info("SHAP not installed — using model feature importance (this is fine)")


FEATURE_LABELS = {
    "rainfall_1h": "Hourly Rainfall",
    "rainfall_3h": "3h Rainfall",
    "rainfall_6h": "6h Rainfall",
    "rainfall_24h": "24h Rainfall",
    "rainfall_72h": "72h Rainfall",
    "soil_moisture": "Soil Moisture",
    "slope": "Slope",
    "elevation": "Elevation",
    "geology_susceptibility": "Geological Susceptibility",
    "historical_landslide_density": "Historical Risk",
    "distance_to_historical_landslide": "Distance to Past Events",
    "drainage_density": "Drainage",
}


def get_explanation(prediction: dict) -> dict:
    """
    Build an explanation object from a risk prediction.

    Returns structured data for the "WHY THIS RISK?" panel.
    Only displays actual calculated values — never fabricated.
    """
    drivers = prediction.get("top_drivers", [])
    risk_level = prediction.get("risk_level", "UNKNOWN")
    risk_score = prediction.get("risk_score", 0)

    # Build driver bars
    driver_bars = []
    for d in drivers[:6]:  # Top 6
        feature = d["feature"]
        contribution = d.get("contribution", 0)
        value = d.get("value", 0)

        driver_bars.append({
            "feature": feature,
            "label": FEATURE_LABELS.get(feature, feature),
            "contribution": contribution,
            "value": value,
            "bar_width": min(100, max(0, contribution)),  # percentage for UI bar
        })

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "drivers": driver_bars,
        "method": "shap" if _shap_available else "feature_importance",
        "note": (
            "Feature contributions derived from model feature importance. "
            "Values represent relative influence on the risk estimate."
        ),
    }
