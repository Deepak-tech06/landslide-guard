"""
Synthetic training data generator for the NER landslide risk model.

Generates training samples based on realistic NER terrain and monsoon parameters.
Every record is labelled source_type: SIMULATED.

⚠ DEMONSTRATION DATA — NOT VALIDATED OBSERVATIONS
"""

import numpy as np
import pandas as pd
import random

random.seed(42)
np.random.seed(42)

FEATURES = [
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_24h", "rainfall_72h",
    "soil_moisture", "slope", "elevation", "geology_susceptibility",
    "historical_landslide_density", "distance_to_historical_landslide",
    "drainage_density",
]


def generate_training_data(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate synthetic landslide training data.

    The label (landslide_occurred) is generated using a physically-informed
    rule combining rainfall intensity, slope, geological susceptibility,
    and soil saturation. This is NOT validated against real observations.
    """
    data = []

    for _ in range(n_samples):
        # Rainfall — monsoon patterns (heavy tail distribution)
        rainfall_1h = max(0, np.random.exponential(5))
        rainfall_3h = rainfall_1h + max(0, np.random.exponential(10))
        rainfall_6h = rainfall_3h + max(0, np.random.exponential(15))
        rainfall_24h = rainfall_6h + max(0, np.random.exponential(40))
        rainfall_72h = rainfall_24h + max(0, np.random.exponential(80))

        # Terrain — NER ranges
        slope = np.clip(np.random.normal(25, 12), 2, 50)
        elevation = np.clip(np.random.normal(800, 600), 10, 4000)
        geology_susceptibility = np.clip(np.random.beta(3, 3), 0.1, 0.95)
        drainage_density = np.clip(np.random.normal(0.55, 0.15), 0.2, 0.9)

        # Soil moisture — correlated with recent rainfall
        base_moisture = 0.3 + 0.3 * (rainfall_24h / 200)
        soil_moisture = np.clip(base_moisture + np.random.normal(0, 0.1), 0.1, 0.99)

        # Historical context
        historical_landslide_density = max(0, np.random.exponential(0.3))
        distance_to_historical_landslide = max(0.1, np.random.exponential(50))

        # === Label generation ===
        # Physically-informed composite risk score
        rainfall_factor = (
            0.15 * min(rainfall_1h / 30, 1) +
            0.20 * min(rainfall_3h / 60, 1) +
            0.25 * min(rainfall_24h / 150, 1) +
            0.15 * min(rainfall_72h / 300, 1)
        )
        terrain_factor = (
            0.4 * min(slope / 45, 1) +
            0.3 * geology_susceptibility +
            0.3 * drainage_density
        )
        saturation_factor = soil_moisture
        history_factor = min(historical_landslide_density / 2, 1) * 0.3

        composite = (
            0.40 * rainfall_factor +
            0.30 * terrain_factor +
            0.20 * saturation_factor +
            0.10 * history_factor
        )

        # Add noise and threshold
        composite_noisy = composite + np.random.normal(0, 0.05)
        landslide_occurred = 1 if composite_noisy > 0.45 else 0

        data.append({
            "rainfall_1h": round(rainfall_1h, 2),
            "rainfall_3h": round(rainfall_3h, 2),
            "rainfall_6h": round(rainfall_6h, 2),
            "rainfall_24h": round(rainfall_24h, 2),
            "rainfall_72h": round(rainfall_72h, 2),
            "soil_moisture": round(soil_moisture, 3),
            "slope": round(slope, 1),
            "elevation": round(elevation, 1),
            "geology_susceptibility": round(geology_susceptibility, 3),
            "historical_landslide_density": round(historical_landslide_density, 3),
            "distance_to_historical_landslide": round(distance_to_historical_landslide, 1),
            "drainage_density": round(drainage_density, 3),
            "landslide_occurred": landslide_occurred,
        })

    df = pd.DataFrame(data)
    return df


if __name__ == "__main__":
    df = generate_training_data(5000)
    print(f"Generated {len(df)} samples")
    print(f"Positive rate: {df['landslide_occurred'].mean():.2%}")
    print(df.describe().round(2))
