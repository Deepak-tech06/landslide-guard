"""Field reports API — citizen/field team incident submissions."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.auth import require_authority, require_citizen

router = APIRouter(tags=["field-reports"])

# In-memory store
_field_reports: list = []

INCIDENT_TYPES = [
    "landslide_observed",
    "road_obstruction",
    "slope_crack",
    "debris_flow",
    "drainage_blockage",
    "unusual_ground_movement",
    "other",
]


class FieldReportCreate(BaseModel):
    latitude: float
    longitude: float
    incident_type: str
    severity: Optional[str] = "MODERATE"
    description: Optional[str] = None
    photo_url: Optional[str] = None


@router.post("/field-reports")
async def submit_field_report(req: FieldReportCreate, user: dict = Depends(require_citizen)):
    """Submit a field/citizen incident report."""
    if req.incident_type not in INCIDENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid incident_type. Must be one of: {INCIDENT_TYPES}")

    now = datetime.now(timezone.utc)
    report = {
        "id": str(uuid.uuid4()),
        "latitude": req.latitude,
        "longitude": req.longitude,
        "incident_type": req.incident_type,
        "severity": req.severity,
        "description": req.description,
        "photo_url": req.photo_url,
        "reporter_id": user["id"],
        "reporter_role": user["role"],
        "status": "SUBMITTED",
        "created_at": now.isoformat(),
    }
    _field_reports.append(report)

    return {"report": report, "message": "Field report submitted successfully."}


@router.get("/field-reports")
async def list_field_reports():
    """List all field reports, newest first."""
    sorted_reports = sorted(_field_reports, key=lambda r: r["created_at"], reverse=True)
    return {"reports": sorted_reports, "count": len(sorted_reports)}


@router.patch("/field-reports/{report_id}")
async def update_field_report(
    report_id: str, 
    status: Optional[str] = None, 
    notes: Optional[str] = None,
    user: dict = Depends(require_authority)
):
    """Update a field report (e.g., change status)."""
    for report in _field_reports:
        if report["id"] == report_id:
            if status:
                report["status"] = status
            if notes:
                report["verification_notes"] = notes
            
            if status == "VERIFIED":
                report["verified_by"] = user["id"]
                report["verified_at"] = datetime.now(timezone.utc).isoformat()
                
            report["updated_at"] = datetime.now(timezone.utc).isoformat()
            return {"report": report}

    raise HTTPException(status_code=404, detail="Field report not found")
