import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, CircleMarker, useMap } from 'react-leaflet';
import { LatLngBoundsExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  fetchWeather, predictRisk, fetchRiskCells, fetchRoads, fetchLandslides,
  fetchSettlements, fetchHotspots, fetchAlerts, createAlert, fetchDataSources,
  runSimulation
} from '../services/api';
import { useAuth } from '../AuthContext';

// NER bounds
const NER_BOUNDS: LatLngBoundsExpression = [[21.5, 88.0], [29.5, 97.5]];
const NER_CENTER: [number, number] = [25.5, 92.5];

// Risk colors
const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e', MODERATE: '#eab308', HIGH: '#f97316',
  VERY_HIGH: '#ef4444', CRITICAL: '#a855f7',
};

function getRiskColor(score: number): string {
  if (score >= 85) return RISK_COLORS.CRITICAL;
  if (score >= 70) return RISK_COLORS.VERY_HIGH;
  if (score >= 50) return RISK_COLORS.HIGH;
  if (score >= 30) return RISK_COLORS.MODERATE;
  return RISK_COLORS.LOW;
}

function getRiskLevel(score: number): string {
  if (score >= 85) return 'CRITICAL';
  if (score >= 70) return 'VERY_HIGH';
  if (score >= 50) return 'HIGH';
  if (score >= 30) return 'MODERATE';
  return 'LOW';
}

function StatusBadge({ status }: { status: string }) {
  const cls = status === 'LIVE' ? 'badge-live'
    : status === 'CACHED' ? 'badge-cached'
    : status === 'SIMULATED' || status === 'CALCULATED' ? 'badge-simulated'
    : status === 'ERROR' ? 'badge-error' : 'badge-unavailable';
  const icon = status === 'LIVE' ? '🟢'
    : status === 'CACHED' ? '🟡'
    : status === 'SIMULATED' || status === 'CALCULATED' ? '🔵' : '⚪';
  return <span className={`badge ${cls}`}>{icon} {status}</span>;
}

