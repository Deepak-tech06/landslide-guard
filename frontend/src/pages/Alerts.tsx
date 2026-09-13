import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchAlerts } from '../services/api';

const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e', MODERATE: '#eab308', HIGH: '#f97316',
  VERY_HIGH: '#ef4444', CRITICAL: '#a855f7',
};

const SEVERITY_ICONS: Record<string, string> = {
  ADVISORY: 'ℹ️', WATCH: '👁', WARNING: '⚠️', SEVERE: '🔴', CRITICAL: '🟣',
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    fetchAlerts().then(data => setAlerts(data.alerts || [])).catch(console.error);
  }, []);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>GEOSENSE</h1>
          <div className="subtitle">AI Early Warning System • NER</div>
        </div>
        <nav className="sidebar-nav">
          <Link to="/dashboard" className="sidebar-link">📊 Dashboard</Link>
          <Link to="/alerts" className="sidebar-link active">🔔 Alerts</Link>
          <Link to="/field-reports" className="sidebar-link">📋 Field Reports</Link>
        </nav>
        <div className="sidebar-demo-label">⚠ DEMO MODEL<br />Not an operational forecast</div>
      </aside>

      <main className="main-content">
        <header className="header-bar">
          <div className="header-title">ALERT MANAGEMENT</div>
          <div className="header-status">
            <span>{alerts.length} total alerts</span>
          </div>
        </header>

        <div style={{ padding: 24 }}>
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            {['GENERATED', 'SENT', 'ACKNOWLEDGED', 'VERIFIED', 'DISMISSED'].map(status => {
              const count = alerts.filter(a => a.status === status).length;
              return (
                <div key={status} className="stat-card" style={{ flex: '1 1 140px' }}>
                  <div className="stat-label">{status}</div>
                  <div className="stat-value" style={{ fontSize: 24 }}>{count}</div>
                </div>
              );
            })}
          </div>

          <div className="panel">
            <div className="panel-header">ALL ALERTS</div>
            <div className="panel-body" style={{ padding: 0 }}>
              {alerts.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                  No alerts generated yet. Use the dashboard to generate a warning.
                </div>
              ) : (
                alerts.map((alert: any, i: number) => (
                  <div key={i} style={{
                    padding: '16px 20px',
                    borderBottom: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 16,
                  }}>
                    <div style={{
                      width: 44, height: 44, borderRadius: 8,
                      background: `${RISK_COLORS[alert.risk_level]}22`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 20, flexShrink: 0,
                    }}>
                      {SEVERITY_ICONS[alert.severity] || '⚠️'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: RISK_COLORS[alert.risk_level] }}>
                            {alert.severity} — {alert.risk_level?.replace('_', ' ')}
                          </div>
                          <div style={{ fontSize: 15, fontWeight: 600, marginTop: 2 }}>{alert.location_name}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className={`badge badge-${alert.status === 'GENERATED' ? 'simulated' : 'live'}`}>
                            {alert.status}
                          </span>
                        </div>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                        Risk Score: <strong style={{ fontFamily: 'JetBrains Mono' }}>{alert.risk_score}</strong>/100
                      </div>
                      {alert.risk_statement && (
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.5, fontStyle: 'italic' }}>
                          {alert.risk_statement}
                        </p>
                      )}
                      <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 6 }}>
                        {new Date(alert.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
