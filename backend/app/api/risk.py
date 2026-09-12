"""Risk prediction API — ML model inference with explainability."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.weather_service import fetch_rainfall
from app.services.risk_engine import build_features, generate_risk_statement
from app.services.explainability import get_explanation

router = APIRouter(tags=["risk"])


class RiskPredictRequest(BaseModel):
    latitude: float
    longitude: float
    # Optional overrides (for simulation/manual input)
    rainfall_24h: Optional[float] = None
    rainfall_72h: Optional[float] = None
    soil_moisture: Optional[float] = None
    slope: Optional[float] = None
    geology_susceptibility: Optional[float] = None
    historical_proximity: Optional[float] = None


@router.post("/risk/predict")
async def predict_risk(req: RiskPredictRequest):
    """
    Run AI risk prediction for given coordinates.

    ⚠ DEMO MODEL — Prototype risk estimate, not an operational forecast.
    """
    from app.main import risk_model

    if not risk_model or not risk_model.is_loaded():
        raise HTTPException(status_code=503, detail="ML model not loaded")

    # Step 1: Fetch live weather
    weather = await fetch_rainfall(req.latitude, req.longitude)

    # Step 2: Get terrain data for this location
    terrain = _get_terrain_for_location(req.latitude, req.longitude)

    # Step 3: Build features
    features = build_features(weather, terrain)

    # Apply manual overrides if provided
    if req.rainfall_24h is not None:
        features["rainfall_24h"] = req.rainfall_24h
    if req.rainfall_72h is not None:
        features["rainfall_72h"] = req.rainfall_72h
    if req.soil_moisture is not None:
        features["soil_moisture"] = req.soil_moisture
    if req.slope is not None:
        features["slope"] = req.slope
    if req.geology_susceptibility is not None:
        features["geology_susceptibility"] = req.geology_susceptibility

    # Step 4: Run ML prediction
    prediction = risk_model.predict(features)

    # Step 5: Generate explanation
    explanation = get_explanation(prediction)
    risk_statement = generate_risk_statement(prediction)

    return {
        **prediction,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "weather": {
            "status": weather.get("status"),
            "provider": weather.get("provider"),
            "precipitation_24h": weather.get("precipitation_24h"),
            "precipitation_72h": weather.get("precipitation_72h"),
        },
        "explanation": explanation,
        "risk_statement": risk_statement,
        "model_note": "⚠ DEMONSTRATION MODEL — Prototype risk estimate, not an operational forecast.",
    }


def _get_terrain_for_location(lat: float, lng: float) -> dict:
    """Look up terrain data for closest grid cell or location."""
    import json
    import os
    import math

    # Load locations
    loc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ner_locations.json")
    with open(loc_path) as f:
        locations = json.load(f)

    # Find closest location
    best = None
    best_dist = float("inf")
    for loc in locations:
        dist = math.sqrt((lat - loc["lat"])**2 + (lng - loc["lng"])**2)
        if dist < best_dist:
            best_dist = dist
            best = loc

    if best and best_dist < 1.0:  # Within ~1 degree
        return {
            "slope": best.get("slope", 20),
            "elevation": best.get("elevation", 500),
            "geology_susceptibility": best.get("geology_susceptibility", 0.5),
            "drainage_density": best.get("drainage", 0.5),
            "historical_landslide_density": 0,
            "distance_to_historical_landslide": 50,
        }

    # Default terrain values for unknown locations
    return {
        "slope": 20,
        "elevation": 500,
        "geology_susceptibility": 0.5,
        "drainage_density": 0.5,
        "historical_landslide_density": 0,
        "distance_to_historical_landslide": 100,
    }


@router.get("/risk/{location_id}")
async def get_risk_by_location(location_id: str):
    """Get the latest risk prediction for a specific location."""
    # For now, use location data to run a fresh prediction
    import json, os
    loc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ner_locations.json")
    with open(loc_path) as f:
        locations = json.load(f)

    loc = None
    for l in locations:
        if l["name"].lower().replace(" ", "_") == location_id.lower():
            loc = l
            break

    if not loc:
        raise HTTPException(status_code=404, detail=f"Location '{location_id}' not found")

    req = RiskPredictRequest(latitude=loc["lat"], longitude=loc["lng"])
    return await predict_risk(req)
