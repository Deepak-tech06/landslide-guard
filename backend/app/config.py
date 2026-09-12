"""LandslideGuard Backend Configuration — loaded from environment variables."""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Open-Meteo
    open_meteo_base_url: str = "https://api.open-meteo.com"

    # CORS
    cors_allowed_origins: str = "http://localhost:5173"

    # ML Model
    model_path: str = os.path.join(os.path.dirname(__file__), "ml", "model_artifacts", "risk_model.joblib")
    model_version: str = "v1-demo"

    # Risk thresholds (configurable, require calibration)
    risk_threshold_low: int = 0
    risk_threshold_moderate: int = 30
    risk_threshold_high: int = 50
    risk_threshold_very_high: int = 70
    risk_threshold_critical: int = 85

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
