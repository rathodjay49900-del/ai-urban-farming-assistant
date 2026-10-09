import axios from 'axios';

/** Shared axios instance. Uses the Vite proxy (/api) unless VITE_API_URL is set. */
export const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string) || '/api',
  timeout: 120000,
});

export interface Plant {
  id: number;
  name: string;
  type: string;
  variety?: string | null;
  planting_date?: string | null;
  location?: string | null;
  sunlight?: string | null;
  growth_stage?: string | null;
  soil_moisture?: number | null;
  watering_interval_days?: number | null;
  last_watered?: string | null;
  health_score: number;
  status: string;
  image?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface PlantCreate {
  name: string;
  type: string;
  variety?: string;
  planting_date?: string;
  location?: string;
  sunlight?: string;
  growth_stage?: string;
  soil_moisture?: number;
  watering_interval_days?: number;
  image?: string;
  notes?: string;
}

export interface Prediction {
  label: string;
  confidence: number;
}

export interface PlantInfo {
  name: string;
  scientific_name: string;
  category: string;
  sunlight: string;
  water: string;
  temperature: string;
  soil: string;
}

export interface ScanResult {
  success: boolean;
  is_plant_related: boolean;
  category: string;
  confidence: number;
  class_label?: string | null;
  disease?: string | null;
  severity?: string | null;
  symptoms?: string[] | null;
  treatment?: string[] | null;
  prevention?: string[] | null;
  explanation?: string | null;
  plant_info?: PlantInfo | null;
  top_predictions?: Prediction[] | null;
  low_confidence: boolean;
  needs_expert: boolean;
  message?: string | null;
}

export interface WateringRecommendation {
  plant_id: number | null;
  plant_name: string;
  water_now: boolean;
  amount_ml?: number | null;
  next_watering?: string | null;
  soil_moisture?: number | null;
  weather?: string | null;
  temperature_c?: number | null;
  reason: string;
}

export interface DashboardStats {
  total_plants: number;
  healthy_plants: number;
  needs_attention: number;
  water_today: number;
  average_health: number;
  total_scans: number;
  healthy_scans: number;
  diseased_scans: number;
}

export interface ScanHistoryItem {
  id: number;
  plant_id?: number | null;
  crop?: string | null;
  class_label?: string | null;
  disease?: string | null;
  confidence?: number | null;
  severity?: string | null;
  low_confidence: boolean;
  needs_expert: boolean;
  created_at: string;
}

export interface HealthLogItem {
  id: number;
  health_score: number;
  status: string;
  note?: string | null;
  created_at: string;
}

export interface WateringLogItem {
  id: number;
  plant_id: number;
  soil_moisture?: number | null;
  amount_ml?: number | null;
  note?: string | null;
  watered_at: string;
}

export const plantApi = {
  list: () => api.get<Plant[]>('/plants/').then((r) => r.data),
  get: (id: number) => api.get<Plant>(`/plants/${id}`).then((r) => r.data),
  create: (payload: PlantCreate) => api.post<Plant>('/plants/', payload).then((r) => r.data),
  update: (id: number, payload: Partial<PlantCreate> & { health_score?: number; status?: string }) =>
    api.put<Plant>(`/plants/${id}`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/plants/${id}`).then((r) => r.data),
  healthHistory: (id: number) => api.get<HealthLogItem[]>(`/plants/${id}/health-history`).then((r) => r.data),
};

export const scannerApi = {
  analyze: (formData: FormData) => api.post<ScanResult>('/scanner/analyze', formData).then((r) => r.data),
  validate: (formData: FormData) => api.post('/scanner/validate', formData).then((r) => r.data),
  history: (plantId?: number) =>
    api.get<ScanHistoryItem[]>('/scanner/history', { params: plantId ? { plant_id: plantId } : {} }).then((r) => r.data),
};

export const wateringApi = {
  recommendations: () => api.get<WateringRecommendation[]>('/watering/recommendations').then((r) => r.data),
  recommendation: (id: number) =>
    api.get<WateringRecommendation>(`/watering/recommendation/${id}`).then((r) => r.data),
  log: (payload: { plant_id: number; soil_moisture?: number; amount_ml?: number; note?: string }) =>
    api.post('/watering/log', payload).then((r) => r.data),
  logs: (plantId?: number) =>
    api.get<WateringLogItem[]>('/watering/logs', { params: plantId ? { plant_id: plantId } : {} }).then((r) => r.data),
};

export const statsApi = {
  dashboard: () => api.get<DashboardStats>('/stats/dashboard').then((r) => r.data),
  weather: () => api.get('/stats/weather').then((r) => r.data),
};

export const assistantApi = {
  chat: (text: string) =>
    api.post<{ text: string; is_valid_topic: boolean }>('/assistant/chat', { text, role: 'user' }).then((r) => r.data),
};
