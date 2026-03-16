'use client';

import { useState, useEffect } from 'react';
import { api, Disease, Prediction, CaseStat } from '@/lib/api';
import StatsCard from '@/components/StatsCard';
import TrendChart from '@/components/TrendChart';

export default function AnalyticsPage() {
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [selectedDisease, setSelectedDisease] = useState<string>('COVID-19');
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [caseStats, setCaseStats] = useState<CaseStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDiseases();
  }, []);

  useEffect(() => {
    if (selectedDisease) loadAnalytics(selectedDisease);
  }, [selectedDisease]);

  async function loadDiseases() {
    try {
      const data = await api.getDiseases();
      setDiseases(data);
      if (data.length > 0 && !data.find(d => d.name === selectedDisease)) {
        setSelectedDisease(data[0].name);
      }
    } catch (err) {
      console.error('Failed to load diseases:', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadAnalytics(disease: string) {
    try {
      const [predData, statsData] = await Promise.allSettled([
        api.getPredictions(disease),
        api.getCaseStats({ disease, days: 60 }),
      ]);
      if (predData.status === 'fulfilled') setPredictions(predData.value);
      if (statsData.status === 'fulfilled') setCaseStats(statsData.value);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    }
  }

  // Compute analytics
  const anomalies = predictions.filter(p => p.is_anomaly);
  const avgPredicted = predictions.length
    ? Math.round(predictions.reduce((s, p) => s + (p.predicted_cases || 0), 0) / predictions.length)
    : 0;
  const maxPredicted = predictions.length
    ? Math.max(...predictions.map(p => p.predicted_cases || 0))
    : 0;

  // Country-level comparison from case stats
  const countryStats = caseStats.reduce((acc, s) => {
    if (s.country_name && s.country_name !== 'Global') {
      if (!acc[s.country_name]) {
        acc[s.country_name] = { total: 0, deaths: 0, latest: 0 };
      }
      acc[s.country_name].total = Math.max(acc[s.country_name].total, s.total_cases);
      acc[s.country_name].deaths = Math.max(acc[s.country_name].deaths, s.total_deaths);
      acc[s.country_name].latest = Math.max(acc[s.country_name].latest, s.new_cases);
    }
    return acc;
  }, {} as Record<string, { total: number; deaths: number; latest: number }>);

  const topCountries = Object.entries(countryStats)
    .sort(([, a], [, b]) => b.total - a.total)
    .slice(0, 10);

  // Sorted stats for time-series
  const sortedStats = [...caseStats]
    .filter(s => s.country_name === 'Global' || !s.country_name)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">📊 ML Analytics</h1>
          <p className="text-dark-400 text-sm mt-1">AI-powered outbreak predictions and anomaly detection</p>
        </div>
        <select
          value={selectedDisease}
          onChange={(e) => setSelectedDisease(e.target.value)}
          className="px-4 py-2 rounded-lg text-sm bg-white/5 border border-white/10 text-white outline-none focus:border-primary-500/50 transition-all cursor-pointer"
        >
          {diseases.map(d => (
            <option key={d.id} value={d.name} className="bg-dark-900">{d.name}</option>
          ))}
        </select>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatsCard title="Avg Predicted" value={avgPredicted.toLocaleString()} subtitle="cases/day" icon="🔮" variant="default" />
        <StatsCard title="Peak Forecast" value={maxPredicted.toLocaleString()} subtitle="max daily cases" icon="📈" variant="warning" />
        <StatsCard title="Anomalies" value={anomalies.length} subtitle="detected spikes" icon="⚠️" variant="danger"
                   trend={anomalies.length > 0 ? 'up' : 'neutral'} trendValue={anomalies.length > 0 ? 'Alert' : 'Normal'} />
        <StatsCard title="Model" value={predictions[0]?.model_type?.toUpperCase() || 'LSTM'} subtitle="prediction engine" icon="🤖" variant="success" />
      </div>

      {/* Prediction Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">🔮 7-Day Forecast — {selectedDisease}</h3>
          {predictions.length > 0 ? (
            <TrendChart
              labels={predictions.map(p => new Date(p.prediction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))}
              datasets={[
                { label: 'Predicted', data: predictions.map(p => p.predicted_cases || 0), color: '#6366f1' },
                { label: 'Upper CI', data: predictions.map(p => p.confidence_upper || 0), color: '#ef4444', fill: false },
                { label: 'Lower CI', data: predictions.map(p => p.confidence_lower || 0), color: '#10b981', fill: false },
              ]}
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-dark-400 text-sm">
              No prediction data available
            </div>
          )}
        </div>

        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">📊 Anomaly Scores</h3>
          {predictions.length > 0 ? (
            <TrendChart
              labels={predictions.map(p => new Date(p.prediction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))}
              datasets={[{
                label: 'Anomaly Score',
                data: predictions.map(p => (p.anomaly_score || 0) * 100),
                color: '#f59e0b',
              }]}
              type="bar"
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-dark-400 text-sm">
              No anomaly data available
            </div>
          )}
        </div>
      </div>

      {/* Historical Trend */}
      {sortedStats.length > 1 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">📈 Historical Case Trend (Global)</h3>
          <TrendChart
            labels={sortedStats.map(s => new Date(s.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))}
            datasets={[
              { label: 'Total Cases', data: sortedStats.map(s => s.total_cases), color: '#6366f1' },
              { label: 'Deaths', data: sortedStats.map(s => s.total_deaths), color: '#ef4444' },
            ]}
            height={300}
          />
        </div>
      )}

      {/* Country Comparison */}
      {topCountries.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">🌍 Country Comparison — {selectedDisease}</h3>
          <TrendChart
            labels={topCountries.map(([name]) => name)}
            datasets={[
              { label: 'Total Cases', data: topCountries.map(([, s]) => s.total), color: '#6366f1', fill: false },
              { label: 'Deaths', data: topCountries.map(([, s]) => s.deaths), color: '#ef4444', fill: false },
            ]}
            type="bar"
            height={300}
          />
        </div>
      )}

      {/* Anomaly Alerts */}
      {anomalies.length > 0 && (
        <div className="glass-card p-5 danger-glow">
          <h3 className="text-sm font-semibold text-red-400 mb-3">⚠️ Anomaly Alerts</h3>
          <div className="space-y-2">
            {anomalies.map((a, idx) => (
              <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <div className="pulse-dot" />
                <div className="flex-1">
                  <p className="text-sm text-white font-medium">
                    Spike detected on {new Date(a.prediction_date).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-dark-400">
                    Predicted: {a.predicted_cases?.toLocaleString()} cases • Score: {((a.anomaly_score || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Model Info */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-white mb-3">🤖 Model Architecture</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-white/5 border border-white/5">
            <h4 className="text-xs font-bold text-primary-400 uppercase tracking-wider mb-2">Trend Prediction</h4>
            <p className="text-sm text-white font-medium">PyTorch LSTM</p>
            <p className="text-xs text-dark-400 mt-1">2-layer LSTM with dropout for 7-day case forecasting with confidence intervals</p>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-white/5">
            <h4 className="text-xs font-bold text-accent-400 uppercase tracking-wider mb-2">Report Classification</h4>
            <p className="text-sm text-white font-medium">BART Zero-Shot</p>
            <p className="text-xs text-dark-400 mt-1">Classifies reports as confirmed/suspected/news using NLI-based zero-shot</p>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-white/5">
            <h4 className="text-xs font-bold text-warning-400 uppercase tracking-wider mb-2">Anomaly Detection</h4>
            <p className="text-sm text-white font-medium">Isolation Forest</p>
            <p className="text-xs text-dark-400 mt-1">sklearn Isolation Forest with Z-score fallback for spike detection</p>
          </div>
        </div>
      </div>
    </div>
  );
}