export default function Dashboard() {
  const { session, user, role, logout } = useAuth();
  const navigate = useNavigate();
  
  const [weather, setWeather] = useState<any>(null);
  const [prediction, setPrediction] = useState<any>(null);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [roads, setRoads] = useState<any>(null);
  const [landslides, setLandslides] = useState<any>(null);
  const [settlements, setSettlements] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [dataSources, setDataSources] = useState<any[]>([]);
  const [selectedLocation, setSelectedLocation] = useState({ name: 'Shillong', lat: 25.5788, lng: 91.8933 });
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [weatherData, predData, hotspotsData, roadsData, landslidesData, settlementsData, alertsData, dsData] = await Promise.allSettled([
        fetchWeather(selectedLocation.lat, selectedLocation.lng),
        predictRisk({ latitude: selectedLocation.lat, longitude: selectedLocation.lng }),
        fetchHotspots(),
        fetchRoads(),
        fetchLandslides(),
        fetchSettlements(),
        fetchAlerts(),
        fetchDataSources(),
      ]);

      if (weatherData.status === 'fulfilled') setWeather(weatherData.value);
      if (predData.status === 'fulfilled') setPrediction(predData.value);
      if (hotspotsData.status === 'fulfilled') setHotspots(hotspotsData.value.hotspots || []);
      if (roadsData.status === 'fulfilled') setRoads(roadsData.value);
      if (landslidesData.status === 'fulfilled') setLandslides(landslidesData.value);
      if (settlementsData.status === 'fulfilled') setSettlements(settlementsData.value);
      if (alertsData.status === 'fulfilled') setAlerts(alertsData.value.alerts || []);
      if (dsData.status === 'fulfilled') setDataSources(dsData.value.sources || []);
    } catch (err) {
      console.error('Load error:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedLocation]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleGenerateWarning = async () => {
    if (!prediction) return;
    if (role !== 'AUTHORITY' && role !== 'ADMIN') {
      alert("Insufficient permissions to generate warnings.");
      return;
    }
    
    try {
      const result = await createAlert({
        location_name: selectedLocation.name,
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lng,
        risk_score: prediction.risk_score,
        risk_level: prediction.risk_level,
        risk_drivers: prediction.top_drivers,
        risk_statement: prediction.risk_statement,
      });
      setAlerts(prev => [result.alert, ...prev]);
    } catch (err: any) {
      alert(`Alert error: ${err.message}`);
      console.error('Alert error:', err);
    }
  };

  const handleSimulation = async () => {
    setIsSimulating(true);
    try {
      const result = await runSimulation();
      setSimulationResult(result);
      setPrediction(result.risk_prediction);
      if (result.alert) setAlerts(prev => [result.alert, ...prev]);
    } catch (err: any) {
      alert(`Simulation error: ${err.message}`);
      console.error('Simulation error:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const riskScore = prediction?.risk_score ?? 0;
  const riskLevel = prediction?.risk_level ?? 'LOW';
  const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' });

  const hasAuthority = role === 'ADMIN' || role === 'AUTHORITY';

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>GEOSENSE</h1>
          <div className="subtitle">AI Early Warning System • NER</div>
        </div>
        <nav className="sidebar-nav">
          <Link to="/dashboard" className="sidebar-link active">📊 Dashboard</Link>
          <Link to="/alerts" className="sidebar-link">🔔 Alerts</Link>
          <Link to="/field-reports" className="sidebar-link">📋 Field Reports</Link>
          
          {hasAuthority && (
            <button className="sidebar-link" onClick={handleSimulation} disabled={isSimulating}>
              {isSimulating ? '⏳ Running...' : '🌧️ Storm Scenario'}
            </button>
          )}
        </nav>
        
        <div style={{ marginTop: 'auto', marginBottom: '20px' }}>
          {session ? (
            <div style={{ padding: '0 20px' }}>
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>
                Logged in as <strong>{role}</strong>
              </div>
              <button 
                onClick={() => logout()}
                className="btn" 
                style={{ width: '100%', background: '#334155', color: 'white', padding: '8px', borderRadius: '6px', fontSize: '13px' }}
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div style={{ padding: '0 20px' }}>
              <Link 
                to="/login"
                className="btn" 
                style={{ display: 'block', textAlign: 'center', width: '100%', background: '#dc2626', color: 'white', padding: '8px', borderRadius: '6px', fontSize: '13px', textDecoration: 'none' }}
              >
                Sign In
              </Link>
            </div>
          )}
        </div>
        
        <div className="sidebar-demo-label">
          ⚠ DEMO MODEL<br />Not an operational forecast
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        {/* Header */}
        <header className="header-bar">
          <div className="header-title">COMMAND DASHBOARD</div>
          <div className="header-status">
            <span className="live-dot">
              {weather?.status === 'LIVE' ? 'LIVE DATA' : 'CONNECTING...'}
            </span>
            <span>{now} IST</span>
          </div>
        </header>

        {/* Simulation banner */}
        {simulationResult && (
          <div className="simulation-banner">
            ⚠ SIMULATION MODE — {simulationResult.scenario} — All data is synthetic
          </div>
        )}

        {/* Stats bar */}
        <div className="stats-bar">
          <div className="stat-card" style={{ borderLeft: `3px solid ${getRiskColor(riskScore)}` }}>
            <div className="stat-label">Risk Score</div>
            <div className="stat-value" style={{ color: getRiskColor(riskScore) }}>{Math.round(riskScore)}</div>
            <div className="stat-sub">{riskLevel.replace('_', ' ')}</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '3px solid var(--risk-critical)' }}>
            <div className="stat-label">Hotspots</div>
            <div className="stat-value">{hotspots.filter(h => h.risk_level === 'VERY_HIGH' || h.risk_level === 'CRITICAL').length}</div>
            <div className="stat-sub">Critical zones</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '3px solid var(--risk-high)' }}>
            <div className="stat-label">Active Alerts</div>
            <div className="stat-value">{alerts.length}</div>
            <div className="stat-sub">Generated</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '3px solid var(--accent)' }}>
            <div className="stat-label">Data Sources</div>
            <div className="stat-value">{dataSources.filter(d => d.status !== 'UNAVAILABLE' && d.status !== 'ERROR').length}/{dataSources.length}</div>
            <div className="stat-sub">Available</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '3px solid var(--status-live)' }}>
            <div className="stat-label">Rainfall 24h</div>
            <div className="stat-value" style={{ fontSize: '22px' }}>
              {weather?.precipitation_24h != null ? `${weather.precipitation_24h}` : '—'}
            </div>
            <div className="stat-sub">{weather?.status === 'LIVE' ? '🟢 Open-Meteo' : '⚪ Loading'} mm</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '3px solid #8b5cf6' }}>
            <div className="stat-label">Soil Moisture</div>
            <div className="stat-value" style={{ fontSize: '22px' }}>
              {prediction?.features?.soil_moisture != null ? `${(prediction.features.soil_moisture * 100).toFixed(0)}%` : '—'}
            </div>
            <div className="stat-sub">SIMULATED</div>
          </div>
        </div>

        {/* Dashboard grid */}
        <div className="dashboard-grid">
          {/* Map */}
          <div className="map-panel" style={{ position: 'relative' }}>
            <MapContainer
              bounds={NER_BOUNDS}
              style={{ height: '100%', width: '100%' }}
              zoomControl={true}
              attributionControl={true}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                className="map-tiles"
              />

              {/* Hotspot markers */}
              {hotspots.map((h, i) => (
                <CircleMarker
                  key={i}
                  center={[h.latitude, h.longitude]}
                  radius={12}
                  fillColor={RISK_COLORS[h.risk_level] || '#f97316'}
                  fillOpacity={0.6}
                  color={RISK_COLORS[h.risk_level] || '#f97316'}
                  weight={2}
                  eventHandlers={{
                    click: () => {
                      setSelectedLocation({ name: h.name, lat: h.latitude, lng: h.longitude });
                      loadData();
                    }
                  }}
                >
                  <Popup>
                    <div style={{ color: '#f1f5f9', minWidth: 220 }}>
                      <h3 style={{ fontSize: 14, marginBottom: 8 }}>{h.name}</h3>
                      <div style={{ fontSize: 11, lineHeight: 1.8 }}>
                        <div style={{ color: '#fbbf24', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>AI Risk Estimate Zone</div>
                        <div>Risk Level: <strong style={{ color: RISK_COLORS[h.risk_level] }}>{h.risk_level?.replace('_', ' ')}</strong></div>
                        <div>Susceptibility: <strong>{(h.susceptibility * 100).toFixed(0)}%</strong></div>
                        <div>Slope: <strong>{h.slope}°</strong></div>
                        <div>State: {h.state}</div>
                        <div style={{ marginTop: 4 }}>
                          <StatusBadge status={h.data_source || 'SIMULATED'} />
                        </div>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}

              {/* Roads layer */}
              {roads && (
                <GeoJSON
                  data={roads}
                  style={{ color: '#f97316', weight: 2, opacity: 0.6 }}
                  onEachFeature={(feature, layer) => {
                    if (feature.properties?.name) {
                      layer.bindPopup(`
                        <div style="color:#f1f5f9">
                          <strong>${feature.properties.name}</strong><br/>
                          Type: ${feature.properties.road_type || 'N/A'}<br/>
                          Road Network: 🟢 LIVE GIS DATA<br/>
                          Road Risk: 🔵 CALCULATED<br/>
                          Road Blockage: ⚪ NOT VERIFIED
                        </div>
                      `);
                    }
                  }}
                />
              )}

              {/* Historical landslides */}
              {landslides && (
                <GeoJSON
                  data={landslides}
                  pointToLayer={(feature, latlng) => {
                    const verified = feature.properties?.verified;
                    return new (window as any).L.CircleMarker(latlng, {
                      radius: 6,
                      fillColor: verified ? '#ef4444' : '#64748b',
                      fillOpacity: 0.7,
                      color: verified ? '#ef4444' : '#64748b',
                      weight: 1,
                    });
                  }}
                  onEachFeature={(feature, layer) => {
                    const p = feature.properties;
                    layer.bindPopup(`
                      <div style="color:#f1f5f9;min-width:200px">
                        <strong>${p?.name || 'Unknown'}</strong><br/>
                        <span style="color:#ef4444;font-size:10px;text-transform:uppercase">Historical Landslide Event (Not Active)</span><br/>
                        Date: ${p?.event_date || 'N/A'}<br/>
                        Severity: ${p?.severity || 'N/A'}<br/>
                        Source: <strong>${p?.source}</strong> (${p?.source_type})<br/>
                        Verified: ${p?.verified ? '✅ Yes' : '❌ No'}<br/>
                        ${p?.source_url ? `<a href="${p.source_url}" target="_blank" style="color:#3b82f6">Source Link</a>` : ''}
                      </div>
                    `);
                  }}
                />
              )}

              {/* Settlements */}
              {settlements && (
                <GeoJSON
                  data={settlements}
                  pointToLayer={(feature, latlng) => (
                    new (window as any).L.CircleMarker(latlng, {
                      radius: 4, fillColor: '#94a3b8', fillOpacity: 0.5,
                      color: '#94a3b8', weight: 1,
                    })
                  )}
                  onEachFeature={(feature, layer) => {
                    const p = feature.properties;
                    layer.bindPopup(`<div style="color:#f1f5f9"><strong>${p?.name}</strong><br/>Pop: ${p?.population?.toLocaleString() || 'N/A'}<br/>${p?.state}</div>`);
                  }}
                />
              )}
            </MapContainer>

            {/* Map Legend */}
            <div className="map-legend">
              <h4>Risk Level</h4>
              {Object.entries(RISK_COLORS).map(([level, color]) => (
                <div className="legend-item" key={level}>
                  <div className="legend-color" style={{ background: color }}></div>
                  {level.replace('_', ' ')}
                </div>
              ))}
              <div className="legend-item" style={{ marginTop: 6, paddingTop: 6, borderTop: '1px solid var(--border)' }}>
                <div className="legend-color" style={{ background: '#94a3b8', borderRadius: '50%' }}></div>
                Settlement
              </div>
            </div>
          </div>

          {/* Right panels */}
          <div className="right-panels">
            {/* Selected location */}
            <div className="panel">
              <div className="panel-header">
                <span>📍 {selectedLocation.name}</span>
                <span className="demo-model-label">🔵 DEMO MODEL</span>
              </div>
              <div className="panel-body">
                <div style={{ textAlign: 'center', marginBottom: 16 }}>
                  <div style={{ fontSize: 48, fontFamily: 'JetBrains Mono', fontWeight: 800, color: getRiskColor(riskScore) }}>
                    {Math.round(riskScore)}
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: getRiskColor(riskScore), letterSpacing: 1 }}>
                    {riskLevel.replace('_', ' ')}
                  </div>
                  {prediction?.confidence && (
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                      Model Confidence: Not Calibrated <br/>
                      <span style={{ color: '#fbbf24' }}>(Unvalidated Prototype)</span>
                    </div>
                  )}
                </div>

                {/* Generate Warning button */}
                {riskScore >= 50 && (
                  <button className="btn btn-danger" style={{ width: '100%', marginBottom: 12 }} onClick={handleGenerateWarning}>
                    ⚠ GENERATE WARNING
                  </button>
                )}
              </div>
            </div>

            {/* WHY THIS RISK? */}
            {prediction?.explanation?.drivers?.length > 0 && (
              <div className="panel">
                <div className="panel-header">WHY THIS RISK?</div>
                <div className="panel-body">
                  {prediction.explanation.drivers.map((d: any, i: number) => (
                    <div className="driver-bar" key={i}>
                      <div className="driver-label">{d.label}</div>
                      <div className="driver-bar-track">
                        <div
                          className="driver-bar-fill"
                          style={{
                            width: `${Math.min(100, d.contribution)}%`,
                            background: `linear-gradient(90deg, ${getRiskColor(d.contribution)}, ${getRiskColor(d.contribution)}88)`,
                          }}
                        />
                      </div>
                      <div className="driver-value">{d.contribution.toFixed(0)}%</div>
                    </div>
                  ))}
                  {prediction.risk_statement && (
                    <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 12, lineHeight: 1.6, fontStyle: 'italic' }}>
                      {prediction.risk_statement}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Weather */}
            <div className="panel">
              <div className="panel-header">
                <span>🌧 RAINFALL</span>
                {weather && <StatusBadge status={weather.status} />}
              </div>
              <div className="panel-body">
                <div className="weather-grid">
                  <div className="weather-item">
                    <div className="value">{weather?.precipitation_1h ?? '—'}</div>
                    <div className="label">1h (mm)</div>
                  </div>
                  <div className="weather-item">
                    <div className="value">{weather?.precipitation_3h ?? '—'}</div>
                    <div className="label">3h</div>
                  </div>
                  <div className="weather-item">
                    <div className="value">{weather?.precipitation_24h ?? '—'}</div>
                    <div className="label">24h</div>
                  </div>
                  <div className="weather-item">
                    <div className="value">{weather?.precipitation_72h ?? '—'}</div>
                    <div className="label">72h</div>
                  </div>
                </div>
                {weather?.observation_time && (
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8, textAlign: 'right' }}>
                    Updated: {new Date(weather.observation_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                    {' • '}{weather.provider}
                  </div>
                )}
              </div>
            </div>

            {/* Active Alerts */}
            <div className="panel">
              <div className="panel-header">
                <span>🔔 ACTIVE ALERTS</span>
                <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12 }}>{alerts.length}</span>
              </div>
              <div className="panel-body" style={{ padding: 0, maxHeight: 200, overflowY: 'auto' }}>
                {alerts.length === 0 ? (
                  <div style={{ padding: 16, fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>No active alerts</div>
                ) : (
                  alerts.slice(0, 5).map((a: any, i: number) => (
                    <div className="alert-item" key={i}>
                      <div className="alert-dot" style={{ background: RISK_COLORS[a.risk_level] || '#f97316' }} />
                      <div className="alert-info">
                        <div className="alert-name">{a.location_name}</div>
                        <div className="alert-detail">
                          Score: {a.risk_score} • {a.severity} • {a.status}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Data Health */}
            <div className="panel">
              <div className="panel-header">📡 DATA SOURCES</div>
              <div className="panel-body">
                <div className="data-health-grid">
                  {dataSources.map((ds: any, i: number) => (
                    <div className="data-health-row" key={i}>
                      <span style={{ color: 'var(--text-secondary)' }}>{ds.display_name || ds.provider}</span>
                      <StatusBadge status={ds.label || ds.status} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
