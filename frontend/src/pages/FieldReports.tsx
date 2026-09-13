import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { submitFieldReport, fetchFieldReports, verifyIncident } from '../services/api';
import { useAuth } from '../AuthContext';

const INCIDENT_TYPES = [
  { value: 'landslide_observed', label: 'Landslide Observed' },
  { value: 'road_obstruction', label: 'Road Obstruction' },
  { value: 'slope_crack', label: 'Slope Crack' },
  { value: 'debris_flow', label: 'Debris Flow' },
  { value: 'drainage_blockage', label: 'Drainage Blockage' },
  { value: 'unusual_ground_movement', label: 'Unusual Ground Movement' },
  { value: 'other', label: 'Other' },
];

const SEVERITY_OPTIONS = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];

export default function FieldReports() {
  const { session, role } = useAuth();
  const [reports, setReports] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    latitude: 25.5788,
    longitude: 91.8933,
    incident_type: 'landslide_observed',
    severity: 'MODERATE',
    description: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchFieldReports().then(data => setReports(data.reports || [])).catch(console.error);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const result = await submitFieldReport(form);
      setReports(prev => [result.report, ...prev]);
      setShowForm(false);
      setForm({ ...form, description: '' });
    } catch (err) {
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (id: string, action: string) => {
    if (role !== 'AUTHORITY' && role !== 'ADMIN') {
      alert("Insufficient permissions to verify incidents.");
      return;
    }
    try {
      const status = action === 'VERIFY' ? 'VERIFIED' : action === 'DISMISS' ? 'DISMISSED' : 'NEEDS_MORE_EVIDENCE';
      await verifyIncident(id, { status, notes: `${action} by authority` });
      // Refresh
      const data = await fetchFieldReports();
      setReports(data.reports || []);
    } catch (err: any) {
      alert(`Verify error: ${err.message}`);
      console.error('Verify error:', err);
    }
  };

  const handleGetLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setForm({ ...form, latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
        () => console.log('Geolocation denied')
      );
    }
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>GEOSENSE</h1>
          <div className="subtitle">AI Early Warning System • NER</div>
        </div>
        <nav className="sidebar-nav">
          <Link to="/dashboard" className="sidebar-link">📊 Dashboard</Link>
          <Link to="/alerts" className="sidebar-link">🔔 Alerts</Link>
          <Link to="/field-reports" className="sidebar-link active">📋 Field Reports</Link>
        </nav>
        <div className="sidebar-demo-label">⚠ DEMO MODEL<br />Not an operational forecast</div>
      </aside>

      <main className="main-content">
        <header className="header-bar">
          <div className="header-title">FIELD REPORTS & INCIDENTS</div>
          {session && (
            <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
              {showForm ? '✕ Cancel' : '+ New Report'}
            </button>
          )}
        </header>

        <div style={{ padding: 24 }}>
          {/* Submit form */}
          {showForm && (
            <div className="panel" style={{ marginBottom: 24 }}>
              <div className="panel-header">SUBMIT FIELD REPORT</div>
              <div className="panel-body">
                <form onSubmit={handleSubmit}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div className="form-group">
                      <label className="form-label">Latitude</label>
                      <input className="form-input" type="number" step="0.0001"
                        value={form.latitude} onChange={e => setForm({ ...form, latitude: parseFloat(e.target.value) })} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Longitude</label>
                      <input className="form-input" type="number" step="0.0001"
                        value={form.longitude} onChange={e => setForm({ ...form, longitude: parseFloat(e.target.value) })} />
                    </div>
                  </div>

                  <div style={{ marginBottom: 12 }}>
                    <button type="button" className="btn btn-outline btn-sm" onClick={handleGetLocation}>
                      📍 Use My Location
                    </button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <div className="form-group">
                      <label className="form-label">Incident Type</label>
                      <select className="form-select" value={form.incident_type}
                        onChange={e => setForm({ ...form, incident_type: e.target.value })}>
                        {INCIDENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Severity</label>
                      <select className="form-select" value={form.severity}
                        onChange={e => setForm({ ...form, severity: e.target.value })}>
                        {SEVERITY_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Description</label>
                    <textarea className="form-textarea" value={form.description}
                      onChange={e => setForm({ ...form, description: e.target.value })}
                      placeholder="Describe what you observed..." />
                  </div>

                  <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: '100%' }}>
                    {submitting ? 'Submitting...' : '📋 Submit Field Report'}
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Reports list */}
          <div className="panel">
            <div className="panel-header">
              <span>ALL REPORTS</span>
              <span style={{ fontFamily: 'JetBrains Mono' }}>{reports.length}</span>
            </div>
            <div className="panel-body" style={{ padding: 0 }}>
              {reports.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                  No field reports yet. Submit one above or run the Storm Scenario.
                </div>
              ) : (
                reports.map((r: any, i: number) => (
                  <div key={i} style={{
                    padding: '16px 20px', borderBottom: '1px solid var(--border)',
                    display: 'flex', gap: 16, alignItems: 'flex-start',
                  }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 8,
                      background: r.status === 'VERIFIED' ? 'rgba(34,197,94,0.15)' :
                        r.status === 'DISMISSED' ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
                    }}>
                      {r.status === 'VERIFIED' ? '✅' : r.status === 'DISMISSED' ? '❌' : '📋'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13 }}>
                            {INCIDENT_TYPES.find(t => t.value === r.incident_type)?.label || r.incident_type}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                            {r.latitude?.toFixed(4)}, {r.longitude?.toFixed(4)} • {r.severity} • {r.reporter_role}
                          </div>
                        </div>
                        <span className={`badge ${r.status === 'VERIFIED' ? 'badge-live' :
                          r.status === 'DISMISSED' ? 'badge-error' : 'badge-simulated'}`}>
                          {r.status}
                        </span>
                      </div>
                      {r.description && (
                        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.5 }}>
                          {r.description}
                        </p>
                      )}
                      <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 6 }}>
                        {new Date(r.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                      </div>

                      {/* Verification buttons */}
                      {r.status === 'SUBMITTED' && (role === 'AUTHORITY' || role === 'ADMIN') && (
                        <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                          <button className="btn btn-sm" style={{ background: '#22c55e', color: '#fff', border: 'none' }}
                            onClick={() => handleVerify(r.id, 'VERIFY')}>✅ Verify</button>
                          <button className="btn btn-sm btn-outline"
                            onClick={() => handleVerify(r.id, 'DISMISS')}>❌ Dismiss</button>
                          <button className="btn btn-sm btn-outline"
                            onClick={() => handleVerify(r.id, 'NEEDS_MORE_EVIDENCE')}>❓ More Evidence</button>
                        </div>
                      )}
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
