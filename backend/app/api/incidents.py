"""Incident verification API — authority workflow."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(tags=["incidents"])


class VerifyRequest(BaseModel):
    action: str  # VERIFY / DISMISS / NEEDS_MORE_EVIDENCE
    notes: Optional[str] = None
    verified_by: Optional[str] = "AUTHORITY"


@router.get("/incidents")
async def list_incidents():
    """List all field reports as incidents for verification."""
    from app.api.field_reports import _field_reports
    return {
        "incidents": _field_reports,
        "count": len(_field_reports),
    }


@router.post("/incidents/{report_id}/verify")
async def verify_incident(report_id: str, req: VerifyRequest):
    """
    Authority verification of a field report.
    VERIFY → incident confirmed, feeds back to model validation dataset.
    DISMISS → false positive.
    NEEDS_MORE_EVIDENCE → request additional field data.

    Note: Unverified citizen reports do NOT automatically retrain the model.
    """
    from app.api.field_reports import _field_reports

    for report in _field_reports:
        if report["id"] == report_id:
            now = datetime.now(timezone.utc)

            if req.action == "VERIFY":
                report["status"] = "VERIFIED"
            elif req.action == "DISMISS":
                report["status"] = "DISMISSED"
            elif req.action == "NEEDS_MORE_EVIDENCE":
                report["status"] = "NEEDS_MORE_EVIDENCE"
            else:
                raise HTTPException(status_code=400, detail="action must be VERIFY, DISMISS, or NEEDS_MORE_EVIDENCE")

            report["verification_notes"] = req.notes
            report["verified_by"] = req.verified_by
            report["verified_at"] = now.isoformat()

            return {
                "incident": report,
                "message": f"Incident {req.action.lower()}d.",
            }

    raise HTTPException(status_code=404, detail="Incident not found")
