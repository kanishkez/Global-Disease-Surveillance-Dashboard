const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Disease {
  id: number;
  name: string;
  description?: string;
  category?: string;
  icd_code?: string;
  is_notifiable: boolean;
  created_at?: string;
  outbreak_count?: number;
  total_cases?: number;
}

export interface Country {
  id: number;
  name: string;
  iso_code?: string;
  iso2_code?: string;
  continent?: string;
  population?: number;
  latitude?: number;
  longitude?: number;
  total_cases?: number;
  total_deaths?: number;
  active_outbreaks?: number;
}

export interface Outbreak {
  id: number;
  disease_name: string;
  country_name?: string;
  region?: string;
  latitude?: number;
  longitude?: number;
  source: string;
  source_url?: string;
  report_date: string;
  description?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  classification?: string;
  cases_count?: number;
  deaths_count?: number;
  is_active: boolean;
  created_at?: string;
}

export interface CaseStat {
  id: number;
  disease_name: string;
  country_name?: string;
  date: string;
  total_cases: number;
  new_cases: number;
  total_deaths: number;
  new_deaths: number;
  total_recovered: number;
  active_cases: number;
  cases_per_million?: number;
  deaths_per_million?: number;
  source?: string;
}

export interface MapDataPoint {
  country_name: string;
  latitude: number;
  longitude: number;
  total_cases: number;
  total_deaths: number;
  active_outbreaks: number;
  severity?: string;
  diseases: string[];
}

export interface Prediction {
  disease_name: string;
  country_name?: string;
  prediction_date: string;
  predicted_cases?: number;
  confidence_lower?: number;
  confidence_upper?: number;
  model_type: string;
  is_anomaly: boolean;
  anomaly_score?: number;
}

export interface SurveillanceEvent {
  id: number;
  title: string;
  description?: string;
  source: string;
  source_url?: string;
  event_date: string;
  location?: string;
  country_name?: string;
  event_type?: string;
}

export interface SearchResult {
  diseases: Disease[];
  outbreaks: Outbreak[];
  countries: Country[];
  events: SurveillanceEvent[];
}

export interface GlobalStats {
  total_diseases_tracked: number;
  total_countries: number;
  active_outbreaks: number;
  total_cases: number;
  total_deaths: number;
  total_events: number;
  last_updated?: string;
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
    if (!res.ok) {
      console.error(`API error: ${res.status} for ${url}`);
      throw new Error(`API error: ${res.status}`);
    }
    return res.json();
  } catch (error) {
    console.error(`Failed to fetch ${url}:`, error);
    throw error;
  }
}

export const api = {
  getStats: () => fetchApi<GlobalStats>('/api/stats'),
  search: (params: { q?: string; disease?: string; country?: string; region?: string }) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return fetchApi<SearchResult>(`/api/search?${qs}`);
  },
  getDiseases: (skip = 0, limit = 50) =>
    fetchApi<Disease[]>(`/api/diseases?skip=${skip}&limit=${limit}`),
  getOutbreaks: (params?: { disease?: string; country?: string; active_only?: boolean }) => {
    const qs = new URLSearchParams(
      Object.entries(params || {}).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
    ).toString();
    return fetchApi<Outbreak[]>(`/api/outbreaks?${qs}`);
  },
  getCountries: (continent?: string) =>
    fetchApi<Country[]>(`/api/countries${continent ? `?continent=${continent}` : ''}`),
  getCountryDetails: (name: string) =>
    fetchApi<{ country: Country; outbreaks: Outbreak[]; case_statistics: CaseStat[] }>(`/api/country/${encodeURIComponent(name)}`),
  getCaseStats: (params?: { disease?: string; country?: string; days?: number }) => {
    const qs = new URLSearchParams(
      Object.entries(params || {}).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
    ).toString();
    return fetchApi<CaseStat[]>(`/api/case-stats?${qs}`);
  },
  getPredictions: (disease: string, country?: string) => {
    const qs = country ? `?country=${encodeURIComponent(country)}` : '';
    return fetchApi<Prediction[]>(`/api/predict/${encodeURIComponent(disease)}${qs}`);
  },
  getMapData: () => fetchApi<MapDataPoint[]>('/api/map-data'),
  getEvents: (days = 7) => fetchApi<SurveillanceEvent[]>(`/api/events?days=${days}`),
  getHealth: () => fetchApi<{ status: string; timestamp: string }>('/api/health'),
};
