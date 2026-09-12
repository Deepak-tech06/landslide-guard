"""Weather API — real rainfall data from Open-Meteo."""

from fastapi import APIRouter, Query
from app.services.weather_service import fetch_rainfall
from app.services.data_source_monitor import update_source_status
import time

router = APIRouter(tags=["weather"])


@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
):
    """
    Fetch current rainfall data for given coordinates.
    Source: Open-Meteo (LIVE when available).
    """
    start = time.time()
    result = await fetch_rainfall(lat, lng)
    latency = int((time.time() - start) * 1000)

    # Update data source status
    if result["status"] == "LIVE":
        update_source_status("open_meteo", "LIVE", latency_ms=latency)
    else:
        update_source_status("open_meteo", result["status"], error=result.get("error"))

    return result
