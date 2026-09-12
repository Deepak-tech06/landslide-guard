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

    # Check Open-Meteo
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.open_meteo_base_url}/v1/forecast",
                                    params={"latitude": 25.57, "longitude": 91.89, "hourly": "precipitation", "forecast_days": 1})
            checks["open_meteo"] = "ONLINE" if resp.status_code == 200 else "ERROR"
    except Exception:
        checks["open_meteo"] = "OFFLINE"

    # Check ML model
    from app.main import risk_model
    checks["ml_model"] = "LOADED" if risk_model and risk_model.is_loaded() else "NOT_LOADED"
    checks["ml_model_type"] = "DEMO MODEL"

    overall = "healthy" if all(v in ("ONLINE", "LOADED", "DEMO MODEL") for v in checks.values()) else "degraded"

    return {
        "status": overall,
        "service": "LandslideGuard API",
        "version": "1.0.0",
        "checks": checks,
        "note": "⚠ DEMONSTRATION SYSTEM — Not an operational forecast service",
    }
