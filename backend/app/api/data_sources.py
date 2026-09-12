"""Data sources status API."""

from fastapi import APIRouter
from app.services.data_source_monitor import get_all_statuses

router = APIRouter(tags=["data-sources"])


@router.get("/data-sources/status")
async def get_data_source_status():
    """
    Get health/status of all external data sources.

    Status labels:
    - LIVE: currently connected and fetching real data
    - CACHED: previously fetched real data
    - SIMULATED: generated/demo data
    - UNAVAILABLE: source cannot be reached
    - ERROR: source returned an error
    """
    statuses = get_all_statuses()
    online_count = sum(1 for s in statuses if s.get("status") in ("LIVE", "SIMULATED"))

    return {
        "sources": statuses,
        "total": len(statuses),
        "online": online_count,
        "summary": f"{online_count}/{len(statuses)} sources available",
    }
