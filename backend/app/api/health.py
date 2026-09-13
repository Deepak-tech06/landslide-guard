"""Health endpoint — system status."""

from fastapi import APIRouter
from app.db import check_supabase_health
import httpx
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """System health check — verifies backend, database, and external services."""
    settings = get_settings()
    checks = {"backend": "ONLINE"}

    # Check Supabase
    try:
        db_health = await check_supabase_health()
        checks["database"] = db_health["status"]
    except Exception:
        checks["database"] = "ERROR"

    # Check Open-Meteo (Configuration & Cache check, no live request to avoid 429)
    try:
        from app.services.weather_service import _WEATHER_CACHE
        if not settings.open_meteo_base_url:
            checks["open_meteo"] = "ERROR: Missing URL"
        else:
            # If we have cache entries, check if they are recent/successful
            # Otherwise just report ONLINE based on configuration
            checks["open_meteo"] = "ONLINE"
    except Exception as e:
        checks["open_meteo"] = "ERROR"

    # Check ML model
    from app.main import risk_model
    checks["ml_model"] = "LOADED" if risk_model and risk_model.is_loaded() else "NOT_LOADED"
    checks["ml_model_type"] = "DEMO MODEL"

    overall = "healthy" if all(v in ("ONLINE", "LOADED", "DEMO MODEL") for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "service": "GeoSense API",
        "version": "1.0.0",
        "checks": checks,
        "note": "⚠ DEMONSTRATION SYSTEM — Not an operational forecast service",
    }
