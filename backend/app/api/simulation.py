"""Simulation API — Shillong Storm Scenario demo."""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import asyncio

from app.auth import require_authority

router = APIRouter(tags=["simulation"])


@router.post("/simulation/shillong-storm")
async def run_shillong_storm_scenario(user: dict = Depends(require_authority)):
    """
    Run the Shillong Storm Scenario — a demonstration simulation.

    ⚠ SIMULATION MODE — All data in this scenario is simulated.

    Sequence: NORMAL → RAINFALL↑ → SOIL↑ → RISK↑ → HOTSPOT →
              ROAD RISK → CRITICAL → WARNING → FIELD TASK → VERIFIED
    """
    from app.main import risk_model
    from app.services.risk_engine import build_features, generate_risk_statement
    from app.services.explainability import get_explanation
    from app.api.alerts import _alerts, _field_tasks
    from app.api.field_reports import _field_reports
    import uuid

    now = datetime.now(timezone.utc)

    # Shillong coordinates
    lat, lng = 25.5788, 91.8933
    location_name = "Shillong Sector"

    steps = []

    # Step 1: Normal conditions
    normal_features = {
        "rainfall_1h": 2.0, "rainfall_3h": 8.0, "rainfall_6h": 15.0,
        "rainfall_24h": 35.0, "rainfall_72h": 80.0,
        "soil_moisture": 0.45, "slope": 28.5, "elevation": 1496,
        "geology_susceptibility": 0.82, "drainage_density": 0.65,
        "historical_landslide_density": 0.5, "distance_to_historical_landslide": 15.0,
    }
    if risk_model and risk_model.is_loaded():
        pred_normal = risk_model.predict(normal_features)
    else:
        pred_normal = {"risk_score": 25, "risk_level": "LOW", "confidence": 0.7, "top_drivers": []}
    steps.append({"step": 1, "name": "NORMAL CONDITIONS", "risk_score": pred_normal["risk_score"], "risk_level": pred_normal["risk_level"]})

    # Step 2: Rainfall increases (heavy monsoon event)
    storm_features = {
        **normal_features,
        "rainfall_1h": 28.0, "rainfall_3h": 65.0, "rainfall_6h": 110.0,
        "rainfall_24h": 178.0, "rainfall_72h": 326.0,
        "soil_moisture": 0.81,
    }
    if risk_model and risk_model.is_loaded():
        pred_storm = risk_model.predict(storm_features)
    else:
        pred_storm = {"risk_score": 82, "risk_level": "VERY_HIGH", "confidence": 0.81, "top_drivers": []}
    steps.append({"step": 2, "name": "RAINFALL INCREASES", "risk_score": pred_storm["risk_score"], "risk_level": pred_storm["risk_level"]})

    # Step 3: Soil saturation
    steps.append({"step": 3, "name": "SOIL MOISTURE INCREASES", "soil_moisture": 0.81})

    # Step 4: Risk score rises
    steps.append({"step": 4, "name": "RISK SCORE RISES", "risk_score": pred_storm["risk_score"], "risk_level": pred_storm["risk_level"]})

    # Step 5: Hotspot appears
    steps.append({"step": 5, "name": "HOTSPOT APPEARS", "hotspot": location_name})

    # Step 6: Road risk increases
    steps.append({"step": 6, "name": "ROAD RISK INCREASES", "affected_roads": ["NH6 (Jorabat–Shillong)", "NH44 (Shillong–Cherrapunji)"]})

    # Step 7: Generate warning
    explanation = get_explanation(pred_storm) if risk_model and risk_model.is_loaded() else {"drivers": []}
    risk_statement = generate_risk_statement(pred_storm) if risk_model and risk_model.is_loaded() else "Estimated risk is elevated."

    alert = {
        "id": str(uuid.uuid4()),
        "location_name": location_name,
        "latitude": lat, "longitude": lng,
        "risk_score": pred_storm["risk_score"],
        "risk_level": pred_storm["risk_level"],
        "severity": "SEVERE",
        "risk_drivers": pred_storm.get("top_drivers", []),
        "risk_statement": risk_statement,
        "status": "GENERATED",
        "generated_by": user["id"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "simulation": True,
    }
    _alerts.append(alert)

    task = {
        "id": str(uuid.uuid4()),
        "alert_id": alert["id"],
        "location_name": location_name,
        "latitude": lat, "longitude": lng,
        "task_type": "FIELD_VERIFICATION",
        "priority": "CRITICAL",
        "status": "PENDING",
        "created_at": now.isoformat(),
        "simulation": True,
    }
    _field_tasks.append(task)
    steps.append({"step": 7, "name": "WARNING GENERATED", "alert_id": alert["id"]})

    # Step 8: Field report submitted
    report = {
        "id": str(uuid.uuid4()),
        "latitude": lat, "longitude": lng,
        "incident_type": "landslide_observed",
        "severity": "HIGH",
        "description": "SIMULATION: Slope movement observed near NH6 km 42, debris on road shoulder",
        "reporter_id": user["id"],
        "reporter_role": "FIELD_TEAM",
        "status": "SUBMITTED",
        "created_at": now.isoformat(),
        "simulation": True,
    }
    _field_reports.append(report)
    steps.append({"step": 8, "name": "FIELD REPORT SUBMITTED", "report_id": report["id"]})

    # Step 9: Incident verified
    report["status"] = "VERIFIED"
    report["verified_by"] = user["id"]
    report["verified_at"] = now.isoformat()
    report["verification_notes"] = "SIMULATION: Verified — slope failure confirmed at location"
    steps.append({"step": 9, "name": "INCIDENT VERIFIED", "status": "VERIFIED"})

    return {
        "simulation": True,
        "mode": "SIMULATION MODE",
        "scenario": "Shillong Storm Scenario",
        "note": "⚠ All data in this simulation is synthetic — not real observations",
        "location": {"name": location_name, "lat": lat, "lng": lng},
        "steps": steps,
        "alert": alert,
        "field_task": task,
        "field_report": report,
        "risk_prediction": pred_storm,
        "explanation": explanation,
    }
