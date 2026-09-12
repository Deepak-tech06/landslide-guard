import { supabase } from './supabase';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }

  const resp = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!resp.ok) {
    const error = await resp.text();
    throw new Error(`API Error ${resp.status}: ${error}`);
  }
  return resp.json();
}

// Weather
export const fetchWeather = (lat: number, lng: number) =>
  apiFetch<any>(`/api/v1/weather/current?lat=${lat}&lng=${lng}`);

// Risk
export const predictRisk = (data: any) =>
  apiFetch<any>('/api/v1/risk/predict', { method: 'POST', body: JSON.stringify(data) });

export const getRiskByLocation = (id: string) =>
  apiFetch<any>(`/api/v1/risk/${id}`);

// Map layers
export const fetchRiskCells = () => apiFetch<any>('/api/v1/map/risk-cells');
export const fetchRoads = () => apiFetch<any>('/api/v1/map/roads');
export const fetchLandslides = () => apiFetch<any>('/api/v1/map/landslides');
export const fetchSettlements = () => apiFetch<any>('/api/v1/map/settlements');
export const fetchHotspots = () => apiFetch<any>('/api/v1/map/hotspots');

// Alerts
export const createAlert = (data: any) =>
  apiFetch<any>('/api/v1/alerts', { method: 'POST', body: JSON.stringify(data) });

export const fetchAlerts = () => apiFetch<any>('/api/v1/alerts');

// Field Reports
export const submitFieldReport = (data: any) =>
  apiFetch<any>('/api/v1/field-reports', { method: 'POST', body: JSON.stringify(data) });

export const fetchFieldReports = () => apiFetch<any>('/api/v1/field-reports');

// Incidents
export const fetchIncidents = () => apiFetch<any>('/api/v1/incidents');

export const verifyIncident = (id: string, data: any) =>
  apiFetch<any>(`/api/v1/incidents/${id}/verify`, { method: 'POST', body: JSON.stringify(data) });

// Data Sources
export const fetchDataSources = () => apiFetch<any>('/api/v1/data-sources/status');

// Health
export const fetchHealth = () => apiFetch<any>('/health');

// Simulation
export const runSimulation = () =>
  apiFetch<any>('/api/v1/simulation/shillong-storm', { method: 'POST' });
