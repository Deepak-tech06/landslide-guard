-- LandslideGuard — Initial Database Schema
-- PostgreSQL + PostGIS
-- Run against Supabase SQL Editor or via migration tool
--
-- ⚠ These are prototype tables. Schema will evolve.

-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- LOCATIONS: key monitoring points in NER
-- ============================================================
CREATE TABLE IF NOT EXISTS locations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation DOUBLE PRECISION,
    slope DOUBLE PRECISION,
    geology_susceptibility DOUBLE PRECISION,
    drainage_density DOUBLE PRECISION,
    geometry GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST(geometry);

-- ============================================================
-- RISK CELLS: 0.25° grid covering NER
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_cells (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cell_id TEXT UNIQUE NOT NULL,               -- e.g. "25.50_91.75"
    center_lat DOUBLE PRECISION NOT NULL,
    center_lng DOUBLE PRECISION NOT NULL,
    elevation DOUBLE PRECISION,
    slope DOUBLE PRECISION,
    geology_susceptibility DOUBLE PRECISION,
    drainage_density DOUBLE PRECISION,
    historical_landslide_density DOUBLE PRECISION DEFAULT 0,
    distance_to_historical_landslide DOUBLE PRECISION DEFAULT 999,
    geometry GEOMETRY(Polygon, 4326),
    data_source TEXT DEFAULT 'SIMULATED',        -- SIMULATED / VALIDATED
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_risk_cells_geom ON risk_cells USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_risk_cells_cell_id ON risk_cells(cell_id);

-- ============================================================
-- RISK PREDICTIONS: AI model outputs per cell
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_predictions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    cell_id TEXT REFERENCES risk_cells(cell_id),
    location_name TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,        -- 0-100
    risk_level TEXT NOT NULL,                     -- LOW/MODERATE/HIGH/VERY_HIGH/CRITICAL
    confidence DOUBLE PRECISION,
    model_version TEXT NOT NULL,
    input_snapshot JSONB,                         -- feature values used
    top_drivers JSONB,                            -- [{feature, contribution, value}]
    data_status TEXT DEFAULT 'DEMO',              -- LIVE / DEMO / MIXED
    risk_statement TEXT,                          -- human-readable explanation
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_risk_predictions_cell ON risk_predictions(cell_id);
CREATE INDEX IF NOT EXISTS idx_risk_predictions_time ON risk_predictions(created_at DESC);

-- ============================================================
-- WEATHER OBSERVATIONS: from Open-Meteo
-- ============================================================
CREATE TABLE IF NOT EXISTS weather_observations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    observation_time TIMESTAMPTZ NOT NULL,
    precipitation_mm DOUBLE PRECISION,
    precipitation_1h DOUBLE PRECISION,
    precipitation_3h DOUBLE PRECISION,
    precipitation_6h DOUBLE PRECISION,
    precipitation_24h DOUBLE PRECISION,
    precipitation_72h DOUBLE PRECISION,
    provider TEXT NOT NULL DEFAULT 'Open-Meteo',
    status TEXT NOT NULL DEFAULT 'LIVE',          -- LIVE / CACHED / ERROR
    request_time TIMESTAMPTZ DEFAULT now(),
    raw_response JSONB
);

CREATE INDEX IF NOT EXISTS idx_weather_time ON weather_observations(observation_time DESC);

