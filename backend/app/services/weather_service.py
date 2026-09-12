"""
Weather service — Open-Meteo integration for real rainfall data.

Fetches current/hourly precipitation and calculates rolling accumulations.
Handles API failures gracefully with CACHED/ERROR status.
"""

import httpx
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings

logger = logging.getLogger("landslide_guard.weather")

# Open-Meteo API — no key required for non-commercial use
HOURLY_PARAMS = "precipitation"


import time

_WEATHER_CACHE = {}
CACHE_TTL = 300  # 5 minutes

def _get_cache_key(lat: float, lng: float) -> str:
    return f"{lat:.2f},{lng:.2f}"

async def fetch_rainfall(lat: float, lng: float) -> dict:
    """
    Fetch current rainfall data from Open-Meteo.

    Returns dict with precipitation values, rolling accumulations,
    provider info, and data status (LIVE/CACHED/ERROR).
    """
    cache_key = _get_cache_key(lat, lng)
    now_time = time.time()
    
    if cache_key in _WEATHER_CACHE:
        cached_data, timestamp = _WEATHER_CACHE[cache_key]
        if now_time - timestamp < CACHE_TTL:
            res = cached_data.copy()
            res["status"] = "CACHED"
            return res

    settings = get_settings()
    base_url = settings.open_meteo_base_url.rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    url = f"{base_url}/v1/forecast"
    logger.info(f"Weather service requesting Open-Meteo URL: {url}")
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": HOURLY_PARAMS,
        "timezone": "Asia/Kolkata",
        "forecast_days": 1,
        "past_days": 3,
    }

    request_time = datetime.now(timezone.utc)

    try:
        headers = {"User-Agent": "LandslideGuard-Demo/1.0 (Contact: demo@landslideguard.in)"}
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        precip = hourly.get("precipitation", [])

        if not times or not precip:
            if cache_key in _WEATHER_CACHE:
                cached_data, _ = _WEATHER_CACHE[cache_key]
                res = cached_data.copy()
                res["status"] = "ERROR (Using stale cache)"
                return res
            return _error_result(lat, lng, request_time, "Empty response from Open-Meteo")

        # Find current hour index (closest to now)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
        current_idx = None
        for i, t in enumerate(times):
            if t >= now_str:
                current_idx = i
                break
        if current_idx is None:
            current_idx = len(times) - 1

        # Rolling accumulations
        precipitation_1h = _safe_sum(precip, current_idx, 1)
        precipitation_3h = _safe_sum(precip, current_idx, 3)
        precipitation_6h = _safe_sum(precip, current_idx, 6)
        precipitation_24h = _safe_sum(precip, current_idx, 24)
        precipitation_72h = _safe_sum(precip, current_idx, 72)

        observation_time = times[current_idx] if current_idx < len(times) else times[-1]

        result = {
            "latitude": lat,
            "longitude": lng,
            "observation_time": observation_time,
            "precipitation_1h": round(precipitation_1h, 2),
            "precipitation_3h": round(precipitation_3h, 2),
            "precipitation_6h": round(precipitation_6h, 2),
            "precipitation_24h": round(precipitation_24h, 2),
            "precipitation_72h": round(precipitation_72h, 2),
            "provider": "Open-Meteo",
            "status": "LIVE",
            "request_time": request_time.isoformat(),
            "units": "mm",
        }
        
        _WEATHER_CACHE[cache_key] = (result.copy(), now_time)
        return result

    except httpx.TimeoutException:
        logger.warning(f"Open-Meteo timeout for ({lat}, {lng})")
        if cache_key in _WEATHER_CACHE:
            cached_data, _ = _WEATHER_CACHE[cache_key]
            res = cached_data.copy()
            res["status"] = "ERROR (Using stale cache)"
            return res
        return _error_result(lat, lng, request_time, "API timeout")
    except httpx.HTTPStatusError as e:
        logger.warning(f"Open-Meteo HTTP error: {e.response.status_code}")
        status_text = "RATE_LIMITED/ERROR" if e.response.status_code == 429 else f"HTTP {e.response.status_code}"
        if cache_key in _WEATHER_CACHE:
            cached_data, _ = _WEATHER_CACHE[cache_key]
            res = cached_data.copy()
            res["status"] = status_text
            return res
        return _error_result(lat, lng, request_time, status_text)
    except Exception as e:
        logger.error(f"Open-Meteo error: {e}")
        if cache_key in _WEATHER_CACHE:
            cached_data, _ = _WEATHER_CACHE[cache_key]
            res = cached_data.copy()
            res["status"] = "ERROR (Using stale cache)"
            return res
        return _error_result(lat, lng, request_time, str(e))


def _safe_sum(precip: list, current_idx: int, hours: int) -> float:
    """Sum precipitation over the last N hours from current index."""
    start = max(0, current_idx - hours + 1)
    end = current_idx + 1
    values = precip[start:end]
    return sum(v for v in values if v is not None)


def _error_result(lat: float, lng: float, request_time: datetime, error: str) -> dict:
    """Return an error/unavailable result."""
    return {
        "latitude": lat,
        "longitude": lng,
        "observation_time": None,
        "precipitation_1h": None,
        "precipitation_3h": None,
        "precipitation_6h": None,
        "precipitation_24h": None,
        "precipitation_72h": None,
        "provider": "Open-Meteo",
        "status": "ERROR",
        "error": error,
        "request_time": request_time.isoformat(),
        "units": "mm",
    }
