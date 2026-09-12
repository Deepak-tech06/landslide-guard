"""Alert API — warning generation and management."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.auth import require_authority, require_citizen

router = APIRouter(tags=["alerts"])

# In-memory store (backed by Supabase when connected)
_alerts: list = []
_field_tasks: list = []


class AlertCreateRequest(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    risk_score: float
    risk_level: str
    risk_drivers: Optional[list] = None
    risk_statement: Optional[str] = None


@router.post("/alerts")
async def create_alert(req: AlertCreateRequest, user: dict = Depends(require_authority)):
    """
    Generate a warning alert.
    One click: creates alert + field verification task.
    """
    now = datetime.now(timezone.utc)

    # Determine severity from risk level
    severity_map = {
        "LOW": "ADVISORY",
        "MODERATE": "WATCH",
        "HIGH": "WARNING",
        "VERY_HIGH": "SEVERE",
        "CRITICAL": "CRITICAL",
    }
    severity = severity_map.get(req.risk_level, "WARNING")

    alert = {
        "id": str(uuid.uuid4()),
        "location_name": req.location_name,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "risk_score": req.risk_score,
        "risk_level": req.risk_level,
        "severity": severity,
        "risk_drivers": req.risk_drivers,
        "risk_statement": req.risk_statement,
        "status": "GENERATED",
        "generated_by": user["id"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    _alerts.append(alert)

    # Auto-create field verification task
    task = {
        "id": str(uuid.uuid4()),
        "alert_id": alert["id"],
        "location_name": req.location_name,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "task_type": "FIELD_VERIFICATION",
        "priority": "CRITICAL" if req.risk_level in ("VERY_HIGH", "CRITICAL") else "HIGH",
        "status": "PENDING",
        "created_at": now.isoformat(),
    }
    _field_tasks.append(task)

    return {
        "alert": alert,
        "field_task": task,
        "message": f"⚠ {severity} alert generated for {req.location_name}. Field verification task created.",
    }


@router.get("/alerts")
async def list_alerts():
    """List all alerts, newest first."""
    sorted_alerts = sorted(_alerts, key=lambda a: a["created_at"], reverse=True)
    return {"alerts": sorted_alerts, "count": len(sorted_alerts)}


@router.get("/field-tasks")
async def list_field_tasks():
    """List field verification tasks."""
    return {"tasks": _field_tasks, "count": len(_field_tasks)}