-- ============================================================
-- HISTORICAL LANDSLIDES: with provenance tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS historical_landslides (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    event_date DATE,
    description TEXT,
    severity TEXT,
    source TEXT NOT NULL,                          -- "GSI" / "NRSC" / "DEMO"
    source_url TEXT,                               -- URL to published data
    source_type TEXT NOT NULL,                     -- "PUBLISHED_DATA" / "SIMULATED"
    verified BOOLEAN NOT NULL DEFAULT false,
    geometry GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_historical_geom ON historical_landslides USING GIST(geometry);

-- ============================================================
-- ROADS: NER highway corridors
-- ============================================================
CREATE TABLE IF NOT EXISTS roads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    road_type TEXT,                                -- NH / SH / District
    state TEXT,
    geometry GEOMETRY(LineString, 4326),
    source TEXT DEFAULT 'OSM',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roads_geom ON roads USING GIST(geometry);

-- ============================================================
-- SETTLEMENTS: population centers
-- ============================================================
CREATE TABLE IF NOT EXISTS settlements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT,
    population INTEGER,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_settlements_geom ON settlements USING GIST(geometry);

-- ============================================================
-- ALERTS: warning workflow
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    location_name TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    risk_level TEXT NOT NULL,
    severity TEXT NOT NULL,
    risk_drivers JSONB,
    risk_statement TEXT,
    status TEXT NOT NULL DEFAULT 'GENERATED',      -- DRAFT/GENERATED/SENT/ACKNOWLEDGED/VERIFIED/DISMISSED
    generated_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- FIELD TASKS: verification assignments
-- ============================================================
CREATE TABLE IF NOT EXISTS field_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    alert_id UUID REFERENCES alerts(id),
    location_name TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    task_type TEXT DEFAULT 'FIELD_VERIFICATION',
    priority TEXT DEFAULT 'HIGH',
    status TEXT NOT NULL DEFAULT 'PENDING',         -- PENDING / ASSIGNED / IN_PROGRESS / COMPLETED
    assigned_to TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- FIELD REPORTS: citizen/field team submissions
-- ============================================================
CREATE TABLE IF NOT EXISTS field_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    incident_type TEXT NOT NULL,                    -- landslide_observed/road_obstruction/slope_crack/etc
    severity TEXT DEFAULT 'MODERATE',
    description TEXT,
    photo_url TEXT,
    reporter_role TEXT DEFAULT 'CITIZEN',
    reporter_id TEXT,
    geometry GEOMETRY(Point, 4326),
    status TEXT DEFAULT 'SUBMITTED',                -- SUBMITTED / UNDER_REVIEW / VERIFIED / DISMISSED
    verification_notes TEXT,
    verified_by TEXT,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_field_reports_geom ON field_reports USING GIST(geometry);

-- ============================================================
-- DATA SOURCE STATUS: external service health
-- ============================================================
CREATE TABLE IF NOT EXISTS data_source_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    provider TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'UNKNOWN',         -- LIVE/CACHED/SIMULATED/UNAVAILABLE/ERROR
    last_updated TIMESTAMPTZ,
    latency_ms INTEGER,
    error_message TEXT,
    metadata JSONB
);

-- ============================================================
-- MODEL VERSIONS: ML model tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS model_versions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    version TEXT UNIQUE NOT NULL,
    model_type TEXT NOT NULL,                       -- random_forest / xgboost
    data_type TEXT NOT NULL,                        -- DEMO / VALIDATED
    training_date TIMESTAMPTZ,
    features JSONB,
    thresholds JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- AUDIT LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    user_id TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- SEED: initial data source status records
-- ============================================================
INSERT INTO data_source_status (provider, display_name, status, metadata) VALUES
    ('open_meteo', 'Open-Meteo Rainfall', 'UNKNOWN', '{"type": "weather", "label": "LIVE"}'),
    ('osm_basemap', 'OSM Basemap', 'LIVE', '{"type": "map", "label": "LIVE"}'),
    ('osm_roads', 'Road Network (OSM)', 'LIVE', '{"type": "gis", "label": "LIVE GIS DATA", "note": "Not live traffic/closures"}'),
    ('road_risk', 'Road Risk', 'SIMULATED', '{"type": "calculated", "label": "CALCULATED", "note": "Derived from AI risk overlay"}'),
    ('historical_landslides', 'Historical Landslides', 'LIVE', '{"type": "dataset", "label": "SOURCE-LABELLED"}'),
    ('ai_model', 'AI Risk Engine', 'SIMULATED', '{"type": "model", "label": "DEMO MODEL", "note": "Synthetic training data"}'),
    ('soil_moisture', 'Soil Moisture', 'SIMULATED', '{"type": "sensor", "label": "SIMULATED"}'),
    ('ground_movement', 'Ground Movement', 'SIMULATED', '{"type": "sensor", "label": "SIMULATED"}'),
    ('satellite_sar', 'Satellite/SAR', 'UNAVAILABLE', '{"type": "satellite", "label": "NOT YET INTEGRATED"}')
ON CONFLICT (provider) DO NOTHING;

-- Seed: initial model version record
INSERT INTO model_versions (version, model_type, data_type, features, thresholds, notes) VALUES
    ('v1-demo', 'random_forest', 'DEMO',
     '["rainfall_1h","rainfall_3h","rainfall_6h","rainfall_24h","rainfall_72h","soil_moisture","slope","elevation","geology_susceptibility","historical_landslide_density","distance_to_historical_landslide","drainage_density"]',
     '{"LOW": [0,29], "MODERATE": [30,49], "HIGH": [50,69], "VERY_HIGH": [70,84], "CRITICAL": [85,100]}',
     'Prototype model trained on synthetic NER data. NOT an operational forecast. Thresholds require calibration.')
ON CONFLICT (version) DO NOTHING;
