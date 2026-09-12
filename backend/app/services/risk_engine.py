"""
Risk engine service — combines weather + terrain + ML model.

Feature engineering pipeline that feeds the risk model and returns
explainable risk predictions.
"""

import logging
from typing import Optional

logger = logging.getLogger("landslide_guard.risk_engine")


def build_features(
    weather: dict,
    terrain: dict,
    historical: Optional[dict] = None,
) -> dict:
    """
    Build ML feature vector from weather, terrain, and historical data.

    Missing features are left as None — the model handles defaults.
    """
    features = {}

    # Rainfall features from weather service
    if weather and weather.get("status") == "LIVE":
        features["rainfall_1h"] = weather.get("precipitation_1h")
        features["rainfall_3h"] = weather.get("precipitation_3h")
        features["rainfall_6h"] = weather.get("precipitation_6h")
        features["rainfall_24h"] = weather.get("precipitation_24h")
        features["rainfall_72h"] = weather.get("precipitation_72h")
    elif weather and weather.get("status") == "CACHED":
        features["rainfall_1h"] = weather.get("precipitation_1h")
        features["rainfall_3h"] = weather.get("precipitation_3h")
        features["rainfall_6h"] = weather.get("precipitation_6h")
        features["rainfall_24h"] = weather.get("precipitation_24h")
        features["rainfall_72h"] = weather.get("precipitation_72h")

    # Terrain features
    if terrain:
        features["slope"] = terrain.get("slope")
        features["elevation"] = terrain.get("elevation")
        features["geology_susceptibility"] = terrain.get("geology_susceptibility")
        features["drainage_density"] = terrain.get("drainage_density")
        features["historical_landslide_density"] = terrain.get("historical_landslide_density", 0)
        features["distance_to_historical_landslide"] = terrain.get("distance_to_historical_landslide", 999)

    # Soil moisture — simulated for MVP
    if "soil_moisture" not in features:
        # Estimate from rainfall if available
        r24 = features.get("rainfall_24h")
        if r24 is not None:
            features["soil_moisture"] = min(0.95, 0.3 + (r24 / 300) * 0.6)
        else:
            features["soil_moisture"] = None  # will use model default

    return features


def generate_risk_statement(prediction: dict) -> str:
    """
    Generate a human-readable risk statement from prediction results.

    Does NOT claim causation — uses "estimated" and "contributing" language.
    """
    risk_level = prediction.get("risk_level", "UNKNOWN")
    risk_score = prediction.get("risk_score", 0)
    drivers = prediction.get("top_drivers", [])

    if not drivers:
        return f"Estimated landslide risk is {risk_level} (score: {risk_score}/100)."

    # Top 3 contributing factors
    top_names = [_human_feature_name(d["feature"]) for d in drivers[:3]]

    if risk_level in ("VERY_HIGH", "CRITICAL"):
        return (
            f"Estimated landslide risk is {risk_level}. "
            f"Primary contributing factors: {', '.join(top_names)}. "
            f"Prioritize field verification and monitor vulnerable road sections."
        )
    elif risk_level == "HIGH":
        return (
            f"Estimated landslide risk is {risk_level}. "
            f"Key factors: {', '.join(top_names)}. "
            f"Increased monitoring recommended."
        )
    elif risk_level == "MODERATE":
        return (
            f"Estimated landslide risk is {risk_level}. "
            f"Monitor conditions, particularly {top_names[0].lower()}."
        )
    else:
        return f"Estimated landslide risk is {risk_level} (score: {risk_score}/100)."


def _human_feature_name(feature: str) -> str:
    """Convert feature name to human-readable label."""
    names = {
        "rainfall_1h": "hourly rainfall",
        "rainfall_3h": "3-hour rainfall",
        "rainfall_6h": "6-hour rainfall",
        "rainfall_24h": "24-hour cumulative rainfall",
        "rainfall_72h": "72-hour cumulative rainfall",
        "soil_moisture": "soil moisture/saturation",
        "slope": "terrain slope",
        "elevation": "elevation",
        "geology_susceptibility": "geological susceptibility",
        "historical_landslide_density": "historical landslide proximity",
        "distance_to_historical_landslide": "distance to past events",
        "drainage_density": "drainage conditions",
    }
    return names.get(feature, feature.replace("_", " "))
