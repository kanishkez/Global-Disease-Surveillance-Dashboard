'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, GlobalStats, MapDataPoint, Outbreak, SurveillanceEvent } from '@/lib/api';
import StatsCard from '@/components/StatsCard';
import AlertFeed from '@/components/AlertFeed';
import OutbreakMap from '@/components/OutbreakMap';
import TrendChart from '@/components/TrendChart';

export default function HomePage() {
  const router = useRouter();
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [mapData, setMapData] = useState<MapDataPoint[]>([]);
  const [outbreaks, setOutbreaks] = useState<Outbreak[]>([]);
  const [events, setEvents] = useState<SurveillanceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, mapPoints, outbreakData, eventData] = await Promise.allSettled([
          api.getStats(),
          api.getMapData(),
          api.getOutbreaks({ active_only: true }),
          api.getEvents(30),
        ]);

        if (statsData.status === 'fulfilled') setStats(statsData.value);
        if (mapPoints.status === 'fulfilled') setMapData(mapPoints.value);
        if (outbreakData.status === 'fulfilled') setOutbreaks(outbreakData.value);
        if (eventData.status === 'fulfilled') setEvents(eventData.value);
      } catch (err) {
        setError('Unable to connect to the surveillance API. Ensure the backend is running.');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Build chart data from outbreaks
  const sourceDistribution = outbreaks.reduce((acc, o) => {
    acc[o.source] = (acc[o.source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const severityDistribution = outbreaks.reduce((acc, o) => {
    const sev = o.severity || 'medium';
    acc[sev] = (acc[sev] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-3 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-white mb-1">Initializing Surveillance</h2>
          <p className="text-dark-400 text-sm">Connecting to global health data sources...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Global Surveillance Dashboard</h1>
          <p className="text-dark-400 text-sm mt-1">Real-time disease intelligence from {stats?.total_countries || 0} countries</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-dark-400">
          <div className="pulse-dot" />
          <span>Updated {stats?.last_updated ? new Date(stats.last_updated).toLocaleTimeString() : 'recently'}</span>
        </div>
      </div>

      {error && (
        <div className="glass-card p-4 danger-glow border-red-500/30">
          <p className="text-red-400 text-sm">⚠️ {error}</p>
          <p className="text-dark-400 text-xs mt-1">Run <code className="text-primary-400">docker compose up</code> to start all services.</p>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatsCard title="Diseases Tracked" value={stats?.total_diseases_tracked || 0} icon="🦠" variant="default" />
        <StatsCard title="Countries" value={stats?.total_countries || 0} icon="🌍" variant="default" />
        <StatsCard title="Active Outbreaks" value={stats?.active_outbreaks || 0} icon="🚨"
                   variant="danger" trend="up" trendValue="Active" />
        <StatsCard title="Total Cases" value={stats?.total_cases ? (stats.total_cases / 1e6).toFixed(1) + 'M' : '0'} icon="📊" variant="warning" />
        <StatsCard title="Total Deaths" value={stats?.total_deaths ? (stats.total_deaths / 1e6).toFixed(1) + 'M' : '0'} icon="💀" variant="danger" />
        <StatsCard title="Events" value={stats?.total_events || 0} icon="📡" variant="success" />
      </div>

      {/* Map + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-white">🗺️ Global Outbreak Map</h2>
            <div className="flex items-center gap-3 text-[10px]">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" /> Low</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" /> Medium</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500" /> High</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Critical</span>
            </div>
          </div>
          <OutbreakMap
            data={mapData}
            height="420px"
            onCountryClick={(name) => router.push(`/countries?name=${encodeURIComponent(name)}`)}
          />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">🚨 Live Alerts</h2>
          <div className="max-h-[420px] overflow-y-auto pr-1 space-y-2">
            <AlertFeed outbreaks={outbreaks} maxItems={15} />
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Outbreaks by Source</h3>
          <TrendChart
            labels={Object.keys(sourceDistribution)}
            datasets={[{ label: 'Reports', data: Object.values(sourceDistribution), fill: false }]}
            type="bar"
            height={250}
          />
        </div>
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Severity Distribution</h3>
          <TrendChart
            labels={Object.keys(severityDistribution).map(s => s.charAt(0).toUpperCase() + s.slice(1))}
            datasets={[{ label: 'Count', data: Object.values(severityDistribution) }]}
            type="doughnut"
            height={250}
          />
        </div>
      </div>

      {/* Recent Events Timeline */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-white mb-4">📡 Recent Surveillance Events</h3>
        {events.length > 0 ? (
          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
            {events.slice(0, 15).map((event, idx) => (
              <div key={event.id || idx} className="flex gap-3 pb-3 border-b border-white/5 last:border-0 animate-slide-up"
                   style={{ animationDelay: `${idx * 30}ms` }}>
                <div className="flex flex-col items-center">
                  <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5" />
                  {idx < events.length - 1 && <div className="w-px flex-1 bg-white/10 mt-1" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium line-clamp-1">{event.title}</p>
                  <p className="text-xs text-dark-400 line-clamp-1 mt-0.5">{event.description}</p>
                  <div className="flex items-center gap-3 mt-1 text-[11px] text-dark-500">
                    <span>{event.source}</span>
                    {event.country_name && <span>📍 {event.country_name}</span>}
                    <span>{new Date(event.event_date).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-dark-400 text-sm text-center py-8">No recent events</p>
        )}
      </div>
    </div>
  );
}
