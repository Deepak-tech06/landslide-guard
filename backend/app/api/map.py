"""Map data API — GeoJSON layers for frontend map rendering."""

import json
import os
from fastapi import APIRouter

router = APIRouter(tags=["map"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


@router.get("/map/risk-cells")
async def get_risk_cells():
    """Return risk grid cells as GeoJSON for map rendering."""
    cells = _load_json("ner_risk_grid.json")

    features = []
    for cell in cells:
        features.append({
            "type": "Feature",
            "properties": {
                "cell_id": cell["cell_id"],
                "elevation": cell.get("elevation"),
                "slope": cell.get("slope"),
                "geology_susceptibility": cell.get("geology_susceptibility"),
                "drainage_density": cell.get("drainage_density"),
                "data_source": cell.get("data_source", "SIMULATED"),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [cell["bounds"]],
            },
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/map/roads")
async def get_roads():
    """Return NER road corridors as GeoJSON."""
    return _load_json("ner_roads.geojson")


@router.get("/map/landslides")
async def get_historical_landslides():
    """
    Return historical landslide events as GeoJSON.
    Each feature includes provenance (source, source_type, verified).
    """
    events = _load_json("historical_landslides.json")

    features = []
    for event in events:
        features.append({
            "type": "Feature",
            "properties": {
                "name": event["name"],
                "event_date": event.get("event_date"),
                "description": event.get("description"),
                "severity": event.get("severity"),
                "source": event["source"],
                "source_url": event.get("source_url"),
                "source_type": event["source_type"],
                "verified": event["verified"],
            },
            "geometry": {
                "type": "Point",
                "coordinates": [event["lng"], event["lat"]],
            },
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/map/settlements")
async def get_settlements():
    """Return NER settlements as GeoJSON."""
    settlements = _load_json("settlements.json")

    features = []
    for s in settlements:
        features.append({
            "type": "Feature",
            "properties": {
                "name": s["name"],
                "state": s.get("state"),
                "population": s.get("population"),
            },
            "geometry": {
                "type": "Point",
                "coordinates": [s["lng"], s["lat"]],
            },
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/map/hotspots")
async def get_hotspots():
    """
    Return current risk hotspots.
    These are calculated clusters of elevated risk — currently based on
    static susceptibility data. With live predictions they update dynamically.
    """
    locations = _load_json("ner_locations.json")

    # Identify high-susceptibility locations as prototype hotspots
    hotspots = []
    for i, loc in enumerate(locations):
        susceptibility = loc.get("geology_susceptibility", 0)
        if susceptibility >= 0.7:
            hotspots.append({
                "id": f"hotspot_{i+1:02d}",
                "name": f"{loc['name']} Sector",
                "latitude": loc["lat"],
                "longitude": loc["lng"],
                "risk_level": "VERY_HIGH" if susceptibility >= 0.8 else "HIGH",
                "susceptibility": susceptibility,
                "slope": loc.get("slope", 20),
                "state": loc.get("state"),
                "data_source": "SIMULATED",
            })

    return {"hotspots": hotspots, "count": len(hotspots)}
