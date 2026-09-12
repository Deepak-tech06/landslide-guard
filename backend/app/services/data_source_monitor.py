"""
Data source monitor — tracks health/status of all external sources.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("landslide_guard.data_sources")


# In-memory status cache (backed by Supabase when available)
_status_cache: dict = {}


def update_source_status(provider: str, status: str, latency_ms: int = None, error: str = None):
    """Update a data source status."""
    _status_cache[provider] = {
        "provider": provider,
        "status": status,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "latency_ms": latency_ms,
        "error": error,
    }


def get_all_statuses() -> list:
    """Get status of all data sources."""
    # Defaults for sources that haven't reported yet
    defaults = {
        "open_meteo": {"provider": "open_meteo", "display_name": "Open-Meteo Rainfall", "status": "UNKNOWN", "label": "LIVE"},
        "osm_basemap": {"provider": "osm_basemap", "display_name": "OSM Basemap", "status": "LIVE", "label": "LIVE"},
        "osm_roads": {"provider": "osm_roads", "display_name": "Road Network (OSM)", "status": "LIVE", "label": "LIVE GIS DATA", "note": "Not live traffic/closures"},
        "road_risk": {"provider": "road_risk", "display_name": "Road Risk", "status": "SIMULATED", "label": "CALCULATED", "note": "Derived from AI risk overlay"},
        "historical_landslides": {"provider": "historical_landslides", "display_name": "Historical Landslides", "status": "LIVE", "label": "SOURCE-LABELLED"},
        "ai_model": {"provider": "ai_model", "display_name": "AI Risk Engine", "status": "SIMULATED", "label": "DEMO MODEL", "note": "Synthetic training data"},
        "soil_moisture": {"provider": "soil_moisture", "display_name": "Soil Moisture", "status": "SIMULATED", "label": "SIMULATED"},
        "ground_movement": {"provider": "ground_movement", "display_name": "Ground Movement", "status": "SIMULATED", "label": "SIMULATED"},
        "satellite_sar": {"provider": "satellite_sar", "display_name": "Satellite/SAR", "status": "UNAVAILABLE", "label": "NOT YET INTEGRATED"},
    }

    result = []
    for provider, default in defaults.items():
        cached = _status_cache.get(provider, {})
        entry = {**default, **cached}
        result.append(entry)

    return result
