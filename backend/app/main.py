"""
LandslideGuard — FastAPI Backend
AI-Based Early Warning & Landslide Risk Monitoring System for Northeast India

DEMO MODEL — NOT AN OPERATIONAL FORECAST
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.ml.model import RiskModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("landslide_guard")

# Global model instance
risk_model: RiskModel | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load ML model, verify external services."""
    global risk_model
    settings = get_settings()

    # Load ML model
    try:
        risk_model = RiskModel(settings.model_path, settings.model_version)
        risk_model.load()
        logger.info(f"ML model loaded: {settings.model_version} (DEMO MODEL)")
    except Exception as e:
        logger.warning(f"ML model not loaded: {e}. Risk predictions will be unavailable.")
        risk_model = None

    # Verify Supabase connectivity
    try:
        from app.db import check_supabase_health
        health = await check_supabase_health()
        logger.info(f"Supabase: {health['status']}")
    except Exception as e:
        logger.warning(f"Supabase not reachable: {e}")

    logger.info("LandslideGuard backend started")
    yield
    logger.info("LandslideGuard backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="LandslideGuard API",
        description=(
            "AI-Based Early Warning & Landslide Risk Monitoring System for Northeast India. "
            "⚠ DEMONSTRATION MODEL — Not an operational forecast."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    origins = [o.strip() for o in settings.cors_allowed_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and register routers
    from app.api.health import router as health_router
    from app.api.weather import router as weather_router
    from app.api.risk import router as risk_router
    from app.api.map import router as map_router
    from app.api.alerts import router as alerts_router
    from app.api.field_reports import router as field_reports_router
    from app.api.incidents import router as incidents_router
    from app.api.data_sources import router as data_sources_router
    from app.api.simulation import router as simulation_router

    app.include_router(health_router)
    app.include_router(weather_router, prefix="/api/v1")
    app.include_router(risk_router, prefix="/api/v1")
    app.include_router(map_router, prefix="/api/v1")
    app.include_router(alerts_router, prefix="/api/v1")
    app.include_router(field_reports_router, prefix="/api/v1")
    app.include_router(incidents_router, prefix="/api/v1")
    app.include_router(data_sources_router, prefix="/api/v1")
    app.include_router(simulation_router, prefix="/api/v1")

    return app


app = create_app()
