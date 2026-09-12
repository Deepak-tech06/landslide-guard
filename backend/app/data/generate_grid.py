"""
Generate the 0.25° risk grid covering Northeast India.
Run once to produce ner_risk_grid.json.

NER bounding box: ~21.5°N–29.5°N, 88°E–97.5°E
Grid resolution: 0.25°

Terrain values are approximate prototype values derived from NER geological
literature. Each cell is labelled data_source: SIMULATED.
"""

import json
import math
import os
import random

random.seed(42)

# NER bounding box
LAT_MIN, LAT_MAX = 21.5, 29.5
LNG_MIN, LNG_MAX = 88.0, 97.5
STEP = 0.25

# Known high-susceptibility zones (approximate centroids)
HIGH_SUSCEPTIBILITY_ZONES = [
    (25.58, 91.89, 1.5),   # Shillong
    (25.27, 91.72, 1.8),   # Cherrapunji/Mawsynram
    (27.34, 88.61, 1.4),   # Gangtok
    (23.73, 92.72, 1.2),   # Aizawl
    (25.01, 93.47, 1.6),   # Noney
    (27.26, 92.42, 1.3),   # Bomdila
    (25.68, 94.11, 1.1),   # Kohima
    (27.59, 91.86, 1.3),   # Tawang
    (27.51, 88.52, 1.4),   # Mangan
]


def distance_km(lat1, lng1, lat2, lng2):
    """Approximate distance in km using Haversine."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def generate_terrain(lat, lng):
    """Generate realistic-ish terrain values based on proximity to known zones."""
    # Base values
    base_elevation = 200 + random.gauss(0, 100)
    base_slope = 10 + random.gauss(0, 5)
    base_susceptibility = 0.3 + random.gauss(0, 0.1)
    base_drainage = 0.4 + random.gauss(0, 0.1)

    # Boost near high-susceptibility zones
    for zlat, zlng, zmult in HIGH_SUSCEPTIBILITY_ZONES:
        d = distance_km(lat, lng, zlat, zlng)
        if d < 100:
            factor = max(0, 1 - d / 100) * zmult
            base_elevation += factor * 800
            base_slope += factor * 25
            base_susceptibility += factor * 0.45
            base_drainage += factor * 0.3

    # Clamp
    elevation = max(10, min(4000, base_elevation))
    slope = max(2, min(50, base_slope))
    susceptibility = max(0.1, min(0.95, base_susceptibility))
    drainage = max(0.2, min(0.9, base_drainage))

    return {
        "elevation": round(elevation, 1),
        "slope": round(slope, 1),
        "geology_susceptibility": round(susceptibility, 3),
        "drainage_density": round(drainage, 3),
    }


def generate_grid():
    cells = []
    lat = LAT_MIN
    while lat < LAT_MAX:
        lng = LNG_MIN
        while lng < LNG_MAX:
            center_lat = round(lat + STEP / 2, 4)
            center_lng = round(lng + STEP / 2, 4)
            cell_id = f"{center_lat}_{center_lng}"

            # Polygon bounds (SW, SE, NE, NW, close)
            bounds = [
                [round(lng, 4), round(lat, 4)],
                [round(lng + STEP, 4), round(lat, 4)],
                [round(lng + STEP, 4), round(lat + STEP, 4)],
                [round(lng, 4), round(lat + STEP, 4)],
                [round(lng, 4), round(lat, 4)],
            ]

            terrain = generate_terrain(center_lat, center_lng)

            cells.append({
                "cell_id": cell_id,
                "center_lat": center_lat,
                "center_lng": center_lng,
                "bounds": bounds,
                **terrain,
                "historical_landslide_density": 0,
                "distance_to_historical_landslide": 999,
                "data_source": "SIMULATED",
            })

            lng += STEP
        lat += STEP

    return cells


if __name__ == "__main__":
    cells = generate_grid()
    out_path = os.path.join(os.path.dirname(__file__), "ner_risk_grid.json")
    with open(out_path, "w") as f:
        json.dump(cells, f, indent=None)
    print(f"Generated {len(cells)} risk grid cells → {out_path}")
